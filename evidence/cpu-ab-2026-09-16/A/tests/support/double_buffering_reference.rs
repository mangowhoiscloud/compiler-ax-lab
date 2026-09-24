//! Deterministic row-major inputs and an integer scalar oracle, independent of SDK contraction.

pub const TOKENS: usize = 16;
pub const REDUCTION: usize = 64;
pub const GROUPS: usize = 20;
pub const OUTPUTS: usize = 8;

pub struct InputCase {
    pub name: String,
    pub activation: Vec<i32>,
    pub weight: Vec<i32>,
}

pub fn cases() -> Vec<InputCase> {
    let mut cases = Vec::new();

    // Probe r = 4*t + offset. Together the four cases select every reduction coordinate.
    // W[g,o,r] = 1 + (17*r + 8*g + o) % 251 gives distinct values for every (g,o)
    // at a fixed token, and distinct values for every token at a fixed (g,o).
    // This includes groups 0/19, every within-pair boundary, and every between-pair boundary.
    for offset in 0..4 {
        let mut activation = vec![0; TOKENS * REDUCTION];
        for t in 0..TOKENS {
            activation[t * REDUCTION + 4 * t + offset] = 1;
        }
        let mut weight = Vec::with_capacity(GROUPS * OUTPUTS * REDUCTION);
        for g in 0..GROUPS {
            for o in 0..OUTPUTS {
                for r in 0..REDUCTION {
                    weight.push(1 + ((17 * r + 8 * g + o) % 251) as i32);
                }
            }
        }
        cases.push(InputCase {
            name: format!("basis_offset_{offset}"),
            activation,
            weight,
        });
    }

    // Immediately follow the final, entirely nonzero output with zero weights and the same
    // nonzero activation. The SDK tests keep one Device alive across this transition.
    cases.push(InputCase {
        name: "zero_weights_after_basis_offset_3".into(),
        activation: cases.last().unwrap().activation.clone(),
        weight: vec![0; GROUPS * OUTPUTS * REDUCTION],
    });

    // All 64 terms participate, with mixed signs and magnitudes in both operands.
    let signed = [-2, -1, 1, 2];
    let mut activation = Vec::with_capacity(TOKENS * REDUCTION);
    for t in 0..TOKENS {
        for r in 0..REDUCTION {
            activation.push(signed[(17 * t + 7 * r + 3 * t * r) % 31 % 4]);
        }
    }
    let mut weight = Vec::with_capacity(GROUPS * OUTPUTS * REDUCTION);
    for g in 0..GROUPS {
        for o in 0..OUTPUTS {
            for r in 0..REDUCTION {
                weight.push(signed[(13 * g + 5 * o + 11 * r + g * r + 3 * o * r) % 29 % 4]);
            }
        }
    }
    cases.push(InputCase {
        name: "signed_dense".into(),
        activation,
        weight,
    });
    cases
}

pub fn expected(activation: &[i32], weight: &[i32]) -> Vec<i32> {
    assert_eq!(activation.len(), TOKENS * REDUCTION);
    assert_eq!(weight.len(), GROUPS * OUTPUTS * REDUCTION);
    let mut result = Vec::with_capacity(TOKENS * GROUPS * OUTPUTS);
    for token in activation.chunks_exact(REDUCTION) {
        for channel in weight.chunks_exact(REDUCTION) {
            let mut sum = 0;
            for (&activation, &weight) in token.iter().zip(channel) {
                sum += activation * weight;
            }
            result.push(sum);
        }
    }
    result
}

#[test]
fn scalar_reference_preserves_axes_and_reduction_endpoints() {
    let mut activation = vec![0; TOKENS * REDUCTION];
    activation[64] = 2; // [t=1, r=0]
    activation[127] = -1; // [t=1, r=63]
    activation[1023] = 3; // [t=15, r=63]
    let mut weight = vec![0; GROUPS * OUTPUTS * REDUCTION];
    weight[448] = 3; // [g=0, o=7, r=0]
    weight[511] = 4; // [g=0, o=7, r=63]
    weight[9791] = -2; // [g=19, o=0, r=63]

    // Hand-computed positions and values deliberately avoid the oracle's indexing logic.
    let mut want = vec![0; 2560];
    want[167] = 2; // [1,0,7]: 2*3 - 1*4
    want[312] = 2; // [1,19,0]: -1*(-2)
    want[2407] = 12; // [15,0,7]: 3*4
    want[2552] = -6; // [15,19,0]: 3*(-2)
    assert_eq!(expected(&activation, &weight), want);
}
