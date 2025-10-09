#!/bin/bash
# A small binary for accessing runfiles

# {RUNFILES_API}

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 <runfile_path>" >&2
    echo "Example: $0 workspace/path/to/file.txt" >&2
    exit 1
fi

RLOCATIONPATH="$1"

RUNFILE="$(rlocation "${RLOCATIONPATH}")"

if [[ -z "${RUNFILE}" ]]; then
    echo "Failed to locate runfile: ${RLOCATIONPATH}" >&2
    exit 1
fi

echo "$(<${RUNFILE})"
