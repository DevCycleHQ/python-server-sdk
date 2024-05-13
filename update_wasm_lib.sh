#!/bin/bash

BUCKETING_LIB_VERSION="1.20.1"

if [[ -n "$1" ]]; then
  BUCKETING_LIB_VERSION="$1"
fi

cd devcycle_python_sdk
rm bucketing-lib.release.wasm
echo "Downloading bucketing lib version $BUCKETING_LIB_VERSION"
wget "https://unpkg.com/@devcycle/bucketing-assembly-script@$BUCKETING_LIB_VERSION/build/bucketing-lib.release.wasm"
