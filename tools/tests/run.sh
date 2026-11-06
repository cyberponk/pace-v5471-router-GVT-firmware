#!/bin/bash
# Offline checks on work/rootfs (after tools/make_rootfs.sh):
# page logic of the cyberponk pages (mock DOM, both languages), script syntax of edited pages,
# shared-library dependencies of every ELF.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
R=$ROOT/work/rootfs
IAD=$R/etc/bewan/iad
T=$(mktemp -d)
trap 'rm -rf "$T"' EXIT

for l in en_US pt_BR; do
	node "$ROOT/tools/tests/test_pages.js" "$IAD/$l/admin"
done

for f in "$IAD"/*/admin/{config_advanced,services_status,config_usb,changelog,config_ap,config_3g,config_internet,config_ddns,config_lan,config_wireless,admin_password,auth,config_ntp,logread}.htm \
	"$IAD"/*/js/{menu.js,config_wireless.javascript,admin_password.javascript,logread.javascript}; do
	python3 -I - "$f" "$T/chk.js" <<'E'
import re, sys
s = open(sys.argv[1], encoding='utf-8', errors='replace').read()
s = re.sub(r'<!--#echo jsonvar="[^"]*"-->', '"x"', s)
s = re.sub(r'<!--#[^>]*-->', '', s)
js = s if sys.argv[1].endswith(('.js', '.javascript')) else '\n;\n'.join(re.findall(r'<script type="text/javascript">(.*?)</script>', s, re.S))
open(sys.argv[2], 'w').write(js)
E
	node --check "$T/chk.js" || { echo "syntax error in $f"; exit 1; }
done
# overlay shell scripts (busybox ash on the router; dash -n catches the same syntax errors)
for f in $(grep -rlE '^#!/bin/(ash|sh)' "$ROOT/tools/overlay"); do
	dash -n "$f" || { echo "shell syntax error in $f"; exit 1; }
done
# commands this busybox lacks: in /bin/sh (patched dash) "not found" stops the softdog = reboot
missing=''
for c in tee cmp readlink base64 timeout seq xargs sha256sum uniq od mktemp flock nproc; do
	[ -e "$R/bin/$c" ] || [ -e "$R/usr/bin/$c" ] || [ -e "$R/sbin/$c" ] || [ -e "$R/usr/sbin/$c" ] || missing="$missing|$c"
done
if [ -n "$missing" ]; then
	re="(^|[|;&(]|\\\$\\(|then|do|else|&&|\\|\\|)[[:space:]]*(${missing#|})([[:space:]]|$)"
	bad=$(grep -rlE "$re" "$ROOT/tools/overlay" $R/etc/bewan/init.d/{ntp,inetd,dnsmasq,lan,users} $R/etc/bewan/lib/{dhcpclient,wifi,dyndns} $R/etc/bewan/user.d/diag 2>/dev/null | grep -v '/iad/' || true)
	if [ -n "$bad" ]; then
		grep -nE "$re" $bad | head
		echo "scripts call commands the firmware does not have"; exit 1
	fi
fi
echo "script syntax ok"

libs=$(cd "$R" && ls lib lib/private lib/public lib/gpl usr/lib 2>/dev/null | grep '\.so' || true)
missing=0
while IFS= read -r f; do
	head -c4 "$f" | grep -q ELF || continue
	for n in $(readelf -d "$f" 2>/dev/null | sed -n 's/.*NEEDED.*\[\(.*\)\]/\1/p'); do
		# here-string, not a pipe: with pipefail, `echo | grep -q` fails at random when grep exits
		# on the first match before echo is done writing (SIGPIPE)
		grep -qxF "$n" <<< "$libs" || { echo "MISSING $n <- ${f#$R/}"; missing=1; }
	done
done < <(find "$R" -path "$R/dev" -prune -o -type f -print)
[ $missing = 0 ] && echo "library dependencies ok"
exit $missing
