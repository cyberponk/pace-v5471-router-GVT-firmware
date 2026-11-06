import sys, lzma, re
d = open(sys.argv[1],'rb').read()
region = d[0x1000:0x1000+0x300000]
found = False
for m in re.finditer(rb'\x5d\x00\x00', region):
    off = m.start()
    try:
        dec = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE)
        out = dec.decompress(region[off:])
    except Exception:
        try:
            # broadcom style: props(1)+dict(4) without 8-byte size
            hdr = region[off:off+5] + b'\xff'*8
            out = lzma.LZMADecompressor(format=lzma.FORMAT_ALONE).decompress(hdr + region[off+5:])
        except Exception:
            continue
    if len(out) > 1_000_000:
        print("lzma at", hex(0x1000+off), "size", len(out)); found = True
        open(sys.argv[2],'wb').write(out); break
if not found: print("none")
