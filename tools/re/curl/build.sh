#!/bin/bash
# Static curl (HTTP/HTTPS only, mbedTLS 3.6: TLS 1.2 and 1.3) for the router, used by the dynamic DNS updates:
# the firmware's own OpenSSL is 1.0.0a (TLS 1.0 only) and it has no curl program.
# musl toolchain: the Bootlin glibc one makes binaries that need kernel >= 4.1 (router: 2.6.30).
#   tools/re/curl/build.sh   -> work/re/curl/out/{curl,ca-certificates.crt}
# Sources (checked): work/re/curl/src/curl-8.10.1.tar.xz (GPG, Daniel Stenberg 27EDEAF22F3ABCEB50DB9A125CC908FDB71E12C2),
# mbedtls-3.6.2.tar.bz2 (sha256 from the release notes). TLS 1.3 is needed: nsupdate.info
# gives nothing over TLS 1.2.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
W=$ROOT/work/re/curl
TC=$ROOT/work/toolchain/mips32--musl--stable-2018.02-2/bin
CURL=curl-8.10.1
MBED=mbedtls-3.6.2
MBED_SHA=8b54fb9bcf4d5a7078028e0520acddefb7900b3e66fec7f7175bb5b7d85ccdca
CURL_SHA=73a4b0e99596a09fa5924a4fb7e4b995a85fda0d18a2c02ab9cf134bebce04ee
LOG=$W/build.log
mkdir -p "$W/out"
exec > >(tee "$LOG") 2>&1

echo "$MBED_SHA  $W/src/$MBED.tar.bz2" | sha256sum -c
echo "$CURL_SHA  $W/src/$CURL.tar.xz" | sha256sum -c
rm -rf "$W/build" && mkdir -p "$W/build" "$W/build/prefix"
cd "$W/build"
tar -xjf "$W/src/$MBED.tar.bz2"
tar -xJf "$W/src/$CURL.tar.xz"
export PATH=$TC:$PATH
P=$W/build/prefix

echo "== mbedtls"
make -C $MBED/library -j"$(nproc)" CC=mips-linux-gcc AR=mips-linux-ar CFLAGS="-Os -I../include -D_FILE_OFFSET_BITS=64" \
	libmbedtls.a libmbedx509.a libmbedcrypto.a
mkdir -p $P/lib $P/include
cp $MBED/library/*.a $P/lib/
cp -r $MBED/include/mbedtls $MBED/include/psa $P/include/

echo "== curl"
cd $CURL
./configure --host=mips-linux --prefix=/usr --disable-shared --enable-static \
	--with-mbedtls=$P --without-zlib --without-brotli --without-zstd --without-libpsl --without-libidn2 \
	--without-nghttp2 --without-libssh2 --disable-ldap --disable-ldaps --disable-rtsp --disable-dict \
	--disable-telnet --disable-tftp --disable-pop3 --disable-imap --disable-smb --disable-smtp \
	--disable-gopher --disable-mqtt --disable-ftp --disable-file --disable-manual \
	--disable-ntlm --disable-unix-sockets --enable-ipv6 \
	--with-ca-bundle=/etc/ssl/certs/ca-certificates.crt --with-ca-path=no \
	CC=mips-linux-gcc CFLAGS="-Os" CPPFLAGS="-I$P/include" LDFLAGS="-static -L$P/lib" LIBS="-lmbedtls -lmbedx509 -lmbedcrypto"
make -j"$(nproc)" LDFLAGS="-static -all-static -L$P/lib"
mips-linux-strip -o "$W/out/curl" src/curl
cd "$W"

echo "== CA bundle (Mozilla, via curl.se)"
if [ ! -f "$W/src/cacert.pem" ]; then
	curl -sSL -o "$W/src/cacert.pem" https://curl.se/ca/cacert.pem
	curl -sSL -o "$W/src/cacert.pem.sha256" https://curl.se/ca/cacert.pem.sha256
fi
(cd "$W/src" && sha256sum -c cacert.pem.sha256)
cp "$W/src/cacert.pem" "$W/out/ca-certificates.crt"

file "$W/out/curl"
ls -l "$W/out"
