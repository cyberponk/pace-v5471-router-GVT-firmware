#!/bin/bash
# Recreate work/rootfs from the alacn-181231 image and apply the lean-AP changes.
#   tools/make_rootfs.sh && tools/build.sh work/build/<name>.bin
# No root needed: ownership/device nodes live in the fakeroot state work/rootfs.fakeroot.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
W=$ROOT/work
SRC="$ROOT/Downloads 2026-10-26/alacn1/alacn-181231-g7b2ba89.bin"
FR="$W/rootfs.fakeroot"

rm -rf "$W/rootfs" "$W/src"
rm -f "$FR"
python3 -I "$ROOT/tools/v5471fw.py" extract "$SRC" "$W/src"
fakeroot -s "$FR" -- unsquashfs -q -no-progress -d "$W/rootfs" "$W/src/fs.sqsh" >/dev/null
# fakeroot turns the FIFO into a regular file; recreate it
fakeroot -i "$FR" -s "$FR" -- sh -c "rm '$W/rootfs/dev/initctl' && mkfifo -m 664 '$W/rootfs/dev/initctl'"
fakeroot -i "$FR" -s "$FR" -- "$ROOT/tools/strip.sh"
fakeroot -i "$FR" -s "$FR" -- python3 -I "$ROOT/tools/configure.py"
du -sh "$W/rootfs"
