# 2026 프론티어 개발 사례와 Compiler AX의 선택

확인일: **2026-09-14**. 기업·저자의 원문, 공개 코드, 평가 항목을 AI 도구와 병렬 조사로 대조한 설계 참고 자료입니다. 공개 사례의 재현 결과가 아니며, 아래 적용 판단은 이 lab의 선택입니다. 검색은 2026년 발표와 현재 원문을 우선한 사례 조사이지 전수조사가 아닙니다.

## 1. 최신성보다 먼저 맞출 것은 작업과 판정 단위다

2023–2025년 모델의 수정 성공률을 현재 Codex의 예상 성능으로 사용하지 않습니다. 발표일, 실제 실험·배포 시점, 모델·하네스, 수정 대상, 평가 집단을 함께 기록합니다. 2026년에 발표됐어도 실험이 2025년에 수행됐다면 그렇게 표시합니다. 반대로 의미 보존·ABI·독립 오라클 같은 원칙은 오래됐다는 이유로 약화하지 않습니다.

2026년 자료도 현재 사용하는 모델과 같다고 가정하지 않습니다. 원문에 모델명이 없으면 미공개로 남기고, 이 lab의 효과는 고정한 모델·하네스·환경에서 별도로 비교합니다.

| 우선순위 | 사례·원문 날짜 | 실제로 확인한 범위 | 이 lab에서 답할 질문 |
|---|---|---|---|
| 주 근거: 컴파일러 탐색 | [Magellan, 2026-01-28](https://arxiv.org/abs/2601.21096) | C++ 최적화 정책 생성·평가 연구. 내부 LLVM은 2025년 여름 수준 | 수정할 결정 로직과 수치 파라미터를 어떻게 나눌까? |
| 주 근거: 제품 통합 판정 | [JetBrains, 2026-05-29](https://blog.jetbrains.com/ai/2026/05/how-we-use-alphaevolve-to-make-complex-ide-algorithms-faster/) | B-tree 후보를 합성 벤치와 수정한 IDE nightly에서 비교 | 작은 벤치의 개선 중 무엇이 실제 작업에 남는가? |
| 주 근거: Rust 작업 규약 | [NVIDIA TileGym, 2026-07 공개·08 평가](https://github.com/NVIDIA/TileGym/tree/9ba5d94d59a87480483573dfe5e880b0d266d547/skills/tilegym-converting-cutile-triton-to-cutile-rs) | MD 절차·검사 스크립트·예제 공개. 평가 점수는 스킬 선택에 한정 | 역할별 산출물과 검사, 실패 시 중단을 어떻게 연결할까? |
| 주 근거: 대규모 Rust 생성 | [Anthropic, 2026-02-05](https://www.anthropic.com/engineering/building-c-compiler) | 병렬 에이전트가 Rust로 C compiler를 만든 연구 프로토타입 | 생성량이 늘 때 오라클과 회귀 검사가 어디서 필요해지는가? |
| 주 근거: 저장소 운영 | [OpenAI, 2026-02-11](https://openai.com/index/harness-engineering/) | 2025년 시작한 개발의 2026년 내부 beta 운영 보고 | 짧은 진입점·상세 문서·기계 검사를 어떻게 연결할까? |
| 주 근거: 스킬 효과 검증 | [NVIDIA ACES, 2026-08-20](https://arxiv.org/abs/2608.20614) | 스킬 유무를 비교한 paired 평가 연구 | MD를 추가한 것이 같은 모델의 실제 결과를 개선하는가? |
| 보조: 탐색 구조의 원전 | [AlphaEvolve, 2025-06-16](https://arxiv.org/html/2506.13131v1) | 프로그램 생성·평가·다양성 유지 구조. 2026 문서·적용 사례로 보완 | 다음 후보를 만들 때 어떤 실행 근거를 제공할까? |
| 보조: 표현·평가 단계 | [AlphaChip, 2020 원전·2024 공개 설명](https://deepmind.google/blog/how-alphachip-transformed-computer-chip-design/) | netlist macro placement의 RL. 새로운 2026 LLM 사례는 아님 | 허용 후보와 빠른 proxy, 실제 품질 평가를 어떻게 구분할까? |

비중은 근거의 용도로 정하며 임의의 신뢰 확률을 붙이지 않습니다. 오래된 RustAssistant·CodePlan·TestGen·자동 수정 사례는 실패 유형과 운영 원칙의 이력으로 둡니다. 현재 모델의 역량, 병렬 agent 수, 성공률을 결정하는 주 근거로 쓰지 않습니다. Dioxus의 현행 코드·검사는 Rust 유지보수에 직접 대응하므로 계속 사용합니다.

## 2. AlphaEvolve: 프로그램을 바꾸는 주체와 채택하는 주체가 다르다

### 2.1 무엇을 바꾸고, 다음 후보는 어떻게 생기는가

1. 사람이 동작하는 초기 프로그램, 수정 영역, 문제 조건, evaluator를 제공합니다. 수정 대상은 답 자체뿐 아니라 답을 만드는 알고리즘이나 탐색 절차일 수도 있습니다.
2. 샘플러는 이전 프로그램과 실행 결과·점수, 관련 설명을 골라 프롬프트를 구성합니다. 원논문의 모델 조합은 Gemini 2.0 Flash·Pro이며 현재 모든 구성의 모델이라고 일반화하지 않습니다.
3. LLM은 코드 변경을 제안합니다. 평가 cluster가 저렴한 검사부터 더 비싼 검사를 수행하고 결과를 프로그램 기록에 연결합니다.
4. 프로그램 저장소는 최고 점수 하나만 남기지 않고 품질과 다양성을 고려합니다. 원논문은 MAP-Elites와 island population에서 영향을 받은 선택을 설명하지만 비공개 구현 전체를 공개하지는 않습니다.

이 과정은 실행 시점의 프로그램 탐색입니다. 모델 weight를 학습했다거나 프로그램이 자신의 release 권한까지 개선했다는 설명은 맞지 않습니다. [원논문 §2·§6](https://arxiv.org/html/2506.13131v1)

### 2.2 공개 client와 2026 서비스 문서가 보여주는 책임

현재 확인한 공개 client revision은 `b51ab7a6446d0168bf6db52c6dccbec414a21b3f`입니다. `controller.py`는 후보 수신·평가 worker를 연결하고, `workers.py`는 후보 식별과 lock token에 평가 결과를 결속합니다. 고객 evaluator가 반환하는 `scores`와 설명용 `insights`는 역할이 다릅니다. 클라우드가 생성·샘플링을 맡고 고객이 평가기를 제공하므로, 이 client를 전체 탐색 엔진의 공개 구현이라고 부르지 않습니다. [공개 구현](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/tree/b51ab7a6446d0168bf6db52c6dccbec414a21b3f/src/alpha_evolve), [구조 문서, 2026-09-03 갱신](https://docs.cloud.google.com/gemini/enterprise/docs/alphaevolve/developer-guide/architecture-and-workflows)

2026-07-09 Google Cloud의 정식 제공 발표는 실제 2026년 제품 사건입니다. 다만 제품 출시와 각 고객 사례의 배포 완료는 별개입니다. 같은 글의 ORNL 사례는 Frontier AMD GPU에서 혼합 정밀도 후보를 컴파일·실행·수치 검증하는 탐색을 설명하며, 정량 speedup을 제시하지 않습니다. [공식 발표](https://cloud.google.com/blog/products/ai-machine-learning/alphaevolve-is-available-for-everyone)

실제 내부 활용의 후속 근거도 있습니다. DeepMind는 2026-05-07에 Spanner compaction의 write amplification 20% 감소와 차세대 TPU 설계에서의 정규 활용을 보고했습니다. 전자는 쓰기 증폭 지표이지 database throughput 20% 개선이 아닙니다. 기업의 내부 활용 보고이며 독립 재현과 구분합니다. [2026 impact report](https://deepmind.google/blog/alphaevolve-impact/)

### 2.3 탐색 점수는 합격 판정으로 복사하지 않는다

현재 공식 문서는 실행 안전·정책, 기능·제약, 성능의 세 평가 층을 제시합니다. 동시에 탐색에는 일부 테스트 통과율이나 soft penalty를 권합니다. 불완전한 후보도 다음 수정의 재료가 될 수 있다는 뜻이지, 오류를 포함한 컴파일러 변경을 병합해도 된다는 뜻은 아닙니다. [Evaluator patterns, 2026-09-03](https://docs.cloud.google.com/gemini/enterprise/docs/alphaevolve/developer-guide/evaluator-implementation-patterns)

다른 공식 지침은 가중 점수의 한 항목 독점, 느슨한 제약 벌점, 수치 edge case, 평가 데이터 노출을 경고합니다. 후보가 수정할 수 없는 검사 영역과 탐색 후 held-out 검증을 권합니다. [Reward-hacking prevention](https://docs.cloud.google.com/gemini/enterprise/docs/alphaevolve/developer-guide/reward-hacking-prevention)

**채택할 규칙:** 공개 검사에서 얻은 실패 위치와 부분 성과만 허용된 수정 시도에 설명합니다. 보호 입력·정답·개별 로그는 후보의 repair에 반환하지 않으며, 보호 검사 실패 뒤 수정은 새 실험입니다. 필수 정확성 실패·검사 미실행·누락 증거를 좋은 성능 점수로 상쇄하지 않습니다. MD의 수정 금지는 접근 제어가 아니므로 검사기 보호와 최종 재실행은 별도 구현·확인이 필요합니다. [기존 최종 검사 규약](../docs/quality.md#품질-검사-순서와-실패-뒤-행동)

## 3. AlphaEvolve의 2026 적용: 컴파일러 정책과 제품 성능을 나눠 읽는다

### 3.1 Magellan — 정책 구조와 숫자 탐색을 분리한다

**문제:** LLVM 휴리스틱의 구조와 상수를 함께 바꾸면 무효 후보와 compiler rebuild 비용이 늘어납니다.

**대응:** LLM은 C++ 결정 로직의 template을 만들고 상수는 flag로 노출합니다. template을 고정한 동안 선택적으로 Vizier가 값을 탐색합니다. 같은 구조를 매번 재생성·재빌드하지 않고 macro-benchmark 점수, tuning log, profile을 다음 정책 제안에 사용합니다.

기존 `MLInlineAdvisor`가 inlining의 legality를 먼저 검사하고 후보는 실행 여부의 선택 정책을 맡습니다. 허용되는 변환 안에서의 탐색이며, 임의의 Rust 수정까지 의미 보존을 보장하는 구조는 아닙니다.

**관측:** 해당 autotuning 비교에서 invalid 비율은 65% 초과에서 13%로 줄었습니다. 10개가 넘는 production binary 평가의 평균 크기 감소는 8.79%였고 비교 neural policy는 8.52%였습니다. 크기 감소를 실행 속도나 유지보수성 개선으로 바꾸어 읽지 않습니다.

**조건:** 기본 모델은 Gemini 2.5 Pro, 기본 설정은 autotuning 없음입니다. 논문은 2026-01-28 제출됐지만 toolchain은 2025년 여름 내부 LLVM 수준입니다. 공개 upstream 병합·전체 서비스 배포의 증거와는 구분합니다. [원논문 §2·§3.1](https://arxiv.org/html/2601.21096v1)

**적용 판단:** 지금의 테스트 보강 과제를 휴리스틱 최적화로 바꾸지 않습니다. 후속 최적화 과제가 승인되면, 먼저 변경할 정책의 입출력과 수치 파라미터를 구분할 수 있는지 확인합니다. 반복 rebuild가 실제 병목일 때만 별도 수치 탐색을 추가합니다.

### 3.2 JetBrains — 합성 벤치에서 이긴 후보도 실제 IDE에서는 탈락한다

**문제와 선택:** 이미 최적화된 IDE indexing의 B-tree를 대상으로, 빠른 합성 read/write benchmark와 unit test를 제공했습니다. score는 중간 규모 benchmark들의 median을 합한 값입니다. 50회 넘게 탐색한 다수 세션에서 보고한 15–20% 개선은 이 합성 score입니다.

**통합 확인:** 수정한 IntelliJ IDEA 2026.2 nightly의 Kotlin Spring Petclinic indexing은 baseline **17.4±0.5초**, 최선 후보 **16.6±0.2초**였습니다. 시간 감소는 약 **4.6%**입니다. 5개 후보 중 유의한 통합 개선은 2개였고, 다른 합성 벤치 우승 후보는 **17.5±0.4초**로 사실상 baseline 수준이었습니다.

**남은 판단:** 더 넓은 제품 지표인 megaAPDEX 검증은 후속 계획입니다. 이를 전체 IDE가 15–20% 빨라진 배포 성과라고 쓰지 않습니다. [JetBrains 원문: Result snapshot·What changed·What we measure next](https://blog.jetbrains.com/ai/2026/05/how-we-use-alphaevolve-to-make-complex-ide-algorithms-faster/)

**적용 판단:** 같은 후보에 `탐색 지표 → 통합 작업 결과 → 사람의 채택`을 따로 남깁니다. 작은 테스트가 탐색 비용을 줄여도, 최종 용도를 대표하지 못하면 채택 이유가 될 수 없습니다.

## 4. AlphaChip: LLM 코딩이 아니라 제약된 macro 배치의 RL이다

### 4.1 상태·행동·보상이 설명하는 탐색 범위

고정 netlist와 chip canvas가 주어지고 정책은 현재 macro를 놓을 grid cell을 선택합니다. 부분 배치, 연결 그래프, macro 크기·종류, routing 정보와 가능한 위치 mask가 상태를 구성합니다. 그래프 표현은 회로 비용이 연결 관계에 의존하기 때문에 사용합니다. 임의의 개발 과제에도 GNN을 붙이라는 근거가 아닙니다.

중간 보상은 없고 배치 완료 시 비용의 음수를 사용하며 PPO로 policy/value를 학습합니다. 2020 원전의 wirelength·congestion 목적과 density 제약, 현재 공개 구현의 wirelength·density·congestion 가중 비용은 구분합니다. 이는 프롬프트나 skill을 갱신하는 작업과 다른 실제 weight training입니다. [원 preprint §3](https://arxiv.org/html/2004.10746), [고정 환경 코드](https://github.com/google-research/circuit_training/blob/c417a3a13f40867b649c719c03daaf1b39a909bc/circuit_training/environment/environment.py)

### 4.2 세 단계는 서로 다른 질문에 답한다

| 단계 | 답하는 질문 | 이 단계만으로 결정할 수 없는 것 |
|---|---|---|
| 위치 mask·환경 제약 | 이번 행동이 허용되는 배치인가? | 좋은 회로인가? |
| wirelength·density·congestion proxy | 빠르게 비교할 때 어떤 배치가 유망한가? | 실제 PPA가 더 좋은가? |
| 별도 EDA 품질 평가 | 특정 물리 구현 단계에서 품질이 나아졌는가? | 다른 공정·도구·전체 제조 승인까지 보장되는가? |

원 preprint는 legalization 뒤 macro를 고정하고 EDA 도구로 standard cell을 배치·평가합니다. 후속 평가 논문은 Nature 실험의 **PlaceOpt**와 자신의 **postRouteOpt** 측정을 구분합니다. 따라서 proxy·EDA·sign-off를 같은 최종 검증이라고 압축하지 않습니다. [원문 §3.3.7](https://arxiv.org/html/2004.10746#S3.SS3.SSS7), [Cheng et al., TCAD §V·주석 12](https://vlsicad.ucsd.edu/Publications/Journals/j148.pdf)

### 4.3 2026년이라고 새 모델의 성과가 되지는 않는다

이번 공식 출처 조사에서 2026 AlphaChip 신모델 발표는 확인하지 못했습니다. 현재 소스 pin의 2026-02-11 변경은 주석의 오탈자 하나를 고친 것이므로 모델 개선의 증거가 아닙니다. [실제 commit diff](https://github.com/google-research/circuit_training/commit/c417a3a13f40867b649c719c03daaf1b39a909bc)

2026년 표기가 있는 *An Updated Assessment of Reinforcement Learning for Macro Placement*는 2025-12-06 accepted, DOI `10.1109/TCAD.2025.3644293`인 후속 평가입니다. CT from-scratch·checkpoint fine-tuning·pretraining을 stronger SA 등과 비교하며 seed·수렴·compute·공정·최종 평가 단계를 문제 삼습니다. 정보가 부족한 Ariane 변환본의 proxy와 ASAP7의 post-route PPA를 한 결과로 합치지 않습니다. [저자 공개 논문 §V–VIII](https://vlsicad.ucsd.edu/Publications/Journals/j148.pdf)

원저자들의 2024 응답도 사전학습·계산량·수렴·분포 차이를 지적합니다. 어느 쪽도 모든 조건에서의 승패로 일반화하지 않습니다. [Goldie et al. §2](https://arxiv.org/html/2411.10053v1#S2)

**적용 판단:** AlphaChip은 허용 후보와 빠른 탐색, 실제 품질 판정을 나누는 보조 근거로 사용합니다. AlphaEvolve의 Verilog 변경·2026 TPU 활용과 AlphaChip macro placement는 별개 사례입니다. 이 lab에 PPO, chip pretraining, 상용 EDA를 선행 구축할 이유는 생기지 않습니다.

## 5. 2026 개발 현장의 구체적인 작업 절차

### 5.1 NVIDIA TileGym — 파일이 있어도 검사가 끝난 것은 아니다

공개 Rust 변환 skill의 고정 revision은 `9ba5d94d59a87480483573dfe5e880b0d266d547`입니다. 첫 공개는 2026-07-10입니다. 필요한 경로는 다음과 같습니다. [고정 소스](https://github.com/NVIDIA/TileGym/tree/9ba5d94d59a87480483573dfe5e880b0d266d547/skills/tilegym-converting-cutile-triton-to-cutile-rs)

```text
SKILL.md                         작업 진입점
agents/agent_a.md ... agent_f.md  reference IR → Rust kernel → FFI·정확성 → 성능
concepts/ffi-bridge.md            C ABI·호출 경계
references/ir-diff-checklist.md   IR 대조 기준
scripts/preflight.sh             환경 확인
scripts/validate_*.sh             단계별 산출물·검사 확인
BENCHMARK.md · evals/evals.json   무엇을 평가했는지 확인
```

reference IR·baseline, `kernel.rs`, C ABI·shared library·Python wrapper, 정확성, CUPTI 성능을 나누고 진단·재시도 한도를 둡니다. 다만 지침에는 validator 부재·실패의 soft fallback이 있으며 최종 집계 스크립트는 수치 정확성을 독립 재실행하는 오라클이 아닙니다. [SKILL.md](https://github.com/NVIDIA/TileGym/blob/9ba5d94d59a87480483573dfe5e880b0d266d547/skills/tilegym-converting-cutile-triton-to-cutile-rs/SKILL.md)

2026-08-12 공개 표의 Claude Code Opus 4.8 **83→99%**, Codex GPT-5.5 **79→98%**는 **커널 성공률이 아닙니다**. 평가 파일의 네 사례는 overview 요청 하나와 해당 skill을 쓰면 안 되는 요청 세 개입니다. Rust 변환·수치 정확성·GPU 성능의 분모로 쓰지 않습니다. [BENCHMARK.md](https://github.com/NVIDIA/TileGym/blob/9ba5d94d59a87480483573dfe5e880b0d266d547/skills/tilegym-converting-cutile-triton-to-cutile-rs/BENCHMARK.md), [평가 항목](https://github.com/NVIDIA/TileGym/blob/9ba5d94d59a87480483573dfe5e880b0d266d547/skills/tilegym-converting-cutile-triton-to-cutile-rs/evals/evals.json)

앞선 2026-04-30 Julia 변환 사례는 17개 의미 규칙, API 대응표, 정적 validator와 dtype별 CPU reference 검사를 제시했습니다. 대표 GEMM의 약 4분·78K token은 변환 사례의 비용이며 speedup은 아닙니다. 모델도 “frontier LLM” 이상으로 특정하지 않습니다. [NVIDIA 원문](https://developer.nvidia.com/blog/automating-gpu-kernel-translation-with-ai-agents-cutile-python-to-cutile-jl/)

**적용 판단:** MD가 산출물·읽을 문서·검사 명령을 안내하고 스크립트가 실제 결과를 확인하는 분담을 가져옵니다. 공개 skill의 agent 수나 soft fallback을 복제하지 않습니다. 필요한 validator가 없으면 이 lab은 미실행으로 남기고 다음 채택 단계로 보내지 않습니다.

### 5.2 Anthropic — 독립 오라클과 회귀 검사를 사람이 만들었다

Opus 4.6 Claude Code agent 16개가 Docker·Git 작업 분담으로 Rust C compiler를 개발했습니다. GCC를 비교 오라클로 사용하고 후보 compiler와 GCC의 혼합 빌드로 실패를 좁혔습니다. 새 기능이 이전 기능을 깨뜨리자 사람이 CI를 보강했습니다. Linux 부팅 결과가 있어도 초기 연구 프로토타입이며, x86 real-mode 일부는 GCC에 의존하고 assembler·linker도 기존 도구를 사용했습니다. 코드 품질과 생성 코드 성능의 한계도 저자가 밝힙니다. [Anthropic 원문: Testing·Parallelism·Limitations](https://www.anthropic.com/engineering/building-c-compiler)

**적용 판단:** 큰 작업을 맡길 수 있는 현재 역량은 인정하되, agent 수·생성 줄 수를 목표로 삼지 않습니다. 먼저 실패를 구별할 비교 실행과 회귀 조건을 준비합니다. 다른 compiler와의 일치는 정의되지 않은 동작까지 정확하다는 증명이 아니므로 입력 의미·수치 계약도 확인합니다.

### 5.3 OpenAI — 짧은 진입점은 상세 근거와 검사로 연결된다

2026년 보고는 2025년 시작한 제품 개발의 내부 beta를 다룹니다. 짧은 `AGENTS.md`에서 버전 관리하는 상세 문서로 안내하고, 저장소 skill·스크립트·구조 lint·CI와 worktree별 관측 수단을 제공합니다. 초기 scaffold는 GPT-5/Codex CLI지만 전체 기간에 단일 모델을 사용했다는 근거는 없습니다. 약 10배 속도라는 표현은 저자의 추정이며 통제실험 결과가 아닙니다. 일부 agent merge와 선택적 사람 PR review는 이 lab의 승인 규칙과 다릅니다. [OpenAI 원문: Repository knowledge·Enforcement·Autonomy·Uncertainty](https://openai.com/index/harness-engineering/)

**적용 판단:** 현재 진입점·문서·검사기를 재사용합니다. 문서를 많이 넣는 대신 해당 작업의 코드·규칙을 찾을 수 있게 하고 실제 사용·검사 여부를 확인합니다. source layout만 복사하거나 자동 병합 권한을 따라 부여하지 않습니다.

### 5.4 ACES — skill의 효과는 내용이 아니라 실행 차이로 확인한다

`arXiv:2608.20614`는 GPU kernel 최적화 논문이 아니라 **Agentic Continuous Evaluation of Skills**입니다. task·model·harness·sandbox·scorer를 맞춘 skill 유무 비교를 설명합니다. 보고된 947 paired case는 58개 skill에서 나온 채점 사례이며, 947개의 독립 skill이나 균형 잡힌 모델 순위표가 아닙니다. 87개 negative case도 보고합니다. 별도의 단일 sanitization 진단에서는 최종 답 점수가 같아도 중간 산출물에 합성 secret canary가 남았습니다. 내부 원본 trajectory 비공개와 미채점 실행 제외도 결과 해석의 조건입니다. [원논문 §4–7](https://arxiv.org/html/2608.20614v1)

**적용 판단:** 최종 설명만 채점하지 않고 diff·실행 명령·중간 파일·판정 기록을 확인합니다. 스캐폴드의 효과는 같은 모델과 과제의 비교로 검증하며, 이 문서를 읽은 사실을 개선 증거로 쓰지 않습니다.

## 6. 기존 실험에 적용하는 최소 규칙

1. **진단부터 수정 단위를 정합니다.** 같은 오류가 반복될 때 파일 수를 늘리기보다 입력 의미, dependency, IR·호출 경계 중 어디서 가정이 깨졌는지 좁힙니다. 근거 없이 모든 작업을 compiler policy search로 바꾸지 않습니다.
2. **후보 생성과 검사 소유권을 분리합니다.** 초기 요구·허용 파일·baseline·보호 oracle·수치 오차·최종 판정 조건은 후보 전에 정합니다. 현재 과제의 생성 테스트와 보호 평가를 같은 파일로 취급하지 않습니다.
3. **공개 검사의 실패를 다음 행동에 연결합니다.** agent가 남긴 설명에 공개 실패 입력·diagnostic·관련 diff를 붙입니다. 같은 후보의 허용된 수정만 진행하며 다른 A/B 후보의 기록이나 보호 최종 검사 자료를 전달하지 않습니다. 다음 시도가 무엇을 바꿀지 밝히며 재시도 한도를 지킵니다. 이유와 실제 값은 hash로 대체하지 않습니다.
4. **탐색 점수와 채택 상태를 나눕니다.** 부분 통과·proxy·합성 benchmark는 탐색 정보입니다. 필요한 검사 누락은 `NOT_RUN`, 불완전 증거는 `INVALID`로 남깁니다. 필수 실패를 성능 점수로 상쇄하지 않습니다.
5. **같은 후보를 실제 용도에서 확인합니다.** CPU correctness, schedule, NPU 측정과 API 호환성은 별도 증거입니다. 통합 검증을 거친 결과와 남은 위험으로 사람이 채택 여부를 정합니다.

적용 위치는 [판단 컨텍스트](../docs/context.md), [운영 skill](../.agents/skills/review-to-verified-pr/SKILL.md), [기존 품질 계약](../docs/quality.md)입니다. 위 규칙은 operator의 선택 근거이며 전체 자료를 A/B 후보에게 주입하지 않습니다.

**조사와 실행 결과를 구분합니다.** 첫 과제는 공개 Rust double-buffering 테스트 보강이며 후속 비교 대상은 같은 모델의 기본 Codex 절차와 근거 기록 절차입니다. 이 조사를 마친 뒤 AWS CPU smoke와 로컬 Docker의 정상 검사·오류 대조군 검출을 별도로 완료했습니다. 최신 근거는 [실행 결과](../docs/kernels/double-buffering.md#8-로컬-docker-실행-결과)에 둡니다. A/B·Nebius 실행·RNGD 실측은 남아 있으며, 별도 population DB·RL 학습·최적화 엔진은 후속 필요성이 확인될 때 검토합니다.
