#!/bin/bash
# Continue the build from the current work/ref/nomis/kernel/linux/.config (already answered
# through oldconfig in a previous run — does NOT run allnoconfig, so it won't throw that away).
# Use this after fixing a config/Kconfig issue by hand; use build.sh instead for a from-scratch
# run. See BUILD_PLAN.md.
#
#   tools/re/modules/continue.sh
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
LOG=$ROOT/work/re/modules/continue.log
mkdir -p "$(dirname "$LOG")"
# full output also goes to $LOG, so it can be read back without copy-pasting
exec > >(tee "$LOG") 2>&1
TREE=$ROOT/work/ref/nomis/kernel/linux
TC=$ROOT/work/toolchain/mips32--glibc--stable-2018.02-2/bin
WANT_VERMAGIC='2.6.30 SMP preempt mod_unload MIPS32_R1 32BIT '

[ -f "$TREE/.config" ] || { echo "ERROR: $TREE/.config missing — run build.sh first"; exit 1; }

export ARCH=mips
export CROSS_COMPILE=$TC/mips-linux-
cd "$TREE"

echo "== oldconfig (re-resolving after the .config/Kconfig edit) =="
set +o pipefail  # yes dies of SIGPIPE once oldconfig stops reading input; harmless
yes "" | make oldconfig
set -o pipefail

echo
echo "== checking the USB chain actually came out enabled =="
missing=0
# USB_SUPPORT/USB: built-in (=y) is fine, usbcore's exports work the same either way.
# USB_USBNET/RNDIS_HOST/CDCETHER: must be =m — `make M=... modules` only produces a .ko
# for symbols set to module; =y (built-in) compiles fine but yields nothing loadable.
for spec in CONFIG_USB_SUPPORT=y CONFIG_USB=y CONFIG_USB_USBNET=m CONFIG_USB_NET_RNDIS_HOST=m CONFIG_USB_NET_CDCETHER=m; do
	sym=${spec%%=*}
	if grep -q "^${spec}$" .config; then
		echo "OK   $spec"
	else
		echo "MISSING: $spec (check .config — it may be \"# $sym is not set\", or set to the"
		echo "         other of y/m, meaning some dependency in the chain still isn't satisfied)"
		missing=1
	fi
done
if [ $missing -ne 0 ]; then
	echo
	echo "Stopping here — fix the .config/Kconfig gap above before building, same as the"
	echo "CONFIG_USB_ARCH_HAS_OHCI/EHCI and CONFIG_USB_SUPPORT issues earlier."
	exit 1
fi

echo
echo "== modules_prepare =="
make modules_prepare

echo
echo "== struct layout gate: this build's own config vs the router fingerprint =="
PROBE_AUTOCONF="$TREE/include/linux/autoconf.h" "$ROOT/tools/re/probe/probe.sh" "$ROOT/work/ref/nomis" > "$ROOT/work/re/modules/probe-gate.log" 2>&1 || {
	grep -E "BAD|error|probed" "$ROOT/work/re/modules/probe-gate.log"
	echo "STOP: struct layouts differ from the router — not building modules."
	exit 1
}
grep probed "$ROOT/work/re/modules/probe-gate.log"

echo
echo "== building drivers/net/usb =="
make M=drivers/net/usb modules
# generic MII library: the router kernel has no mii_* exports and usbnet needs them
make drivers/net/mii.ko

echo
echo "== vermagic check (must read exactly: $WANT_VERMAGIC) =="
status=0
for m in drivers/net/mii.ko drivers/net/usb/usbnet.ko drivers/net/usb/rndis_host.ko drivers/net/usb/cdc_ether.ko; do
	if [ ! -f "$m" ]; then
		echo "MISSING: $m"
		status=1
		continue
	fi
	got=$(strings "$m" | grep '^vermagic=' | sed 's/^vermagic=//')
	if [ "$got" = "$WANT_VERMAGIC" ]; then
		echo "OK   $m"
	else
		echo "BAD  $m  (got: '$got')"
		status=1
	fi
done

echo
if [ $status -eq 0 ]; then
	mkdir -p "$ROOT/work/re/modules/out"
	cp drivers/net/mii.ko drivers/net/usb/usbnet.ko drivers/net/usb/rndis_host.ko drivers/net/usb/cdc_ether.ko "$ROOT/work/re/modules/out/"
	(cd "$ROOT/work/re/modules/out" && md5sum *.ko)
	echo "All vermagic strings match. Modules are in $TREE/drivers/net/usb/*.ko"
	echo "Copy them to the router and load manually on a RAM-booted image — see"
	echo "tools/re/modules/BUILD_PLAN.md 'Loading on the router' for the safety rules."
else
	echo "vermagic mismatch or build failure above — DO NOT load these on the router."
fi
exit $status
