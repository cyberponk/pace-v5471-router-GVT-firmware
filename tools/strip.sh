#!/bin/bash
# Lean AP: remove DSL, VoIP, HPNA, TR-069 daemon, USB storage/DLNA,
# GVT hotspot/STB/lynx and the diag chroot from work/rootfs.
# Run via:  fakeroot -i work/rootfs.fakeroot -s work/rootfs.fakeroot -- tools/strip.sh
#
# init.d scripts are replaced with no-op stubs instead of being deleted:
# configd runs onchange handlers as ". /etc/bewan/init.d/<svc>", and sourcing
# a missing file aborts that shell before onchange-unlock releases the mutex.
set -euo pipefail
R=$(cd "$(dirname "$0")/.." && pwd)/work/rootfs
cd "$R"
B=etc/bewan
M=lib/modules/2.6.30/extra

STUBS=(
	dsl voip hpna hpna_statusd tr069 tr069_cr gvthotspot gvt-tr069-usb
	samba superdlna.init lynx.init manage_storage mountpoint
)

RM=(
	# DSL
	$M/adsldd.ko $M/adsl_stats.ko $M/adsl_stats_hal.ko etc/adsl
	bin/xdslctl bin/adsl bin/adslctl bin/dsldiagd
	$B/rc.d/S04dslrelay $B/rc.d/S05dsl
	# VoIP
	$M/endpointdd.ko usr/bin/voip lib/libsofia-sip-ua.so lib/libsofia-sip-ua.so.0 lib/libsofia-sip-ua.so.0.6.0
	$B/rc2.d/S50voip $B/ip-up.d/S70-voip $B/ip-up-lan.d/S70-voip
	$B/ip-down.d/K01-voip $B/ip-down-lan.d/K01-voip $B/reboot.d/reboot.voip
	# HPNA (coax)
	bin/hpna_address bin/hpna_devinf bin/hpna_getimage bin/hpna_loadfw bin/hpna_netinf
	bin/hpna_netper bin/hpna_prog bin/hpna_stats usr/bin/hpna_statusd $B/coppergate
	$B/rc.d/S05-fap-hpna-tmii $B/rc2.d/S90hpna
	# TR-069 daemon (data-model plugins and libtr069api stay, configd/web may load them)
	bin/tr069 bin/tr143diag $B/rc.d/S60tr069 $B/ip-up.d/S99tr069
	# USB storage / DLNA (USB host, printer and 3G modem stay)
	bin/smbd bin/nmbd bin/ntfs-3g lib/libntfs-3g.so lib/libntfs-3g.so.80 lib/libntfs-3g.so.80.0.0
	bin/superdlna usr/share/superdlna lib/libsqlite3.so lib/libsqlite3.so.0 lib/libsqlite3.so.0.8.6
	bin/fusermount sbin/mount.fuse lib/libfuse.so lib/libfuse.so.2 lib/libfuse.so.2.7.5
	usr/bin/storaged usr/bin/storage_sched usr/bin/storage_update_share_samba
	$B/mdev/50-storage $B/rc.d/S99-storaged
	$B/rc2.d/S01-fuse $B/rc2.d/S50samba $B/rc2.d/S91superdlna
	$B/ip-up-lan.d/S50samba $B/ip-up-lan.d/S91superdlna $B/ip-down-lan.d/S91superdlna
	$B/storage.d/S11superdlna $B/storage.d/S50samba
	$B/factory.d/S70superdlna
	# GVT: lynx STB detection, STB DHCP block, hotspot (stopssid blanks SSID 2 when WAN is down)
	bin/lynx lib/libsdlna.so $B/rc2.d/S93lynx $B/ip-up-lan.d/S62lynx $B/ip-down-lan.d/S62lynx
	$B/rc.d/S41-gvtSTB $B/rc2.d/S99-hotspot $B/ip-up.d/S98-gvthotspot $B/ip-down.d/K08-gvthotspot
	# L2TP
	$B/rc2.d/S05l2tp
	# diag chroot shell (uid 0 "admin" login)
	home/diag $B/rc.d/S99-box-diagnostic
)

for s in "${STUBS[@]}"; do
	f=$B/init.d/$s
	[ -f "$f" ] || { echo "missing init.d/$s" >&2; exit 1; }
	printf '#!/bin/sh\n# %s: removed in lean AP build\n' "$s" > "$f"
done

for p in "${RM[@]}"; do
	if [ -e "$p" ] || [ -L "$p" ]; then
		rm -rf -- "$p"
	else
		echo "already gone: $p"
	fi
done

# dangling symlinks left behind
# (absolute targets are resolved inside the rootfs, not on the host)
find . -path ./dev -prune -o -type l -print | while read -r l; do
	t=$(readlink "$l")
	case "$t" in
	/var/*|/tmp/*|/proc/*|/dev/*|/nvram/*) continue ;;
	/*) p=.$t ;;
	*) p=$(dirname "$l")/$t ;;
	esac
	[ -e "$p" ] || [ -L "$p" ] || echo "dangling: $l -> $t"
done
echo "strip done"
