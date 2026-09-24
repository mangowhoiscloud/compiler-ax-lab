//! CPU value checks; these do not establish NPU correctness, timing, or overlap.

#[path = "support/double_buffering_reference.rs"]
mod reference;

use furiosa_opt_examples::double_buffering::{Group, Out, Pairs, Red, Tok, rolled, software_pipelined, unrolled};
use furiosa_opt_std::prelude::*;
use reference::{GROUPS, InputCase, OUTPUTS, REDUCTION, TOKENS};

type Activation = HbmTensor<bf16, m![1], m![Tok, Red]>;
type Weight = HbmTensor<bf16, m![1], m![Group, Out, Red]>;
type Output = HbmTensor<bf16, m![1], m![Tok, Group, Out]>;

fn to_bf16(values: &[i32]) -> Vec<bf16> {
    values.iter().map(|&value| bf16::from_f32(value as f32)).collect()
}

async fn inputs(device: &mut Device, variant: &str, case: &InputCase) -> (Activation, Weight) {
    println!(
        "variant={variant} case={} generator=double_buffering_reference_v1 \
         activation=[16,64] weight=[20,8,64] output=[16,20,8] row-major",
        case.name
    );
    assert_eq!(
        (Tok::SIZE, Red::SIZE, Group::SIZE, Out::SIZE),
        (TOKENS, REDUCTION, GROUPS, OUTPUTS)
    );
    assert_eq!(Pairs::SIZE * 2, GROUPS);
    let activation = HostTensor::<bf16, m![Tok, Red]>::from_vec(to_bf16(&case.activation))
        .to_hbm(&mut device.pdma)
        .await
        .unwrap_or_else(|error| panic!("{variant} case={}: activation copy: {error:?}", case.name));
    let weight = HostTensor::<bf16, m![Group, Out, Red]>::from_vec(to_bf16(&case.weight))
        .to_hbm(&mut device.pdma)
        .await
        .unwrap_or_else(|error| panic!("{variant} case={}: weight copy: {error:?}", case.name));
    (activation, weight)
}

async fn check_output(device: &mut Device, variant: &str, case: &InputCase, output: Output) {
    let expected = reference::expected(&case.activation, &case.weight);
    let actual = output
        .to_host::<m![Tok, Group, Out]>(&mut device.pdma)
        .await
        .unwrap_or_else(|error| panic!("{variant} case={}: output copy: {error:?}", case.name))
        .into_vec();
    println!("variant={variant} case={} expected={expected:?}", case.name);
    println!("variant={variant} case={} actual={actual:?}", case.name);
    assert_eq!(expected.len(), TOKENS * GROUPS * OUTPUTS);
    assert_eq!(
        actual.len(),
        expected.len(),
        "{variant} case={}: result length",
        case.name
    );

    // Exact bf16 equality is justified here: basis inputs/results are integers in [0,251].
    // Dense operands are +/-1 or +/-2, so the sum of absolute products is at most 64*4=256.
    // Every product and any partial sum is therefore an exactly representable bf16 integer.
    // This argument does not apply to arbitrary floating-point reductions. +/-0 compare equal.
    for t in 0..TOKENS {
        for g in 0..GROUPS {
            for o in 0..OUTPUTS {
                let index = (t * GROUPS + g) * OUTPUTS + o;
                let want = expected[index];
                let got = actual[index];
                assert!(
                    got.to_f32().is_finite() && got == bf16::from_f32(want as f32),
                    "{variant} case={} coordinate=({t},{g},{o}) expected={want} actual={got:?}",
                    case.name
                );
            }
        }
    }
    println!("SUCCESS variant={variant} case={}", case.name);
}

#[tokio::test]
async fn test_double_buffering_rolled() {
    let mut device = Device::new(rolled.topology()).unwrap();
    for case in reference::cases() {
        let (activation, weight) = inputs(&mut device, "rolled", &case).await;
        let output = launch(rolled, (&mut device, &activation, &weight))
            .await
            .unwrap_or_else(|error| panic!("rolled case={}: launch: {error:?}", case.name));
        check_output(&mut device, "rolled", &case, output).await;
    }
}

#[tokio::test]
async fn test_double_buffering_software_pipelined() {
    let mut device = Device::new(software_pipelined.topology()).unwrap();
    for case in reference::cases() {
        let (activation, weight) = inputs(&mut device, "software_pipelined", &case).await;
        let output = launch(software_pipelined, (&mut device, &activation, &weight))
            .await
            .unwrap_or_else(|error| panic!("software_pipelined case={}: launch: {error:?}", case.name));
        check_output(&mut device, "software_pipelined", &case, output).await;
    }
}

#[tokio::test]
async fn test_double_buffering_unrolled() {
    let mut device = Device::new(unrolled.topology()).unwrap();
    for case in reference::cases() {
        let (activation, weight) = inputs(&mut device, "unrolled", &case).await;
        let output = launch(unrolled, (&mut device, &activation, &weight))
            .await
            .unwrap_or_else(|error| panic!("unrolled case={}: launch: {error:?}", case.name));
        check_output(&mut device, "unrolled", &case, output).await;
    }
}
