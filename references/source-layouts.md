# 원본 사례의 파일 구조와 채택 경계

확인일: 2026-09-14. 이 문서는 **설계 참고 대장**이며 실행 지침이 아닙니다. 고정 revision의 파일과 원문을 읽어 확인했으며, 아래 시스템을 설치하거나 실험 결과를 재현한 기록은 아닙니다.

파일 트리는 전체 목록이 아니라 관련 경로의 발췌입니다. `{a,b}`는 실제로 존재하는 같은 계층의 파일을 줄여 쓴 표기입니다. 실행 중 생성되는 파일은 추적된 소스와 따로 표시했습니다. 원문·전사·코드는 이 저장소에 복제하지 않고 출처로 연결합니다.

## 1. autoresearch: 수정 대상은 작게, 판정 조건은 고정

고정 revision: `228791fb499afffb54b46200aca536f79142f117` · [소스 트리](https://github.com/karpathy/autoresearch/tree/228791fb499afffb54b46200aca536f79142f117)

```text
autoresearch/                 # 이 revision은 루트 파일 10개이며 하위 폴더가 없음
├── README.md
├── program.md
├── prepare.py
├── train.py
├── analysis.ipynb
├── pyproject.toml
└── uv.lock
```

나머지 추적 파일은 `.gitignore`, `.python-version`, `progress.png`입니다. `run.log`와 `results.tsv`는 프로그램을 실행하며 만드는 기록이지, 위 revision에 들어 있는 원본 파일이 아닙니다.

**지침과 실행의 분담.** `program.md`는 에이전트가 `train.py`만 바꾸도록 지시합니다. 데이터 준비와 `evaluate_bpb`가 있는 `prepare.py`는 고정합니다. 실행 파일과 평가 조건을 나눠, 무엇을 바꿨을 때 성능이 달라졌는지 추적하는 구조입니다. 기본 실험은 단일 GPU에서 학습 시간 5분이며 시작·컴파일 시간은 제외됩니다. [실험 범위와 제약](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md#L11-L37)

**판정과 기록.** 기준 실행 뒤 후보를 커밋하고 실행하며, `val_bpb`와 메모리 사용량을 읽어 유지·폐기·실패를 `results.tsv`에 남깁니다. 원본 지침의 상태는 `keep/discard/crash`입니다. 무한 반복과 Git 되돌리기도 지침에 포함되어 있습니다. [결과 형식과 반복 절차](https://github.com/karpathy/autoresearch/blob/228791fb499afffb54b46200aca536f79142f117/program.md#L66-L114)

**가져올 판단.** 먼저 기준 실행을 재현하고, 후보마다 수정 범위·명령·결과·유지 사유를 남깁니다. 평가 프로그램을 바꾸는 작업과 평가 대상의 개선은 다른 변경으로 취급합니다.

**그대로 가져오지 않을 것.** 무한 반복은 유한한 시도·시간 예산으로 바꿉니다. 공유 브랜치의 자동 되돌리기를 사용하지 않습니다. 원본의 실패 점수 `0.000000`은 이 실험에 맞지 않으므로, 측정 실패는 수치가 아닌 실패 상태와 누락 사유로 보존합니다. MD의 수정 금지 문장과 해시 검사는 OS 접근 제어나 샌드박스가 아닙니다.

## 2. Dioxus: 에이전트가 만든 변경을 실행 가능한 회귀로 좁힌다

고정 revision: `ada3b67c73c1c5484dd2e8408cb21c470b200423` · [소스 트리](https://github.com/DioxusLabs/dioxus/tree/ada3b67c73c1c5484dd2e8408cb21c470b200423)

```text
dioxus/
├── AGENTS.md
├── notes/architecture/
├── .github/workflows/main.yml
└── packages/fuzz/
    ├── README.md
    ├── src/{case,harness,mutator,reducer,targeted}.rs
    └── fuzz/
        ├── fuzz_parallel_cmin.sh
        └── fuzz_targets/vdom_ops.rs
```

**문서를 읽는 순서.** `AGENTS.md`가 `notes/architecture/`로 연결합니다. 에이전트에게 모든 자료를 한꺼번에 주는 대신, 작업에 필요한 구조를 읽고 실제 코드로 확인하도록 안내합니다. CI에는 포맷·린트·문서 등 검사가 있지만, 워크플로 파일의 존재만으로 현재 실행 성공이나 필수 병합 설정까지 확인된 것은 아닙니다. [AGENTS.md](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/AGENTS.md), [CI](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/.github/workflows/main.yml)

**변이와 판정.** fuzz 코드는 구조화한 UI 연산을 만들고, 증분 갱신 결과와 새로 렌더링한 결과를 비교합니다. `case`는 입력 표현, `mutator`는 변이, `harness`는 실행·비교, `reducer`는 실패 축소를 맡습니다. 무작위 텍스트보다 시스템의 연산을 입력 단위로 삼는 점이 중요합니다. [fuzz 설명](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/README.md)

**회귀와 커버리지는 다릅니다.** `targeted.rs`의 엄격한 회귀 테스트는 의미 불일치를 실패로 처리합니다. 반면 coverage용 corpus 재생은 비교 결과를 의도적으로 무시하는 경로가 있습니다. 같은 입력을 실행했다고 해서 같은 판정 권한을 갖는 것은 아닙니다. [두 실행 경로](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/src/targeted.rs#L21-L108)

**실패의 보존.** 스크립트는 corpus 최소화(`cmin`) 뒤 제한 시간의 fuzz를 실행하고, 실패하면 입력 최소화(`tmin`)를 시도합니다. 최소화 성공으로 원래 fuzz 실패를 덮지 않도록 종료 상태를 보존합니다. 다만 corpus를 변경하고 CPU 수에 맞춰 worker를 늘리며, 모든 단계에 timeout이 있는 것은 아닙니다. [실행 스크립트](https://github.com/DioxusLabs/dioxus/blob/ada3b67c73c1c5484dd2e8408cb21c470b200423/packages/fuzz/fuzz/fuzz_parallel_cmin.sh)

**운영 경험의 맥락.** Jonathan Kelley의 발표는 코드 생성량보다 병합할 변경의 품질, 사람이 설계한 검사 조건, 에이전트의 fuzz 보조, 과도한 리팩터링 검토를 다룹니다. 전사는 설계 동기를 이해하는 자료이고, 구현 주장은 위 고정 코드에서 확인합니다. [발표: Building ambitious software](https://www.youtube.com/watch?v=H7vFrcNWXzs&t=378s)

**가져올 판단.** 컴파일러 입력의 구조를 유지하는 변이를 만들고, 실패를 작은 입력으로 줄여 회귀 테스트에 추가합니다. 커버리지 확보와 의미 보존 검증의 결과를 섞지 않습니다. 검사는 성공·실패와 재현 명령을 반환하고, 사람은 변경 범위와 남은 위험을 검토합니다.

**그대로 가져오지 않을 것.** UI의 비교 오라클을 컴파일러에 그대로 쓰지 않습니다. worker 자동 확대, corpus 자동 변경, timeout 없는 단계를 복제하지 않습니다. 공개 CI를 근거로 모든 변경이 자동으로 안전하게 병합된다고 서술하지 않습니다.

## 3. AlphaEvolve: 생성·평가·보관을 나누되 공개 범위를 구분한다

[원논문 v1, 2025-06-16](https://arxiv.org/html/2506.13131v1)과 [DeepMind 소개, 2025-05-14](https://deepmind.google/blog/alphaevolve-a-gemini-powered-coding-agent-for-designing-advanced-algorithms/)는 초기 프로그램, 후보 생성, 평가, 프로그램 저장소, 다음 후보의 선택을 분리합니다. 저렴한 검사에서 후보를 먼저 거르고 비싼 평가로 진행하며, 여러 지표와 과거 프로그램을 탐색에 사용합니다. 이는 저자들이 보고한 시스템이며 이 저장소의 실행 결과가 아닙니다.

### 3.1 Google Cloud 공개 client와 예제

고정 revision: `b51ab7a6446d0168bf6db52c6dccbec414a21b3f` · 커밋: 2026-07-27 · [소스 트리](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/tree/b51ab7a6446d0168bf6db52c6dccbec414a21b3f)

```text
alphaevolve-on-googlecloud/
├── src/alpha_evolve/{client,controller,experiment,workers}.py
├── tests/{test_client,test_controller,test_evaluator,test_experiment}.py
├── examples/circle_packing/
│   ├── instructions.md
│   └── src/{program,evaluate,run_evolution}.py
├── examples/adaptive_sort/{evaluator.py,run_experiment.py}
└── skills/
    ├── alpha_evolve_experiment_design/SKILL.md
    ├── alpha_evolve_experiment_design/examples/circle_packing/
    ├── alpha_evolve_post_experiment/SKILL.md
    └── ae_cli/{client,controller,evaluator}.py
```

**MD와 실행.** 공개 라이브러리는 관리형 서비스에서 후보를 받아 로컬 평가를 수행하고 결과를 제출하는 client입니다. 설계 skill은 문제 설명, 초기 프로그램, 평가기, 각각의 테스트를 준비하도록 안내합니다. 공개된 skill의 행동 지시는 여기서 실행하지 않고 설계 참고로만 읽습니다. [README](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/blob/b51ab7a6446d0168bf6db52c6dccbec414a21b3f/README.md), [실험 설계 skill](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/blob/b51ab7a6446d0168bf6db52c6dccbec414a21b3f/skills/alpha_evolve_experiment_design/SKILL.md)

**평가기 자체도 시험합니다.** 예제에는 `evaluator.py`, `initial_program.py`, `test_evaluator.py`, `test_program.py`, `problem_description.md`, `example_evaluation.json`이 함께 있습니다. 개선 대상의 테스트와 점수를 만드는 평가기의 테스트를 구분할 수 있는 실제 구조입니다. [설계 예제](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/tree/b51ab7a6446d0168bf6db52c6dccbec414a21b3f/skills/alpha_evolve_experiment_design/examples/circle_packing)

**공개 client가 전체 탐색 엔진은 아닙니다.** 후보의 획득과 평가 제출 코드는 공개되어 있지만, 관리형 서비스의 모델·후보 선택·프로그램 DB를 모두 재현하는 저장소는 아닙니다. 또한 circle-packing 실행 예제는 후보 코드를 `exec`로 읽습니다. 이 예제만으로 평가 코드의 변조 방지나 OS 격리가 구현되었다고 판단할 수 없습니다. [client 경계](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/blob/b51ab7a6446d0168bf6db52c6dccbec414a21b3f/src/alpha_evolve/client.py#L262-L302), [후보 실행 코드](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/blob/b51ab7a6446d0168bf6db52c6dccbec414a21b3f/examples/circle_packing/src/evaluate.py#L45-L78)

**실험과 통합의 기록.** skill은 실행 중 `.evolve/experiment_description.json`, `.evolve/source_map.json` 등을 만들도록 안내하고, 실험 뒤에는 보상 편법과 원래 코드로의 통합을 검토합니다. 이 이름들은 생성되는 작업 자료이며, 모두 원본 tree에 추적된 실험 결과라는 뜻은 아닙니다. [후속 검토 skill](https://github.com/Google-Cloud-AI/alphaevolve-on-googlecloud/blob/b51ab7a6446d0168bf6db52c6dccbec414a21b3f/skills/alpha_evolve_post_experiment/SKILL.md)

### 3.2 공개 결과와 문제 저장소

결과 revision: `4226acbf237ff9ad10ba7673a2af127a2d8a5971` · 2026-01-05 · [결과 트리](https://github.com/google-deepmind/alphaevolve_results/tree/4226acbf237ff9ad10ba7673a2af127a2d8a5971)

문제 revision: `8f447457957deac61e28bf1676746f0753b3b2f8` · 2026-07-11 · [문제 트리](https://github.com/google-deepmind/alphaevolve_repository_of_problems/tree/8f447457957deac61e28bf1676746f0753b3b2f8)

```text
alphaevolve_results/
├── README.md
└── mathematical_results.ipynb
alphaevolve_repository_of_problems/
├── README.md
├── experiments/packing_circles_max_sum_of_radii/packing_circles_max_sum_of_radii.ipynb
├── experiments/finite_field_kakeya_problem/finite_field_kakeya.ipynb
├── experiments/finite_field_kakeya_problem/lean_proof/{kakeya.lean,lakefile.toml,lean-toolchain}
├── problems/1.html
└── status.json
```

이 자료는 문제 설명·구성·결과 검증을 읽을 수 있는 공개 산출물입니다. 문제 저장소는 AlphaEvolve를 실행하는 코드가 포함되어 있지 않다고 명시합니다. notebook이나 Lean 증명 파일이 존재하는 것과 탐색 서비스를 재현할 수 있는 것은 구분해야 합니다. [문제 저장소의 공개 범위](https://github.com/google-deepmind/alphaevolve_repository_of_problems/blob/8f447457957deac61e28bf1676746f0753b3b2f8/README.md)

**가져올 판단.** 후보를 만들기 전에 입력·수정 영역·지표를 정하고 평가기 오류부터 검사합니다. 값싼 문법·빌드 검사, 의미 보존 검사, 비용이 큰 실측을 순서대로 적용합니다. 실패와 살아남은 후보를 함께 기록하되, 탐색 점수 상승을 원래 프로그램에 통합할 근거와 구분합니다.

**그대로 가져오지 않을 것.** 관리형 탐색 서비스나 모델을 공개 구현이라고 부르지 않습니다. API·클라우드 작업의 자동 시작이나 종료 없는 탐색을 도입하지 않습니다. 여러 지표를 썼다는 사실만으로 독립 검증이 성립한다고 판단하지 않습니다. 원논문도 작업별로 시뮬레이션, 실제 하드웨어, 전문가 검토 등 서로 다른 확인 절차를 사용합니다.

## 4. AlphaChip: 값싼 proxy는 후보를 줄이고 최종 판정은 별도로 한다

고정 revision: `c417a3a13f40867b649c719c03daaf1b39a909bc` · 커밋: 2026-02-11 · [소스 트리](https://github.com/google-research/circuit_training/tree/c417a3a13f40867b649c719c03daaf1b39a909bc)

```text
circuit_training/
├── circuit_training/environment/{environment,plc_client}.py
├── circuit_training/environment/test_data/ariane/{netlist.pb.txt,initial.plc}
├── circuit_training/grouping/{grouper,grouping}.py
├── circuit_training/dreamplace/{dreamplace_core,plc_converter}.py
├── circuit_training/learning/{train_ppo,ppo_collect,ppo_reverb_server,eval,eval_lib}.py
├── circuit_training/model/{model,model_lib}.py
├── docs/{PLACEMENT_COST,PRETRAINING,ARIANE}.md
├── tools/e2e_smoke_test.sh
└── tox.ini
```

**MD는 학습·평가 환경의 안내입니다.** 위 문서는 LLM 코딩 에이전트의 행동 정책이 아니라 netlist, placement cost, 사전학습·평가 작업을 구성하는 안내입니다. 공개 구현은 정책 학습, 수집 worker, Reverb, 평가 실행을 분리합니다. [사전학습 구성](https://github.com/google-research/circuit_training/blob/c417a3a13f40867b649c719c03daaf1b39a909bc/docs/PRETRAINING.md)

**변이의 표현과 값싼 판정.** 정책은 매크로를 배치하고, 환경은 허용하지 않는 위치를 마스킹합니다. 배치 비용은 wirelength·density·congestion의 근삿값으로 구성합니다. 후보를 빠르게 비교할 수 있지만, 이 수치만으로 제조 가능한 설계나 최종 PPA가 증명되지는 않습니다. [환경의 비용 계산](https://github.com/google-research/circuit_training/blob/c417a3a13f40867b649c719c03daaf1b39a909bc/circuit_training/environment/environment.py#L83-L129), [placement cost의 성격](https://github.com/google-research/circuit_training/blob/c417a3a13f40867b649c719c03daaf1b39a909bc/docs/PLACEMENT_COST.md)

**공개 소프트웨어와 최종 검증.** README는 빠른 proxy 평가와 상용 EDA를 사용하는 최종 품질 평가를 구분합니다. 또한 공개 학습 코드는 논문에 근거한 재구현이며 내부 인프라를 그대로 공개한 것은 아닙니다. placement-cost client가 연결하는 공개 바이너리 역시 전체 EDA 소스 공개와 다릅니다. [README의 평가·재구현 설명](https://github.com/google-research/circuit_training/blob/c417a3a13f40867b649c719c03daaf1b39a909bc/README.md#L536-L579)

**원문 맥락.** [2020년 논문](https://arxiv.org/abs/2004.10746), [2021년 Nature 논문](https://www.nature.com/articles/s41586-021-03544-w), [2024-09-26 DeepMind 설명](https://deepmind.google/blog/how-alphachip-transformed-computer-chip-design/)을 구분해 읽습니다. 제품 배치 성과는 저자·기업의 보고이며, 위 공개 예제의 로컬 실행 결과로 바꾸어 서술하지 않습니다.

**가져올 판단.** 수정안을 무제한 텍스트가 아니라 제약을 확인할 수 있는 표현으로 만듭니다. 값싼 신호는 탈락시킬 후보를 줄이는 데 사용하고, 승인에 필요한 정확성·타깃 측정은 별도 단계에서 확인합니다. Compiler AX에서 CPU host 검사와 NPU 실행을 구분하는 이유도 이와 같습니다.

**그대로 가져오지 않을 것.** PPO 학습·분산 수집 인프라를 만들지 않습니다. 비공개 netlist나 상용 EDA가 있는 것으로 가정하지 않습니다. proxy 개선을 최종 성능 개선으로 승격하지 않습니다. 제공 smoke script에도 외부 timeout이 필요한 경로가 있어, 이름만 보고 제한된 실행으로 판단하지 않습니다. [smoke script](https://github.com/google-research/circuit_training/blob/c417a3a13f40867b649c719c03daaf1b39a909bc/tools/e2e_smoke_test.sh)

## 5. Tao: 정답보다 가설이 막힌 이유를 보존한다

이 사례는 공개 게시물에 담긴 **논의 구조**입니다. 에이전트 운영 저장소·고정 commit·실제 폴더 구조를 확인한 사례가 아니므로 파일 트리를 붙이지 않습니다.

2026-09-03 게시물은 하나의 ansatz에서 출발해 정확한 장애를 발견하고, 그 장애를 일부 제거하도록 ansatz를 조정하는 탐색을 설명합니다. 최종 형태만 알면 실패했던 길에서 얻을 통찰을 놓칠 수 있다는 맥락입니다. [원문 게시물](https://mathstodon.xyz/@tao/117207855800042681)

```text
논의 구조 — 저장소나 실행 로그가 아님
초기 가설 → 구체적인 장애 확인 → 가설·표현 조정
         → 재검토 → 막힌 이유와 변경의 근거 보존
```

2026-09-05에는 Navier–Stokes와 관련된 해당 논의가 가상 상황이며, 유의미한 새 진전을 알고 있는 것은 아니라고 명확히 했습니다. 따라서 “Tao의 제안으로 OpenAI가 방정식을 풀었다”는 전제로 이 실험을 설계하지 않습니다. [후속 해명](https://mathstodon.xyz/@tao/117219101339291693)

**기록에 가져올 판단.** 후보의 성공 여부만 남기지 않고, 어떤 입력에서 어떤 가정이 깨졌으며 다음 변경이 그 원인을 어떻게 다루는지 남깁니다. 최종 patch에서 사라지는 폐기 사유도 재현 가능한 입력과 함께 보존합니다.

**그대로 가져오지 않을 것.** 수학적 탐색을 컴파일러 정확성의 증명으로 대체하지 않습니다. 공개 토론을 실행 가능한 agent 시스템이나 실제 해결 성과로 포장하지 않습니다. 이 사례는 가설과 반증을 기록하는 태도의 참고이며, 코드 판정은 테스트·오라클·검토자가 맡습니다.

## 이 실험에 적용하는 공통 기준

1. **문서는 범위를 설명하고 실행기는 이를 검사합니다.** 허용 파일, 명령, 자원 예산, 종료 조건을 지침만이 아니라 실행 설정과 결과로 확인합니다.
2. **후보와 평가기를 함께 고치지 않습니다.** 평가기 변경은 별도 검토하며, 후보의 점수와 평가기 테스트 결과를 다른 기록으로 남깁니다.
3. **빠른 검사 통과는 다음 검사로 갈 자격입니다.** 문법·빌드·proxy 통과를 의미 보존이나 실제 NPU 성능의 증거로 사용하지 않습니다.
4. **실패를 작은 재현 사례로 남깁니다.** 입력, 변경, 명령, 원래 종료 상태, 판정 이유를 보존하고 실패를 정상 점수로 채우지 않습니다.
5. **탐색 결과와 병합 결정을 나눕니다.** 후보 생성자는 변경을 제안하고, 검증은 증거를 생산하며, 검토자는 그 증거와 변경 범위를 보고 승인·반려합니다.

이 대장의 출처 검토는 위 기준의 설계 근거입니다. 이 저장소에서 실제로 설정·실행·통과한 범위는 해당 실행의 명령, 산출물, 결과 기록으로 별도 확인해야 합니다.
