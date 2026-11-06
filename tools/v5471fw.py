#!/usr/bin/env python3
"""Pace V5471 (B14103) firmware image tool, ported from alacn1 updatefw.cpp.

  v5471fw.py info  fw.bin
  v5471fw.py extract fw.bin outdir        -> outdir/{header,kernel,fs.sqsh}
  v5471fw.py build src.bin fs.sqsh out.bin [-k kernel] [-m releasename]
  v5471fw.py send fw.bin [local-ip]        -> multicast RAM boot (hold WPS at power on)

Image layout: 4096-byte header, kernel partition, squashfs partition.
The squashfs in the image has byte-swapped magic ("shsq") and compression
field set to zlib although the data is LZMA (Broadcom kernel quirk);
extract restores a standard LE/lzma superblock so host unsquashfs reads it,
build applies the quirk again.
"""
import hashlib, os, struct, sys, time

HDR = 4096
PRODCODE = 0xB14103
MAGIC = bytes([0x0A, 0x20, 0x20, 0x42, 0x7C, 0x22, 0x61, 0xDB,
               0x12, 0x78, 0xB2, 0x9B, 0x27, 0xB2, 0xCE, 0x31])
OFF_BOOTSTATUS, OFF_SIZE, OFF_BOOTORDER, OFF_PROD, OFF_SVN = 0x404, 0x40c, 0x410, 0x414, 0x418
OFF_PART, PART_SZ = 0x41c, 284
OFF_CSUM = 0xff0


def u32(b, o):
    return struct.unpack_from('>I', b, o)[0]


def cstr(b):
    return b.split(b'\0', 1)[0].decode('latin-1')


def parts(h):
    out = []
    for i in range(3):
        o = OFF_PART + i * PART_SZ
        out.append((cstr(h[o:o + 64]), u32(h, o + 64), u32(h, o + 68)))
    return out


def checksum(h, body):
    h = bytearray(h)
    struct.pack_into('>I', h, OFF_BOOTORDER, 0)
    struct.pack_into('>I', h, OFF_BOOTSTATUS, 0xffffffff)
    m = hashlib.md5(bytes(h[:OFF_CSUM]))
    m.update(body)
    return bytes(a ^ b for a, b in zip(m.digest(), MAGIC))


def load(path):
    d = open(path, 'rb').read()
    h, body = d[:HDR], d[HDR:]
    if checksum(h, body) != h[OFF_CSUM:HDR]:
        sys.exit(f'{path}: checksum mismatch')
    return h, body, d


def info(path):
    h, _, d = load(path)
    print('file:       ', path)
    for name, o, n in (('copyright', 0, 80), ('platform', 0x50, 80), ('sprodcode', 0xa0, 8),
                       ('filename', 0xa8, 80), ('date', 0xf8, 24), ('releasename', 0x110, 8)):
        print(f'{name + ":":12} {cstr(h[o:o + n])}')
    print(f'prodcode:    0x{u32(h, OFF_PROD):X}  svn: {u32(h, OFF_SVN)}')
    print(f'size:        {u32(h, OFF_SIZE)} (file {len(d)})')
    for name, off, size in parts(h):
        if name or size:
            print(f'  part {name:7} off 0x{off:X} size {size}')
    print('checksum ok')


def sqsh_to_std(b):
    b = bytearray(b)
    if b[:4] == b'shsq':
        b[:4] = b'hsqs'
        struct.pack_into('<H', b, 20, 2)  # lzma
    return bytes(b)


def sqsh_to_bcm(b):
    b = bytearray(b)
    if b[:4] != b'hsqs' or struct.unpack_from('<H', b, 20)[0] not in (1, 2):
        sys.exit('fs is not a little-endian gzip/lzma squashfs')
    b[:4] = b'shsq'
    struct.pack_into('<H', b, 20, 1)
    return bytes(b)


