#!/bin/bash
# Cross-build usbnet/rndis_host/cdc_ether against work/ref/nomis for the router kernel.
#
# See tools/re/modules/BUILD_PLAN.md for the full writeup.
#
#   tools/re/modules/build.sh
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/../../.." && pwd)
LOG=$ROOT/work/re/modules/build.log
mkdir -p "$(dirname "$LOG")"
# full output also goes to $LOG, so it can be read back without copy-pasting
exec > >(tee "$LOG") 2>&1
TREE=$ROOT/work/ref/nomis/kernel/linux
TC=$ROOT/work/toolchain/mips32--glibc--stable-2018.02-2/bin
WANT_VERMAGIC='2.6.30 SMP preempt mod_unload MIPS32_R1 32BIT '

[ -d "$TREE" ] || { echo "ERROR: $TREE missing (expected the nomis clone from the RE session)"; exit 1; }
[ -x "$TC/mips-linux-gcc" ] || { echo "ERROR: toolchain missing at $TC"; exit 1; }

export ARCH=mips
export CROSS_COMPILE=$TC/mips-linux-

cd "$TREE"

echo "== allnoconfig + board/options =="
make allnoconfig

# Enable board + the option set tools/re/probe/config.h already verified against the real
# kernel's struct layout (minus pure probe-only bookkeeping), plus what usbnet/rndis_host need.
# NOT enabling CONFIG_MODVERSIONS: the router kernel doesn't have it either (confirmed from
# stock usbserial.ko: a bare `vermagic=` line, no per-symbol __crc_* versions) — matching the
# vermagic string below is what actually has to be exact, not Module.symvers.
cat >> .config <<'CFG'
CONFIG_MIPS_BRCM=y
# int/string symbols with no Kconfig default (normally set by Broadcom's missing
# profile layer); pure runtime tunables, no effect on ABI/vermagic
CONFIG_BCM_SCHED_RT_PERIOD=1000000
CONFIG_BCM_SCHED_RT_RUNTIME=0
CONFIG_BCM_DEFAULT_CONSOLE_LOGLEVEL=7
# "implementation index" symbols for every bcm963xx driver subsystem — reachable
# regardless of whether that subsystem is actually enabled (depends only on the
# board family, not on the feature flag), so oldconfig prompts for all of them.
# "1" = the conventional impl1/ baseline; irrelevant here since we only build
# M=drivers/net/usb and none of these subsystems are compiled. Full list extracted
# directly from Kconfig (grep -oE '^config [A-Z0-9_]*_IMPL$'), not hand-copied.
CONFIG_BCM_ADSL_IMPL=1
CONFIG_BCM_ARL_IMPL=1
CONFIG_BCM_BCMDSP_IMPL=1
CONFIG_BCM_BCMPROF_IMPL=1
CONFIG_BCM_BOARD_IMPL=1
CONFIG_BCM_BPM_IMPL=1
CONFIG_BCM_CHIPINFO_IMPL=1
CONFIG_BCM_DECTSHIM_IMPL=1
CONFIG_BCM_DECT_IMPL=1
CONFIG_BCM_ENDPOINT_IMPL=1
CONFIG_BCM_ENET_IMPL=1
CONFIG_BCM_EXT_BONDING_IMPL=1
CONFIG_BCM_FAP_IMPL=1
CONFIG_BCM_GPON_IMPL=1
CONFIG_BCM_I2C_BUS_IMPL=1
CONFIG_BCM_I2C_CHIP_IMPL=1
CONFIG_BCM_INGQOS_IMPL=1
CONFIG_BCM_ISDN_IMPL=1
CONFIG_BCM_LASER_IMPL=1
CONFIG_BCM_LOG_IMPL=1
CONFIG_BCM_P8021AG_IMPL=1
CONFIG_BCM_PKTCMF_IMPL=1
CONFIG_BCM_PKTDMA_IMPL=1
CONFIG_BCM_PKTFLOW_IMPL=1
CONFIG_BCM_PROCFS_IMPL=1
CONFIG_BCM_PWRMNGT_IMPL=1
CONFIG_BCM_SERIAL_IMPL=1
CONFIG_BCM_SPU_IMPL=1
CONFIG_BCM_TRNG_IMPL=1
CONFIG_BCM_USB_IMPL=1
CONFIG_BCM_VLAN_IMPL=1
CONFIG_BCM_WLAN_IMPL=1
CONFIG_BCM_XTMCFG_IMPL=1
CONFIG_BCM_XTMRT_IMPL=1
CONFIG_BCM963268=y
CONFIG_SMP=y
CONFIG_NR_CPUS=2
CONFIG_PREEMPT=y
CONFIG_32BIT=y
CONFIG_CPU_MIPS32_R1=y
CONFIG_MODULES=y
CONFIG_MODULE_UNLOAD=y
CONFIG_NET=y
# master "Network device support" switch — separate from CONFIG_NET (the protocol stack);
# without it the whole drivers/net/ tree, USB networking included, is closed and not even
# written to .config, let alone prompted
CONFIG_NETDEVICES=y
CONFIG_INET=y
CONFIG_IPV6=y
CONFIG_XFRM=y
CONFIG_NETFILTER=y
CONFIG_NF_CONNTRACK=y
CONFIG_BRIDGE=y
CONFIG_BRIDGE_NETFILTER=y
CONFIG_NET_SCHED=y
CONFIG_NET_CLS_ACT=y
CONFIG_BCM_VLAN=y
CONFIG_PM=y
# (no PM_SLEEP: impossible on SMP here — ARCH_SUSPEND_POSSIBLE depends on !SMP)
# Options that change struct layouts or inline code, matching tools/re/probe/config.h and the
# live router (SLAB: no /sys/kernel/slab + SLAB-format slabinfo; HZ: timer IRQs ~1000/s per CPU).
# oldconfig silently defaulted all of these differently the first time round.
CONFIG_EMBEDDED=y
CONFIG_BASE_FULL=y
CONFIG_SYSFS=y
CONFIG_PROC_FS=y
CONFIG_HOTPLUG=y
CONFIG_SLAB=y
# CONFIG_SLUB is not set
# CONFIG_SLOB is not set
CONFIG_HZ_1000=y
# CONFIG_HZ_250 is not set
CONFIG_HZ=1000
CONFIG_BLOG=y
CONFIG_WIRELESS=y
CONFIG_WIRELESS_EXT=y
CONFIG_11ac_throughput_patch_from_412L07=y
# struct module layout: the router has KALLSYMS (/proc/kallsyms), which adds 20 bytes between
# init and exit (router .ko files: section 0x11c, exit at 0x114; without it 0x108/0x100)
CONFIG_KALLSYMS=y
# USB_ARCH_HAS_OHCI/EHCI have no prompt of their own (pure `default`-computed,
# default n on non-PCI MIPS) and get silently recomputed by oldconfig even if set
# here by hand — fixed instead via `select` on the BCM963268 board Kconfig entry
# (see arch/mips/bcm963xx/Kconfig; real router confirmed to have USB host support
# from its own shipped ehci-hcd.ko/ohci-hcd.ko)
CONFIG_USB_SUPPORT=y
CONFIG_USB=y
# USB_NET_RNDIS_HOST depends on EXPERIMENTAL, off by default since allnoconfig
CONFIG_EXPERIMENTAL=y
# =m, not =y: `make M=drivers/net/usb modules` only builds .ko files for symbols set to
# module (m); =y (built-in) compiles fine but produces no loadable module at all
CONFIG_USB_USBNET=m
CONFIG_USB_NET_RNDIS_HOST=m
CONFIG_USB_NET_CDCETHER=m
CFG

set +o pipefail  # yes dies of SIGPIPE once oldconfig stops reading input; harmless
# twice: one pass is top-to-bottom, so a menu sourced before a symbol it depends on
# (drivers/net/Kconfig before drivers/usb/Kconfig) only opens on the second pass
yes "" | make oldconfig
yes "" | make oldconfig
set -o pipefail

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
