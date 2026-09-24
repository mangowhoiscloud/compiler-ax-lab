# Additional working procedure

1. Before changing code, identify the observable output contract and one way a plausible implementation or test could violate it. Locate the relevant implementation and its existing test caller; write a brief working diagnosis, not an inventory of modules.
2. Separate the product's computation from the checker. State why the selected input exposes the failure and why its expected value is independent. If a value comparison can pass for the wrong reason, change the representation or input so that reason becomes observable.
3. Implement the smallest change within the allowed files. Preserve the public meaning and do not move the success threshold to fit an output. If the obstacle belongs to environment or product code outside scope, identify it rather than hiding it.
4. Use actual check results to choose the next action. Connect the source revision, command, selected test and observed result. A compile failure, zero tests or missing output is not evidence of numerical detection.
5. Before the final handoff, check whether the evidence answers the original diagnosis, identify unexecuted checks, and provide a reviewable patch plus its remaining decision. Do not turn a successful command into a claim of NPU performance or human approval.
