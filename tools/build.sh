#!/bin/bash
# Build a V5471 image from work/rootfs (fakeroot state in work/rootfs.fakeroot).
#   tools/build.sh [out.bin] [releasename]
# Default out: work/build/cyberponk-v<VERSION>.bin, releasename cyberpk (header field, 7 chars max).
# Kernel + header template come from the alacn-181231 image.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
W=$ROOT/work
SRC="$ROOT/Downloads 2026-10-26/alacn1/alacn-181231-g7b2ba89.bin"
VERSION=$(cat "$ROOT/VERSION")
OUT=${1:-$W/build/cyberponk-v$VERSION.bin}
REL=${2:-cyberpk}
FS=$W/build/$(basename "$OUT" .bin).sqsh

grep -qx "cyberponk-v$VERSION" "$W/rootfs/etc/bewan/release" ||
	echo "WARNING: rootfs release is '$(cat "$W/rootfs/etc/bewan/release")', VERSION is $VERSION (rerun tools/make_rootfs.sh)" >&2

mkdir -p "$W/build"
rm -f "$FS"
fakeroot -i "$W/rootfs.fakeroot" -- \
	mksquashfs "$W/rootfs" "$FS" -comp lzma -b 65536 -all-root -noappend -quiet -no-progress
python3 -I "$ROOT/tools/v5471fw.py" build "$SRC" "$FS" "$OUT" -m "$REL"
rm -f "$FS"
python3 -I "$ROOT/tools/v5471fw.py" info "$OUT"
sha1sum "$OUT"
