#!/bin/bash
set -euo pipefail
IFS=$'\n\t'

tmp="$(mktemp --tmpdir --directory hash-cache-venv.XXXXXXXXXX)"
trap "rm -rf ${tmp}" EXIT

target="${tmp}/hash-cache-venv"
output="${target}.pyz"

python3.8 -m pip install \
  --target=${target} \
  --no-compile \
  --implementation=py \
  --only-binary :all: \
  --require-hashes \
  --no-deps \
  --requirement ./requirements-zipapp.txt

python3.8 -m zipapp \
  ${target} \
  --output=${output} \
  --compress \
  --main=hash_cache_venv:main \
  --python='/usr/bin/env python'

strip-nondeterminism -t zip -v ${output}
mv ${output} .
