//! CPU output checks for the public double-buffering examples.
//! These establish value agreement only, not NPU correctness, timing or overlap.

#[path = "support/double_buffering_reference.rs"]
mod double_buffering_reference;

use double_buffering_reference::{GROUP, OUT, RED, RESULT_LEN, TOK, cases, reference};
use furiosa_opt_examples::double_buffering::{Group, Out, Red, Tok, rolled, software_pipelined, unrolled};
use furiosa_opt_std::prelude::*;

fn as_bf16(values: &[i32]) -> Vec<bf16> {
    values
        .iter()
        .map(|&value| {
            assert!((-256..=256).contains(&value), "fixture integer must be exact in bf16");
            bf16::from_f32(value as f32)
        })
        .collect()
}

fn compare(variant: &str, case: &str, expected: &[i32], actual: &[bf16]) {
    // Print complete vectors before any comparison can fail. Values follow
    // [Tok, Group, Out] order; case names identify the deterministic v1 formulas.
    println!("variant={variant} case={case} expected={expected:?}");
    println!("variant={variant} case={case} actual={actual:?}");
    assert_eq!(
        expected.len(),
        RESULT_LEN,
        "variant={variant} case={case} oracle length"
    );
    assert_eq!(actual.len(), RESULT_LEN, "variant={variant} case={case} result length");
    for (index, (&expected, &actual)) in expected.iter().zip(actual).enumerate() {
        let (t, g, o) = (index / (GROUP * OUT), index / OUT % GROUP, index % OUT);
        // Integers in [-256,256] are exact in bf16. Identity results are 1..251;
        // dense products have total absolute sum <=128. Exact comparison is
        // justified for these fixtures, not for arbitrary floating reductions.
        assert!((-256..=256).contains(&expected), "oracle must remain exact in bf16");
        assert!(
            actual.to_f32().is_finite() && actual.to_f32() == expected as f32,
            "variant={variant} case={case} coordinate=({t},{g},{o}) expected={expected} actual={actual:?}"
        );
    }
    println!("PASS variant={variant} case={case}");
}

// Match the existing integration-test SDK upload/launch/copy pattern without
// coupling the scalar oracle to the kernel implementation or tensor operations.
macro_rules! double_buffering_test {
    ($name:ident, $kernel:ident) => {
        #[tokio::test]
        async fn $name() {
            let variant = stringify!($kernel);
            assert_eq!(
                (Tok::SIZE, Red::SIZE, Group::SIZE, Out::SIZE),
                (TOK, RED, GROUP, OUT)
            );
            let mut device = Device::new($kernel.topology()).unwrap();
            for case in cases() {
                println!(
                    "INPUT variant={variant} case={} activation=[16,64] weight=[20,8,64] result=[16,20,8]",
                    case.name
                );
                let expected = reference(&case);
                let activation = HostTensor::<bf16, m![Tok, Red]>::from_vec(as_bf16(&case.activation))
                    .to_hbm::<m![1], m![Tok, Red]>(&mut device.pdma)
                    .await
                    .unwrap();
                let weight = HostTensor::<bf16, m![Group, Out, Red]>::from_vec(as_bf16(&case.weight))
                    .to_hbm::<m![1], m![Group, Out, Red]>(&mut device.pdma)
                    .await
                    .unwrap();
                let output = launch($kernel, (&mut device, &activation, &weight))
                    .await
                    .unwrap();
                let actual = output
                    .to_host::<m![Tok, Group, Out]>(&mut device.pdma)
                    .await
                    .unwrap()
                    .into_vec();
                compare(variant, case.name, &expected, &actual);
            }
            println!("PASS variant={variant} all cases");
        }
    };
}

double_buffering_test!(test_double_buffering_rolled, rolled);
double_buffering_test!(test_double_buffering_software_pipelined, software_pipelined);
double_buffering_test!(test_double_buffering_unrolled, unrolled);
