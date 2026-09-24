//! Integer fixtures and a scalar oracle, independent of SDK tensor operations.

pub const TOK: usize = 16;
pub const RED: usize = 64;
pub const GROUP: usize = 20;
pub const OUT: usize = 8;
pub const RESULT_LEN: usize = TOK * GROUP * OUT;

pub struct Case {
    pub name: &'static str,
    pub activation: Vec<i32>,
    pub weight: Vec<i32>,
}

// Two base-251 digits identify all 2560 coordinates without bf16 rounding.
// The low digit alone repeats; checking both prevents a matching digit from
// concealing a permutation. Distinct reduction bands also exercise both ends.
fn identity_case(high: bool) -> Case {
    let mut activation = vec![0; TOK * RED];
    let mut weight = vec![0; GROUP * OUT * RED];
    let band = if high { 48 } else { 0 };
    for t in 0..TOK {
        activation[t * RED + band + t] = 1;
        for g in 0..GROUP {
            for o in 0..OUT {
                let coordinate = (t * GROUP + g) * OUT + o;
                let digit = if high { coordinate / 251 } else { coordinate % 251 };
                weight[(g * OUT + o) * RED + band + t] = (digit + 1) as i32;
            }
        }
    }
    Case {
        name: if high { "identity_high_v1" } else { "identity_low_v1" },
        activation,
        weight,
    }
}

pub fn cases() -> Vec<Case> {
    let low = identity_case(false);
    // Keep nonzero weights and reuse the Device immediately after `low`.
    let zero = Case {
        name: "zero_activation_after_identity_low_v1",
        activation: vec![0; TOK * RED],
        weight: low.weight.clone(),
    };
    // Every reduction position contributes a signed integer product. Activation
    // is +/-1 and weight is in {-2, -1, 1, 2}, so even the sum of absolute
    // products is <=128. All partial sums and results are exactly representable.
    let dense = Case {
        name: "signed_dense_v1",
        activation: (0..TOK * RED)
            .map(|i| {
                let (t, r) = (i / RED, i % RED);
                if (t * 11 + r * 7 + r / 3 + t * r) % 17 < 8 {
                    -1
                } else {
                    1
                }
            })
            .collect(),
        weight: (0..GROUP * OUT * RED)
            .map(|i| {
                let (g, o, r) = (i / (OUT * RED), i / RED % OUT, i % RED);
                [-2, -1, 1, 2][(g * 13 + o * 7 + r * 3 + r / 5 + g * r + o * r) % 11 % 4]
            })
            .collect(),
    };
    vec![low, zero, identity_case(true), dense]
}

/// Row-major output[t,g,o] = sum_r activation[t,r] * weight[g,o,r].
/// Use i32 arithmetic on the original integers, without an SDK contraction or
/// floating-point rounding. The caller uploads these same integers as bf16.
pub fn reference(case: &Case) -> Vec<i32> {
    assert_eq!(case.activation.len(), TOK * RED, "{} activation length", case.name);
    assert_eq!(case.weight.len(), GROUP * OUT * RED, "{} weight length", case.name);
    let mut expected = Vec::with_capacity(RESULT_LEN);
    for activation_row in case.activation.chunks_exact(RED) {
        for weight_row in case.weight.chunks_exact(RED) {
            let mut sum = 0;
            for (&activation, &weight) in activation_row.iter().zip(weight_row) {
                sum += activation * weight;
            }
            expected.push(sum);
        }
    }
    expected
}

#[test]
fn reference_checks_strides_and_identity_digits() {
    // Literal flat offsets independently pin token/group/channel/reduction
    // strides, including the last coordinate. Two terms check the reduction.
    let mut case = Case {
        name: "hand_computed_strides",
        activation: vec![0; TOK * RED],
        weight: vec![0; GROUP * OUT * RED],
    };
    case.activation[0] = 2;
    case.activation[1022] = -3;
    case.activation[1023] = 2;
    case.weight[0] = 5;
    case.weight[64] = -2;
    case.weight[512] = 3;
    case.weight[10238] = 4;
    case.weight[10239] = 7;
    let mut expected = vec![0; RESULT_LEN];
    expected[0] = 10;
    expected[1] = -4;
    expected[8] = 6;
    expected[2559] = 2;
    assert_eq!(reference(&case), expected);

    let low = reference(&identity_case(false));
    let high = reference(&identity_case(true));
    assert_eq!(low.len(), RESULT_LEN);
    assert_eq!(high.len(), RESULT_LEN);
    for (coordinate, (&low, &high)) in low.iter().zip(&high).enumerate() {
        assert_eq!((high - 1) * 251 + low - 1, coordinate as i32);
    }
}
