use furiosa_opt_examples::double_buffering::{Group, Out, Red, Tok, rolled, software_pipelined, unrolled};
use furiosa_opt_std::prelude::*;

#[path = "support/double_buffering_reference.rs"]
mod reference;

// The macro only binds each device entrypoint's concrete type. Fixtures and the oracle are shared.
macro_rules! check_variant {
    ($test:ident, $kernel:ident) => {
        #[tokio::test]
        async fn $test() {
            assert_eq!(
                (Tok::SIZE, Group::SIZE, Out::SIZE, Red::SIZE),
                (
                    reference::TOKENS,
                    reference::GROUPS,
                    reference::OUTPUTS,
                    reference::REDUCTION
                )
            );
            let mut device = Device::new($kernel.topology()).unwrap();
            for case in reference::CASES {
                let (activation, weight) = reference::inputs(case);
                let expected = reference::reference(&activation, &weight);
                let activation = HostTensor::<bf16, m![Tok, Red]>::from_vec(
                    activation.into_iter().map(|x| bf16::from_f32(x as f32)),
                );
                let weight = HostTensor::<bf16, m![Group, Out, Red]>::from_vec(
                    weight.into_iter().map(|x| bf16::from_f32(x as f32)),
                );
                let activation_hbm = activation.to_hbm(&mut device.pdma).await.unwrap();
                let weight_hbm = weight.to_hbm(&mut device.pdma).await.unwrap();
                let out = launch($kernel, (&mut device, &activation_hbm, &weight_hbm))
                    .await
                    .unwrap();
                let actual: Vec<f32> = out
                    .to_host::<m![Tok, Group, Out]>(&mut device.pdma)
                    .await
                    .unwrap()
                    .into_vec()
                    .into_iter()
                    .map(|x| x.to_f32())
                    .collect();
                // --nocapture preserves all observed values; fixture inputs are deterministic integer formulas.
                println!(
                    "CASE_RESULT variant={} case={case:?} expected={expected:?} actual={actual:?}",
                    stringify!($kernel)
                );
                reference::compare(stringify!($kernel), case, &expected, &actual).unwrap();
                println!(
                    "CASE_PASS variant={} case={case:?} compared={}",
                    stringify!($kernel),
                    actual.len()
                );
            }
        }
    };
}

check_variant!(test_double_buffering_rolled, rolled);
check_variant!(test_double_buffering_software_pipelined, software_pipelined);
check_variant!(test_double_buffering_unrolled, unrolled);
