#!/bin/bash
# A small binary for accessing runfiles.
#
# Implements the subject contract in `CONTRIBUTING.md`.

__init_start="${EPOCHREALTIME:-}"

# {RUNFILES_CONFORMANCE}

__init_end="${EPOCHREALTIME:-}"

set -euo pipefail

EXIT_ERROR=1
EXIT_NO_RUNFILES=2
EXIT_NOT_FOUND=3
EXIT_BENCH_UNSUPPORTED=5

usage() {
    echo "Usage: $0 [--bench ITERATIONS] <rlocationpath>..." >&2
    echo "Example: $0 workspace/path/to/file.txt" >&2
}

BENCH_ITERATIONS=""
if [[ "${1:-}" == "--bench" ]]; then
    if [[ $# -lt 2 ]]; then
        usage
        exit "${EXIT_ERROR}"
    fi
    BENCH_ITERATIONS="$2"
    shift 2
fi

if [[ $# -lt 1 ]]; then
    usage
    exit "${EXIT_ERROR}"
fi

# The library's own discovery has run by now (at source time). Mirror its
# notion of "no runfiles" so the exit code is meaningful.
if [[ ! -d "${RUNFILES_DIR:-/dev/null}" && ! -f "${RUNFILES_MANIFEST_FILE:-/dev/null}" ]]; then
    echo "Failed to locate runfiles" >&2
    exit "${EXIT_NO_RUNFILES}"
fi

if [[ -n "${BENCH_ITERATIONS}" ]]; then
    if [[ -z "${EPOCHREALTIME:-}" ]]; then
        echo "Benchmarking requires bash >= 5 (EPOCHREALTIME)" >&2
        exit "${EXIT_BENCH_UNSUPPORTED}"
    fi

    # EPOCHREALTIME is "<seconds>.<microseconds>"; dropping the dot yields
    # integer microseconds.
    init_ns=$(( (${__init_end/./} - ${__init_start/./}) * 1000 ))

    lookup_start="${EPOCHREALTIME}"
    {
        for ((i = 0; i < BENCH_ITERATIONS; i++)); do
            for path in "$@"; do
                rlocation "${path}" || true
            done
        done
    } > /dev/null 2>&1
    lookup_end="${EPOCHREALTIME}"
    lookup_ns=$(( (${lookup_end/./} - ${lookup_start/./}) * 1000 ))

    echo "{\"init_ns\":${init_ns},\"lookup_ns\":${lookup_ns},\"iterations\":${BENCH_ITERATIONS},\"paths\":$#}"
    exit 0
fi

for path in "$@"; do
    runfile="$(rlocation "${path}")" || runfile=""
    if [[ -z "${runfile}" || ! -f "${runfile}" ]]; then
        echo "Failed to locate runfile: ${path}" >&2
        exit "${EXIT_NOT_FOUND}"
    fi
    cat "${runfile}"
done
