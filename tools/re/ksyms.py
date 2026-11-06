# Recover exported symbols from the raw router kernel: python3 -I ksyms.py vmlinux out.txt
# Recover exported symbols (__ksymtab: {value, name_ptr} BE pairs) from a raw MIPS BE kernel.
import sys, struct, re
d = open(sys.argv[1], 'rb').read(); BASE = 0x80010000; END = BASE + len(d)
def s_at(va):
    o = va - BASE
    if not (0 <= o < len(d)): return None
    e = d.find(b'\0', o, o + 128)
    if e <= o: return None
    s = d[o:e]
    return s.decode() if re.fullmatch(rb'[A-Za-z_][A-Za-z0-9_.$]*', s) else None
syms = {}
for o in range(0, len(d) - 8, 4):
    v, n = struct.unpack_from('>II', d, o)
    if BASE <= v < END and BASE <= n < END and v != n:
        s = s_at(n)
        if s and (o == 0 or True):
            syms.setdefault(o, (v, s))
# keep only long runs of consecutive pairs (real tables), not random matches
offs = sorted(syms); runs = []; cur = []
for o in offs:
    if cur and o != cur[-1] + 8: runs.append(cur); cur = []
    cur.append(o)
runs.append(cur)
tab = [syms[o] for r in runs if len(r) >= 50 for o in r]
print('tables', [(hex(BASE + r[0]), len(r)) for r in runs if len(r) >= 50], 'symbols', len(tab), file=sys.stderr)
with open(sys.argv[2], 'w') as f:
    for v, s in sorted(set(tab)):
        f.write(f'{s} {v:08x}\n')
