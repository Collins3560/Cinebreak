#!/usr/bin/env bash
# Cinebreak build - one command. Requires the BD-J SDK cloned as ./bdj-sdk
set -e
SDK="${BDJSDK_HOME:-$HOME/ps5dev/bdj-sdk}"
JB="$(pwd)"
[ -x "$SDK/host/bin/makefs" ] || { echo "makefs missing - build the SDK host tools first (see README)"; exit 1; }
make -C "$JB" clean >/dev/null 2>&1 || true
make -C "$JB" BDJSDK_HOME="$SDK"
echo "=== BUILD COMPLETE ==="
ls -la "$JB"/BD-JB5-2.0.iso
