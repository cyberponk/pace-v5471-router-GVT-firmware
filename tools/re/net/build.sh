#!/bin/bash
# Static network daemons for the router (musl toolchain, like tools/re/curl/build.sh):
#   dnsmasq 2.93      replaces the stock 2.45 (2008) DNS forwarder / DHCP server
#   dropbear 2026.94  replaces the stock 0.52 SSH server (DSS host key shared by every unit);
#                     multi binary: dropbear + dropbearkey (per-device ed25519 host key)
#   dotproxy          DNS over TLS forwarder (tools/re/dot/dotproxy.c), mbedTLS from the curl build
#   tools/re/net/build.sh   -> work/re/net/out/{dnsmasq,dropbearmulti,dotproxy}
# Sources (checked): work/re/dnsmasq/src/dnsmasq-2.93.tar.xz (GPG, Simon Kelley
# D6EACBD6EE46B834248D111215CDDA6AE19135A2), work/re/dropbear/src/dropbear-2026.94.tar.bz2 (GPG,
# Matt Johnston F7347EF2EE2E07A267628CA944931494F29C6773). Needs tools/re/curl/build.sh first (mbedTLS).
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
W=$ROOT/work/re/net
TC=$ROOT/work/toolchain/mips32--musl--stable-2018.02-2/bin
MBEDP=$ROOT/work/re/curl/build/prefix
DNSMASQ=dnsmasq-2.93
DROPBEAR=dropbear-2026.94
DNSMASQ_SHA=0c00d4e5c97c8306e5fb932b348b34269c9c29a0e7df0e8e82958b407092bc19
DROPBEAR_SHA=e098034a843699200c8c977a991fff73159735bf795d5f72ef672c41a6b1ae81
mkdir -p "$W/out"
exec > >(tee "$W/build.log") 2>&1

echo "$DNSMASQ_SHA  $ROOT/work/re/dnsmasq/src/$DNSMASQ.tar.xz" | sha256sum -c
echo "$DROPBEAR_SHA  $ROOT/work/re/dropbear/src/$DROPBEAR.tar.bz2" | sha256sum -c
test -f "$MBEDP/lib/libmbedtls.a"
rm -rf "$W/build" && mkdir -p "$W/build"
cd "$W/build"
tar -xJf "$ROOT/work/re/dnsmasq/src/$DNSMASQ.tar.xz"
tar -xjf "$ROOT/work/re/dropbear/src/$DROPBEAR.tar.bz2"
export PATH=$TC:$PATH

echo "== dnsmasq"
make -C $DNSMASQ -j"$(nproc)" CC=mips-linux-gcc CFLAGS="-Os -Wall" LDFLAGS="-static" \
	COPTS="-DNO_TFTP -DNO_AUTH -DNO_DUMPFILE -DNO_IPSET -DNO_LOOP -DNO_INOTIFY"
mips-linux-strip -o "$W/out/dnsmasq" $DNSMASQ/src/dnsmasq

echo "== dropbear"
cd $DROPBEAR
cat > localoptions.h <<'EOF'
/* cyberponk: LAN-only admin shell, password or public key login, no forwarding */
#define DROPBEAR_X11FWD 0
#define DROPBEAR_SVR_AGENTFWD 0
#define DROPBEAR_SVR_LOCALTCPFWD 0
#define DROPBEAR_SVR_REMOTETCPFWD 0
#define DROPBEAR_SFTPSERVER 0
#define DROPBEAR_DSS 0
#define DROPBEAR_ECDSA 0
#define DROPBEAR_ED25519 1
#define DROPBEAR_RSA 1
#define DROPBEAR_ENABLE_CBC_MODE 0
#define DEFAULT_PATH "/usr/bin:/bin:/usr/sbin:/sbin"
#define ED25519_PRIV_FILENAME "/var/bewan/ssh/dropbear_ed25519_host_key"
#define RSA_PRIV_FILENAME "/var/bewan/ssh/dropbear_rsa_host_key"
EOF
./configure --host=mips-linux --enable-static --disable-zlib --disable-harden --disable-lastlog \
	--disable-utmp --disable-utmpx --disable-wtmp --disable-wtmpx --disable-pututline --disable-pututxline \
	CC=mips-linux-gcc CFLAGS="-Os"
make -j"$(nproc)" PROGRAMS="dropbear dropbearkey" MULTI=1 STATIC=1
mips-linux-strip -o "$W/out/dropbearmulti" dropbearmulti
cd "$W/build"

echo "== dotproxy"
mips-linux-gcc -Os -Wall -static -DBUILD_EPOCH="$(date +%s)" -I"$MBEDP/include" \
	-o dotproxy "$ROOT/tools/re/dot/dotproxy.c" -L"$MBEDP/lib" -lmbedtls -lmbedx509 -lmbedcrypto
mips-linux-strip -o "$W/out/dotproxy" dotproxy

file "$W/out/"*
ls -l "$W/out"
