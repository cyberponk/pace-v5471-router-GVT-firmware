#!/bin/bash
# Compile probe.c against a candidate kernel tree with config.h; print "name value" lines and
# compare them with fingerprint.txt (offsets measured in the router kernel).
#   tools/re/probe/probe.sh work/ref/nomis
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
P=$ROOT/tools/re/probe
TREE=$(cd "${1:?candidate tree}" && pwd)
K=$TREE/kernel/linux
CC=$ROOT/work/toolchain/mips32--glibc--stable-2018.02-2/bin/mips-linux-gcc
T=$ROOT/work/re/probe; mkdir -p "$T/gen/linux"
# kbuild-generated headers the struct definitions need
printf '#define NR_PAGEFLAGS 22\n#define MAX_NR_ZONES 3\n' > "$T/gen/linux/bounds.h"
# PROBE_AUTOCONF=<tree>/include/linux/autoconf.h checks a real build's generated config
# instead of the hand-written probe config
cp "${PROBE_AUTOCONF:-$P/config.h}" "$T/gen/linux/autoconf.h"
echo '#define UTS_RELEASE "2.6.30"' > "$T/gen/linux/utsrelease.h"
# 2.6.30 only ships compiler-gcc3/4.h; gcc 6 uses the gcc4 definitions
echo '#include <linux/compiler-gcc4.h>' > "$T/gen/linux/compiler-gcc6.h"
$CC -S -o "$T/probe.s" -O2 -nostdinc -isystem "$($CC -print-file-name=include)" \
	-D__KERNEL__ -DMODULE -DKBUILD_MODNAME='"probe"' -DKBUILD_BASENAME='"probe"' -include "$T/gen/linux/autoconf.h" -I"$T/gen" \
	-I"$K/include" -I"$K/arch/mips/include" -I"$K/arch/mips/include/asm/mach-bcm963xx" \
	-I"$K/arch/mips/include/asm/mach-generic" \
	-I"$TREE/shared/opensource/include/bcm963xx" -I"$TREE/bcmdrivers/opensource/include/bcm963xx" \
	-mabi=32 -march=mips32 -EB -G 0 -mno-abicalls -fno-pic -msoft-float \
	-Wno-error -w "$P/probe.c"
python3 -I - "$T/probe.s" "$P/fingerprint.txt" <<'PY'
import re, sys
s = open(sys.argv[1]).read()
got = {}
for name, val in re.findall(r"\n(o__\w+|z__\w+):\n\s+\.(?:word\s+(-?\d+)|space\s+4)", s):
    got[name] = int(val) if val else 0
bad = 0
want_names = set()
for line in open(sys.argv[2]):
    line = line.split('#')[0].split()
    if len(line) != 2: continue
    name, want = line[0], int(line[1], 0)
    want_names.add(name)
    have = got.get(name)
    ok = have == want
    bad += not ok
    print(f'{"ok " if ok else "BAD"} {name:42} want {want:#06x} have {have if have is None else hex(have)}')
print(f'{len(got)} probed, {bad} mismatches')
for n in sorted(got):
    if n.startswith(('z__urb', 'z__usb', 'o__urb', 'o__net_device__')) and n not in want_names: print('   info', n, hex(got[n]))
sys.exit(1 if bad else 0)
PY