def extract(path, outdir):
    h, _, d = load(path)
    os.makedirs(outdir, exist_ok=True)
    (kn, ko, ks), (fn, fo, fs), _ = parts(h)
    assert (kn, fn) == ('kernel', 'fs'), (kn, fn)
    open(os.path.join(outdir, 'header'), 'wb').write(h)
    open(os.path.join(outdir, 'kernel'), 'wb').write(d[ko:ko + ks])
    open(os.path.join(outdir, 'fs.sqsh'), 'wb').write(sqsh_to_std(d[fo:fo + fs]))
    print('extracted to', outdir)


def build(src, fspath, out, kernel=None, rel=None):
    h, _, d = load(src)
    if u32(h, OFF_PROD) != PRODCODE:
        sys.exit('prodcode mismatch')
    (kn, ko, ks), (fn, fo, fsz), (xn, _, xs) = parts(h)
    if (kn, fn) != ('kernel', 'fs') or xn or xs:
        sys.exit('unexpected partition table')
    k = open(kernel, 'rb').read() if kernel else d[ko:ko + ks]
    fs = sqsh_to_bcm(open(fspath, 'rb').read())
    h = bytearray(h)
    h[OFF_CSUM:HDR] = bytes(16)
    struct.pack_into('>I', h, OFF_BOOTORDER, 0)
    struct.pack_into('>I', h, OFF_BOOTSTATUS, 0xffffffff)
    h[0xf8:0xf8 + 24] = time.strftime('%Y-%m-%d-%H:%M:%S').encode().ljust(24, b'\0')
    h[0xa8:0xa8 + 80] = os.path.basename(out).encode()[:80].ljust(80, b'\0')
    if rel:
        h[0x110:0x118] = rel.encode()[:7].ljust(8, b'\0')
    o0 = OFF_PART
    struct.pack_into('>II', h, o0 + 64, HDR, len(k))
    struct.pack_into('>II', h, o0 + PART_SZ + 64, HDR + len(k), len(fs))
    struct.pack_into('>I', h, OFF_SIZE, HDR + len(k) + len(fs))
    body = k + fs
    h[OFF_CSUM:HDR] = checksum(h, body)
    if os.path.exists(out):
        sys.exit(f'{out} exists')
    open(out, 'wb').write(bytes(h) + body)
    print(f'wrote {out}: kernel {len(k)}, fs {len(fs)}, total {HDR + len(body)}')


def send(path, iface=None, passes=3):
    """Multicast RAM boot (router powered on holding WPS): boots fw without flashing."""
    import socket
    _, _, d = load(path)
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
    if iface:
        try:
            s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(iface))
        except OSError as e:
            sys.exit(f'{iface} is not an address of this machine ({e.strerror}). Use the IP of the '
                     'network adapter cabled to the V5471 (a VM needs a bridged adapter; NAT drops multicast).')
    s.connect(('239.255.255.240', 53428))
    print('from', s.getsockname()[0], 'sending', len(d), 'bytes,', passes, 'passes')
    # Several passes: the loader only listens once it prints "Entering multicast mode" and
    # collects packets by sequence number, so a pass started too early is completed by the next.
    for p in range(passes):
        for seq, off in enumerate(range(0, len(d), 1280)):
            chunk = d[off:off + 1280]
            s.send(struct.pack('>6I', seq, 0, PRODCODE, 0x80800000, len(d), len(chunk)) + chunk)
            if seq % 100 == 0:
                print('.', end='', flush=True)
            time.sleep(0.002)
        print(' pass', p + 1)
    print('done')


if __name__ == '__main__':
    a = sys.argv[1:]
    if a[:1] == ['info'] and len(a) == 2:
        info(a[1])
    elif a[:1] == ['send'] and len(a) in (2, 3):
        send(a[1], a[2] if len(a) == 3 else None)
    elif a[:1] == ['extract'] and len(a) == 3:
        extract(a[1], a[2])
    elif a[:1] == ['build'] and len(a) >= 4:
        opt = dict(zip(a[4::2], a[5::2]))
        build(a[1], a[2], a[3], opt.get('-k'), opt.get('-m'))
    else:
        sys.exit(__doc__)
