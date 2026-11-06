#!/bin/bash
# Import the router kernel into Ghidra (headless) with recovered __ksymtab names, then decompile
# the functions given as arguments.  Output: work/re/kernel.log, project in work/re/proj.
#   tools/re/kernel_ghidra.sh skb_put __alloc_skb eth_type_trans
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
G=${GHIDRA_INSTALL_DIR:-$HOME/tools/ghidra_12.1.4_PUBLIC}/support/analyzeHeadless
W=$ROOT/work/re
mkdir -p "$W/proj"
[ -f "$W/vmlinux" ] || python3 -I "$ROOT/tools/extract_kernel.py" "$ROOT/Downloads 2026-10-26/alacn1/alacn-181231-g7b2ba89.bin" "$W/vmlinux"
python3 -I "$ROOT/tools/re/ksyms.py" "$W/vmlinux" "$W/ksyms.txt"
# raw kernel: MIPS32 BE, loaded at 0x80010000 (confirmed by __ksymtab name pointers)
"$G" "$W/proj" kernel -import "$W/vmlinux" -overwrite \
	-processor MIPS:BE:32:default -loader BinaryLoader -loader-baseAddr 0x80010000 \
	-scriptPath "$ROOT/tools/re" -preScript ImportSyms.java "$W/ksyms.txt" \
	-postScript Decomp.java "$@" -analysisTimeoutPerFile 3000 > "$W/kernel.log" 2>&1
sed -n 's/^INFO  Decomp.java> //p; /^=== /p' "$W/kernel.log"
