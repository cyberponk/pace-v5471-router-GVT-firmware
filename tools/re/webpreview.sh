#!/bin/bash
# Live preview of the web UI from work/rootfs on the running router, without flashing:
# copies etc/bewan/iad (login blocks stripped) to the router's /var/www, serves it with a second
# lighttpd on :8088 (the ssi CGI fills cli=/include data without login), and screenshots pages.
#   tools/re/webpreview.sh push            # after tools/make_rootfs.sh
#   tools/re/webpreview.sh shot page.htm [lang] [height]   -> work/re/preview/shots/<lang>_<page>.png
# Needs: the serial logger running, this PC on the router LAN (ROUTER/PC below), snap Firefox.
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../.." && pwd)
P=$ROOT/work/re/preview
ROUTER=${ROUTER:-192.168.25.1}
PC=${PC:-$(ip -4 -o addr show | awk '/192\.168\.25\./ {sub("/.*","",$4); print $4; exit}')}
SHOTS=$P/shots
FF=$HOME/snap/firefox/common/preview   # snap Firefox can't use a profile under /tmp

case "${1:-}" in
push)
	rm -rf "$P/www" && mkdir -p "$P/www" "$SHOTS"
	cp -a "$ROOT/work/rootfs/etc/bewan/iad/." "$P/www/"
	chmod -R u+w "$P/www"
	python3 -I - "$P/www" <<'EOF'
import os, re, sys
for d, _, files in os.walk(sys.argv[1]):
    for f in files:
        p = os.path.join(d, f)
        if os.path.islink(p) or not f.endswith('.htm'):
            continue
        t = open(p, encoding='utf-8', errors='surrogateescape').read()
        # drop the not-logged-in branch (auth form) and the auth markers
        t = re.sub(r'<!--#isNotAuth[^>]*-->.*?(?=<!--#isAuth)', '', t, flags=re.S)
        t = re.sub(r'<!--#(isAuth|endAuth)[^>]*-->', '', t)
        # tokens need a login: a dummy one lets the page scripts initialise (saving won't work)
        t = re.sub(r'<!--#echo jsonvar="token=[^"]*"-->', '{"t":0}', t)
        open(p, 'w', encoding='utf-8', errors='surrogateescape').write(t)
EOF
	# preview only: tabs are revealed by an animation after load, too late for the screenshot
	printf '\n/* preview */ .tab{ display:block !important; height:auto !important; overflow:visible !important; } *, *:after, *:before { transition:none !important; }\n' >> "$P/www/css/gateway.css"
	(cd "$P" && tar -cf www.tar -C www .)
	# one-shot HTTP server for the router to fetch the tarball
	(cd "$P" && timeout 60 python3 -I -m http.server 8005 --bind "$PC" >/dev/null 2>&1 &)
	sleep 1
	"$ROOT/tools/re/serial_cmd.sh" "kill \$(cat /var/run/http-T.pid 2>/dev/null) 2>/dev/null; rm -rf /var/www; mkdir -p /var/www && cd /var/www && wget -q -O - http://$PC:8005/www.tar | tar -xf - && rm -f ssi && ln -s /etc/bewan/iad/cgi-ssi ssi && sed -e 's#/etc/bewan/iad#/var/www#g' -e 's#port = 80#port = 8088#' -e 's#fcgi.sock#fcgiT.sock#g' -e 's#http-1.pid#http-T.pid#' -e '/include_shell/d' /var/bewan/lighty/lighttpd.conf_1 > /var/t.conf && /sbin/lighttpd -f /var/t.conf -m /lib; echo push-rc=\$?; cd /" 15
	;;
shot)
	page=$2; lang=${3:-pt_BR}; h=${4:-1400}
	# one profile (its session cookie is reused: every new web session counts against the ssi
	# CGI's session limit, shared with the real web UI) with the cache off (no stale CSS)
	mkdir -p "$FF/prof" "$SHOTS"
	printf '%s\n' 'user_pref("browser.cache.disk.enable", false);' 'user_pref("browser.cache.memory.enable", false);' > "$FF/prof/user.js"
	# each Firefox run opens a new web session; remove the ones this shot created afterwards
	"$ROOT/tools/re/serial_cmd.sh" 'ls /var/bewan/session > /tmp/sess.before' 2 >/dev/null
	timeout 90 firefox --headless --no-remote --profile "$FF/prof" --window-size="1400,$h" \
		--screenshot "$FF/shot.png" "http://$ROUTER:8088/$lang/admin/$page" >/dev/null 2>&1
	"$ROOT/tools/re/serial_cmd.sh" 'for f in $(ls /var/bewan/session); do grep -qx $f /tmp/sess.before || rm -f /var/bewan/session/$f; done' 2 >/dev/null
	mv "$FF/shot.png" "$SHOTS/${lang}_${page%.htm}.png"
	echo "$SHOTS/${lang}_${page%.htm}.png"
	;;
*)
	sed -n '2,7p' "$0"; exit 1 ;;
esac
