#!/usr/bin/env bash
# Only the frozen binary and this wrapper belong in the fresh runtime container.
# The controller calls it only after BOTH candidates are frozen and supplies the
# read-only/no-network/non-root resource boundary. No implementation label input.
set -euo pipefail

if [[ $# != 1 ]]; then
  printf 'Usage: bash run-frozen-test.sh EXACT_PUBLIC_TEST_NAME\n' >&2
  exit 2
fi
ax_test=$1
case "$ax_test" in
  test_double_buffering_rolled|test_double_buffering_software_pipelined|test_double_buffering_unrolled) ;;
  *) printf 'INVALID_TEST_NAME: only an exact public SDK test is allowed\n' >&2; exit 2 ;;
esac
# Keep argument rejection ahead of Linux-only checks and binary access.
[[ $(uname -s) == Linux && $(uname -m) == x86_64 && $(id -u) == 1000 ]] || {
  printf 'STOP: requires UID 1000 in the x86_64 Linux runtime container\n' >&2
  exit 126
}
export PATH=/usr/bin:/bin LC_ALL=C LANG=C TZ=UTC
for ax_file in /trial/test /usr/bin/env /usr/bin/timeout; do test -x "$ax_file"; done
[[ -f /trial/test && ! -L /trial/test ]]
for ax_file in memory.events memory.peak; do test -r "/sys/fs/cgroup/$ax_file"; done

finish() {
  local ax_status=$? ax_file
  trap - EXIT
  set +e
  printf 'runtime_exit=%s\n' "$ax_status"
  for ax_file in memory.events memory.peak; do
    printf '/sys/fs/cgroup/%s\n' "$ax_file"
    cat "/sys/fs/cgroup/$ax_file" || printf 'RECORD_UNAVAILABLE: %s\n' "$ax_file" >&2
  done
  exit "$ax_status"
}
trap finish EXIT
trap 'exit 130' INT
trap 'exit 143' TERM
printf 'selected_test=%s\n' "$ax_test"
sha256sum /trial/test
TIMEFORMAT='runtime_wall_seconds=%R runtime_user_seconds=%U runtime_system_seconds=%S'
time /usr/bin/env -i PATH=/usr/bin:/bin LC_ALL=C LANG=C TZ=UTC \
  RAYON_NUM_THREADS=2 RUST_TEST_THREADS=1 \
  /usr/bin/timeout --kill-after=10s 120s \
  /trial/test --exact "$ax_test" --nocapture --test-threads=1 --format pretty --color never
# libtest's zero-test exit 0 is NOT a verdict. The controller must observe exactly
# one executed selected test and distinguish assertions from timeout/capture errors.
