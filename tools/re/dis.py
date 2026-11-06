# Disassemble a function range of a MIPS BE ELF: python3 -I dis.py <elf> <hexaddr> <size>
import sys, subprocess, capstone
path, start, size = sys.argv[1], int(sys.argv[2], 16), int(sys.argv[3])
d = open(path, 'rb').read()
# map vaddr -> file offset via PT_LOAD segments (readelf)
segs = []
for l in subprocess.run(['readelf', '-lW', path], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if p and p[0] == 'LOAD':
        segs.append((int(p[2], 16), int(p[1], 16), int(p[4], 16)))
def off(va):
    for v, o, s in segs:
        if v <= va < v + s: return o + va - v
# symbols for call targets
syms = {}
for l in subprocess.run(['readelf', '-sW', path], capture_output=True, text=True).stdout.splitlines():
    p = l.split()
    if len(p) >= 8 and p[3] in ('FUNC', 'OBJECT') and p[1] != '00000000':
        syms[int(p[1], 16)] = p[7]
md = capstone.Cs(capstone.CS_ARCH_MIPS, capstone.CS_MODE_MIPS32 | capstone.CS_MODE_BIG_ENDIAN)
o = off(start)
for i in md.disasm(d[o:o + size], start):
    print(f'{i.address:08x}  {i.mnemonic:8} {i.op_str}')
