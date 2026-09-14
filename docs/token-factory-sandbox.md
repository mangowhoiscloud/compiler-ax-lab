# Token Factory Sandbox: CPU 기준 실행을 위한 준비

확인일: 2026-09-14. **로컬 CLI·client 설치와 무네트워크 검사를 완료했다. 베타 신청은 접수 완료했으며 실행 권한 승인을 기다린다. API 인증·Rust 빌드·원격 실행은 `NOT_RUN`이다.** 신청 접수는 권한 활성화의 증거가 아니다. 이 문서는 첫 무변경 CPU smoke의 환경 선택을 다룬다. [본 실험의 비교·판정 계약](experiment.md)은 유지한다.

## 1. 선택 이유와 현재 범위

필요한 것은 모델 추론 API가 아니라 고정 Rust 코드를 빌드하고 실행할 Linux worker다. Token Factory는 모델 API 외에도 OCI 이미지를 실행하는 **Sandboxes beta**를 제공한다. 별도 AI Cloud VM을 구매하기 전에 이 경로의 적합성을 확인한다. Codex 구독 세션은 로컬에 남기며, Sandbox로 개인 인증정보를 보내지 않는다. [공식 개요](https://docs.tokenfactory.nebius.com/sandboxes/overview)

현재 로그인한 [Sandboxes 안내 화면](https://tokenfactory.nebius.com/sandboxes/about)은 베타 동안 실행이 무료이고 크레딧을 차감하지 않는다고 표시한다. 외부 API 사용에는 베타 접근 신청을 안내하며, 브라우저 Playground의 응답은 시뮬레이션이라고 명시한다. 따라서 Playground 출력은 실행 증거가 아니다. 화면이 금지한 개인정보·민감 데이터를 올리지 않으며, 이번 실험은 공개 코드만 사용한다. 일반 출시 이후 가격이나 영구 무료를 보장하는 문구로 해석하지 않는다.

[Token Factory 과금 문서](https://docs.tokenfactory.nebius.com/other-capabilities/billing-new)와 [AI Cloud 프로모션 문서](https://docs.nebius.com/signup-billing/payments/promo-codes)는 각 제품의 크레딧을 설명하지만 자동 잔액 공유를 보장하지 않는다. 이번 준비에서 AI Cloud 결제·VM·디스크·IP를 생성하지 않았다. 프로모션 잔액과 Sandbox 실행 권한도 별도로 확인한다.

## 2. 공개 계약과 실행 전에 측정할 값

| 항목 | 확인한 공개 계약 | 이번 실험에서의 처리 |
|---|---|---|
| 실행·격리 | OCI 이미지, VM 격리, 명령 실행과 파일시스템 snapshot을 제공한다. | Ubuntu 24.04 amd64 이미지 digest를 고정한 뒤 실행한다. 프로세스·RAM까지 복원하는 checkpoint라고 가정하지 않는다. |
| CPU·RAM·아키텍처 | 조사한 API에는 CPU 수·RAM·아키텍처 선택 필드가 없다. `x86_64`는 이벤트 예시다. | 첫 짧은 probe에서 `uname`, online CPU, cgroup CPU quota·memory limit, `/proc/meminfo`, `df`를 수집한다. 기존 8 vCPU·32 GiB VM 계획을 Sandbox 사양으로 옮겨 적지 않는다. |
| 디스크 | `resources_limits.max_layer_bytes`의 기본값은 12 GiB다. | writable layer 상한이지 전체 디스크 보장량이 아니다. dependency·Rust build cache의 실제 증가량을 확인한다. |
| 접근·한도 | IAM bearer와 Project 헤더를 사용한다. `whoami`는 현재 토큰의 권한·한도 맵을 반환한다. 필요한 시간·동시성 항목은 실제 응답에서 확인한다. | 저장된 profile의 프로젝트를 먼저 대조한다. `whoami`에는 project 필드가 없으므로 서버가 프로젝트 일치를 확인했다고 쓰지 않는다. `list` 권한만으로 spawn 준비 완료가 아니다. |
| 네트워크 | 기본 활성화이며 비활성화할 수 있다. | 공개 dependency 설치까지만 허용한다. cache 준비 후 네트워크 없이 실행 가능한지 별도로 확인한다. |
| 출력·시간 | API 출력 기본값은 stream당 1 MiB, 최대 10 MiB다. CLI 기본값은 64 KiB·120초다. | Rust 빌드에 기본값을 그대로 적용하지 않는다. 실제 계정 한도 안에서 준비·빌드·테스트·수거 시간을 따로 제한한다. |
| 저장·분기 | SDK는 기본 disposable, CLI/API는 기본 non-disposable이다. 미참조·미태그 snapshot의 공개 보존 안내는 180일이다. | 환경 probe는 disposable, dependency 준비·검사 기록은 명시적 non-disposable로 구분한다. 필요한 파일은 즉시 로컬로 수거하며 장기 보관을 서비스에 맡기지 않는다. |

근거: [OpenAPI](https://eu-north.nebius.computer/static/api.yaml), [명령 실행](https://docs.tokenfactory.nebius.com/sandboxes/cli/commands/run), [분기](https://docs.tokenfactory.nebius.com/sandboxes/sdk/python_sdk/branching), [공식 client](https://github.com/nebius/contree-client). 공개 기본값보다 실제 프로젝트의 권한·한도를 우선한다.

## 3. 설치한 도구와 우회해야 할 동작

별도 Python 3.12 환경에 `contree-cli==0.9.4`, `contree-client==0.4.0`만 설치했다. 전역 PATH·인증 설정·기존 실험 실행기는 바꾸지 않았다. 인증·cache는 별도 `CONTREE_HOME`에 둔다. 계정·토큰·실행 로그는 Git에서 제외한다.

설치된 CLI의 `client_from_profile`은 `RetryPolicy(max_attempts=None, retry_unsafe=True)`를 사용한다. 생성 요청의 응답이 유실됐을 때 무제한 재시도로 중복 생성될 위험이 있으므로 CLI `run/build`를 무인 controller로 쓰지 않는다. 조회는 공식 stdlib client에 아래 설정을 명시한다. HTTP 대기 한도와 원격 작업 실행 한도는 별개다.

```python
from contree_client import RetryPolicy
from contree_client.http import ContreeClient

with ContreeClient.from_profile(
    profile, timeout=15.0,
    retry=RetryPolicy(max_attempts=1, retry_unsafe=False),
) as client:
    account = client.whoami()
```

로컬 preflight는 패키지 버전·profile의 IAM 유형·endpoint·예상 프로젝트를 검사한 뒤, 사용자가 요청한 경우에만 `whoami`를 한 번 조회한다. 토큰·응답 원문·예외 본문은 출력하지 않는다. 인증정보가 없으면 `NOT_CONFIGURED`로 끝낸다. 별도 가짜 응답 검사에서는 네트워크 연결을 막고, 권한 부족·프로젝트 불일치·timeout·민감값 비출력을 확인했다.

추가 주의점은 세 가지다.

1. CLI `build`는 완전한 Docker build가 아니다. `CMD`, `ENTRYPOINT`, `HEALTHCHECK`, `SHELL`, `COPY --from` 등을 그대로 실행하지 않으므로 upstream Dockerfile을 무비판적으로 전달하지 않는다. 이번 plain Cargo 검사에 필요한 공개 dependency만 설치한다. [Build 안내](https://docs.tokenfactory.nebius.com/sandboxes/cli/tutorial/build)
2. CLI가 합성한 operation JSON은 출력의 `truncated` 값을 보존하지 못할 수 있다. 원시 SSE와 실제 API 상태, 파일 원본을 우선한다. 출력 누락 여부가 불명확하면 완전한 결과로 인계하지 않는다. [CLI 구현](https://github.com/nebius/contree-cli/blob/3fc9c2f1061db8ca039d1eaf6b1f59b28464a764/contree_cli/cli/run.py)
3. `contree auth`는 토큰을 안전한 prompt로 받을 수 있지만 등록 때 API 검증을 수행한다. `--token` 인자에 비밀을 넣지 않는다. 등록용 환경변수와 실행 시 사용하는 저장 profile을 혼동하지 않는다. 이번에는 profile이나 API 키를 생성하지 않았다. [설치·인증](https://docs.tokenfactory.nebius.com/sandboxes/cli/tutorial/installation)

## 4. 첫 실행의 순서와 중단 기준

```text
베타 승인 → 인증·실제 한도 조회 → 짧은 환경 probe
 → 적합성 확인 → 고정 소스·toolchain·native 준비
 → 기존 CPU 테스트 1개 → 원문 파일 수거·재검증 → 사람 확인
```

1. **접근:** 베타 승인을 받은 뒤 전용 profile을 준비한다. 허용 권한·한도가 없으면 VM 구매나 다른 모델 API로 자동 우회하지 않는다.
2. **환경:** 1개 작업만 사용해 Linux/x86-64·GLIBC·CPU/RAM·저장 한도를 확인한다. 계정 실행 한도와 빌드 요구가 맞지 않으면 원인을 기록하고 멈춘다. 물리 CPU 모델·전용 코어를 추정하지 않는다.
3. **준비:** Ubuntu 24.04 amd64 digest, `build-essential`, `libclang-dev`, `git`, `curl`, `ca-certificates`, GNU `coreutils`, `time`을 고정한다. Rust는 `nightly-2026-05-01`을 사용한다. 공개 source·lockfile·native `.a`와 라이선스를 출처·전체 hash로 확인한다. API·Codex·GitHub 인증정보는 guest에 넣지 않는다.
4. **검사:** 후속 AWS 2 vCPU·8 GiB smoke 승인에 맞춰 공용 worker는 `CARGO_BUILD_JOBS=1`, `RAYON_NUM_THREADS=2`, `RUST_TEST_THREADS=1`로 낮췄다. clean source와 별도 build cache를 사용하며 성능 최적값이라는 의미는 아니다. `--list`도 컴파일을 유발한다. AWS 선택은 [실험 계약](experiment.md#작업과-환경)에 두며 Sandbox가 실행됐다는 뜻이 아니다.
5. **판정:** 고정 revision, exit=0, 실제 `test_binary_add_2048` 통과와 summary의 1 passed·0 failed·0 ignored·1 filtered out, 변경 없는 lockfile을 확인한다. 실행 상태 `SUCCESS`나 자체 `PASS` 문자열만으로 판정하지 않는다.
6. **수거:** 명령·환경·native hash·stdout/stderr·exit·`time -v` 기록과 operation/result image UUID를 연결한다. 실행 시간과 출력 상한을 먼저 정하고, 완료 후 파일 원본·크기·hash를 로컬에서 확인한다. 원격 수거·검증 연결은 아직 실행하지 않았다.

```bash
cargo +nightly-2026-05-01 test --locked --color never \
  -p furiosa-opt-examples --release --test binary_add_tests -- --list --color never
cargo +nightly-2026-05-01 test --locked --color never \
  -p furiosa-opt-examples --release --test binary_add_tests \
  -- --exact test_binary_add_2048 --test-threads=1 --format pretty --color never
```

대상은 [furiosa-opt v0.8.1](https://github.com/furiosa-ai/furiosa-opt/tree/9b9cf0fdc78df00cdc430eae725a5ad9084a735e)이다. 이 검사는 공개 CPU 경로에서 기존 정수 덧셈 assertion이 동작하는지 확인한다. NPU lowering·RNGD 정확성·성능 측정이나 double-buffering 테스트 보강의 완료가 아니다.

## 5. 실패·취소 뒤 무엇이 남는가

`op wait --timeout`은 관찰만 중단하며 원격 작업을 취소하지 않는다. 정확히 이 작업이 생성한 operation UUID만 취소한다. `--all`은 프로젝트 전체에 영향을 줄 수 있으므로 쓰지 않는다. DELETE 202 응답 뒤에도 terminal 상태를 다시 조회한다. 생성 요청의 결과가 불명확하면 `UNKNOWN_RECONCILE`로 두고, 목록과 식별자를 대조하기 전 재생성하지 않는다. 공개 API에서 create의 idempotency key 보장을 찾지 못했다. [Operation 안내](https://docs.tokenfactory.nebius.com/sandboxes/cli/commands/operation)

**취소된 operation은 events가 삭제되고 결과 image UUID가 null이 될 수 있다.** 따라서 실행 중 받은 SSE는 controller에 저장한다. 초기 worker 초안은 종료 때 마지막 출력만 stream에 내보냈지만, 후속 AWS·Docker 실행에서는 [전체 stdout/stderr 보존과 수집 종료 코드](quality.md#cpu-smoke의-관측성과-기록-규격)를 분리하도록 보강했다. 이 로컬·AWS 관측 결과가 Token Factory의 수거 성공을 뜻하지는 않는다. Sandbox에서는 중간 취소로 이미지와 미수거 로그가 사라지는지 별도 확인해야 하며, 복구하지 못한 구간은 `NOT_RETAINED`로 남긴다.

정상 종료 후에는 새 worker를 생성하지 않고 아래 조회로 결과 파일을 가져올 수 있다. 조회 대상 UUID·파일 경로·응답 크기를 검증하고, tar는 경로 이탈·symlink를 검사한 뒤 별도 디렉터리에 풀어야 한다. snapshot 보존과 실행 프로세스 종료는 별개 상태로 기록한다.

```text
GET /v1/inspect/{result_image_uuid}/download?path=/evidence/environment.txt
GET /v1/inspect/{result_image_uuid}/archive?path=/evidence
```

근거: [파일 다운로드](https://docs.tokenfactory.nebius.com/api-reference/sandboxes/inspect/download-a-file-from-image), [디렉터리 수거](https://docs.tokenfactory.nebius.com/api-reference/sandboxes/inspect/download-a-file-or-a-directory-from-image-as-tar-archive), [OpenAPI](https://eu-north.nebius.computer/static/api.yaml).

## 6. 고정한 출처와 준비 상태

| 근거 | 고정 값 |
|---|---|
| 설치 CLI / client | `contree-cli 0.9.4` / `contree-client 0.4.0` |
| CLI wheel의 PyPI SHA-256 | `1bf33a9f70066d45623ca8fc46f33868db45107170b208c46c06dd1457f18af8` |
| Client wheel의 PyPI SHA-256 | `0e262c1bf32432ba2142fa44b55c3310e3338044c2a55194c9d926794b6099c3` |
| OpenAPI 및 설치 client의 `SPEC_SHA256` | `23d748a2918b1124b3072d54d17d8eb43aa00d0b969bc1fa718f34ac884ee887` |
| 비교한 공개 CLI commit | `3fc9c2f1061db8ca039d1eaf6b1f59b28464a764` |
| 공개 client commit | `5a5f4510c0dee1e72d20e471468f05fe433cd897` |
| 공개 SDK commit | `38d973120ecdb8e459ab7ee375704c7aef54d035` |

Wheel hash는 [PyPI CLI 메타데이터](https://pypi.org/pypi/contree-cli/0.9.4/json)와 [client 메타데이터](https://pypi.org/pypi/contree-client/0.4.0/json)의 값이다. 공개 CLI commit의 패키지 버전은 설치판과 다르므로 설치 코드를 직접 확인한 재시도 동작과 구분한다. SDK는 조사만 했으며 설치하지 않았다.

로컬 준비 파일은 Git에서 제외한 `.local/tokenfactory-sandbox/`의 `preflight.py`, `cpu-smoke.sh`, `README.md`다. 무네트워크 preflight 검사·shell 구문·가짜 테스트 출력 검사는 통과했다. **API 접근 승인, 실제 환경 probe, native 설치와 Rust 빌드, 원격 로그 수거는 남아 있다.** 계정별 신청서·인증자료·실행 기록은 공개 문서에 복제하지 않는다.
