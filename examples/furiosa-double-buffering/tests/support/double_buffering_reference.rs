//! Exact finite fixtures for the pinned 16 x 20 x 8 double-buffering example.
//! This module has no SDK dependency; rustc --test can check the same oracle used by the integration tests.

pub const TOKENS: usize = 16;
pub const GROUPS: usize = 20;
pub const OUTPUTS: usize = 8;
pub const REDUCTION: usize = 64;
pub const OUTPUT_LEN: usize = TOKENS * GROUPS * OUTPUTS;

#[derive(Clone, Copy, Debug)]
pub enum Case {
    Basis(usize),
    SignedDense,
    Zero,
}

// Zero follows nonzero work so repeated use of one Device also exercises state clearing.
pub const CASES: [Case; 6] = [
    Case::Basis(0),
    Case::Basis(1),
    Case::Basis(2),
    Case::Basis(3),
    Case::SignedDense,
    Case::Zero,
];

fn sign(k: usize, r: usize) -> i32 {
    if (k & r).count_ones().is_multiple_of(2) { 1 } else { -1 }
}

pub fn inputs(case: Case) -> (Vec<i32>, Vec<i32>) {
    if let Case::Basis(q) = case {
        assert!(q < 4, "basis block outside the pinned reduction axis");
    }
    let mut activation = vec![0; TOKENS * REDUCTION];
    let mut weight = vec![0; GROUPS * OUTPUTS * REDUCTION];
    for t in 0..TOKENS {
        for r in 0..REDUCTION {
            activation[t * REDUCTION + r] = match case {
                Case::Basis(q) => i32::from(r == TOKENS * q + t),
                Case::SignedDense => sign(t, r),
                Case::Zero => 0,
            };
        }
    }
    for g in 0..GROUPS {
        for o in 0..OUTPUTS {
            for r in 0..REDUCTION {
                weight[(g * OUTPUTS + o) * REDUCTION + r] = match case {
                    Case::SignedDense => {
                        let magnitude = (OUTPUTS * g + o + 1) as i32;
                        let polarity = if o % 2 == 0 { 1 } else { -1 };
                        polarity * magnitude * sign(2 * o + g % 2, r)
                    }
                    _ => (1 + (OUTPUTS * g + o + 17 * r) % 251) as i32,
                };
            }
        }
    }
    (activation, weight)
}

pub fn reference(activation: &[i32], weight: &[i32]) -> Vec<i32> {
    assert_eq!(activation.len(), TOKENS * REDUCTION);
    assert_eq!(weight.len(), GROUPS * OUTPUTS * REDUCTION);
    assert!(activation.iter().all(|&x| (-1..=1).contains(&x)));
    assert!(weight.iter().all(|&x| (-251..=251).contains(&x)));
    let mut expected = vec![0; OUTPUT_LEN];
    // Independent scalar definition; no SDK contraction, cast or kernel is used here.
    for t in 0..TOKENS {
        for g in 0..GROUPS {
            for o in 0..OUTPUTS {
                let mut sum = 0i32;
                for r in 0..REDUCTION {
                    sum += activation[t * REDUCTION + r] * weight[(g * OUTPUTS + o) * REDUCTION + r];
                }
                expected[(t * GROUPS + g) * OUTPUTS + o] = sum;
            }
        }
    }
    expected
}

pub fn compare(variant: &str, case: Case, expected: &[i32], actual: &[f32]) -> Result<(), String> {
    if expected.len() != OUTPUT_LEN || actual.len() != OUTPUT_LEN {
        return Err(format!(
            "variant={variant} case={case:?} length: expected={} actual={}",
            expected.len(),
            actual.len()
        ));
    }
    for (index, (&want, &got)) in expected.iter().zip(actual).enumerate() {
        // Numerical equality accepts signed zero and rejects NaN/Inf against finite expected values.
        if got != want as f32 {
            let t = index / (GROUPS * OUTPUTS);
            let g = index / OUTPUTS % GROUPS;
            let o = index % OUTPUTS;
            return Err(format!(
                "variant={variant} case={case:?} t={t} g={g} o={o} expected={want} actual={got}"
            ));
        }
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn fixtures_match_closed_forms_and_are_exact_bf16_values() {
        for case in CASES {
            let (activation, weight) = inputs(case);
            let expected = reference(&activation, &weight);
            for &value in activation.iter().chain(&weight).chain(&expected) {
                // bf16 retains the upper 16 bits of an exactly representable f32 value.
                assert_eq!((value as f32).to_bits() & 0xffff, 0, "case={case:?} value={value}");
            }
            for t in 0..TOKENS {
                for g in 0..GROUPS {
                    for o in 0..OUTPUTS {
                        let closed_form = match case {
                            Case::Zero => 0,
                            Case::Basis(q) => (1 + (8 * g + o + 17 * (16 * q + t)) % 251) as i32,
                            Case::SignedDense if t == 2 * o + g % 2 => {
                                (if o % 2 == 0 { 1 } else { -1 }) * 64 * (8 * g + o + 1) as i32
                            }
                            Case::SignedDense => 0,
                        };
                        assert_eq!(
                            expected[(t * GROUPS + g) * OUTPUTS + o],
                            closed_form,
                            "{case:?} t={t} g={g} o={o}"
                        );
                    }
                }
            }
            let actual: Vec<_> = expected.iter().map(|&x| x as f32).collect();
            compare("reference-only", case, &expected, &actual).unwrap();
        }
    }

    #[test]
    fn comparison_rejects_wrong_groups_missing_outputs_and_nonfinite_values() {
        let case = Case::Basis(0);
        let (activation, weight) = inputs(case);
        let expected = reference(&activation, &weight);
        let correct: Vec<_> = expected.iter().map(|&x| x as f32).collect();
        let mut rotated = correct.clone();
        let mut missing_second = correct.clone();
        let mut transposed = correct.clone();
        for t in 0..TOKENS {
            for g in 0..GROUPS {
                for o in 0..OUTPUTS {
                    let index = (t * GROUPS + g) * OUTPUTS + o;
                    rotated[index] = correct[(t * GROUPS + (g + 1) % GROUPS) * OUTPUTS + o];
                    if g % 2 == 1 {
                        missing_second[index] = 0.0;
                    }
                    transposed[(t * OUTPUTS + o) * GROUPS + g] = correct[index];
                }
            }
        }
        // These are output-level checker controls, not executions of faulty SDK kernels.
        for wrong in [&rotated, &missing_second, &transposed] {
            assert!(compare("output-control", case, &expected, wrong).is_err());
        }
        for value in [f32::NAN, f32::INFINITY, f32::NEG_INFINITY] {
            let mut wrong = correct.clone();
            wrong[OUTPUT_LEN - 1] = value;
            let error = compare("output-control", case, &expected, &wrong).unwrap_err();
            assert!(error.contains("t=15 g=19 o=7"));
        }
        assert!(compare("output-control", case, &expected, &correct[..OUTPUT_LEN - 1]).is_err());
        let zero = vec![0; OUTPUT_LEN];
        compare("signed-zero", Case::Zero, &zero, &vec![-0.0; OUTPUT_LEN]).unwrap();
    }
}
