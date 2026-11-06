# Building usbnet/rndis_host/cdc_ether for the router

Goal: cross-compile `usbnet.ko`, `rndis_host.ko`, `cdc_ether.ko` from
`work/ref/nomis` (github.com/nomis/bcm963xx_4.12L.06B_consumer,
`kernel/linux/drivers/net/usb/`) against the MIPS toolchain in
`work/toolchain/`, so they load on the router kernel.

## Why this should work (compatibility groundwork already done)

- Kernel is unmodified Broadcom BSP, not a custom build: struct
  layout fully cross-checked against this exact tree in
  `tools/re/probe/` — 103/103 offsets that a USB/net driver touches
  match (tools/re/probe/).
- **No CONFIG_MODVERSIONS** on the router kernel (confirmed earlier:
  stock `usbserial.ko` carries only a single `vermagic=` string, no
  per-symbol `__crc_*` versions) — so a module only needs to match the
  router's **exact vermagic string**, not per-symbol CRCs. That string
  is already known from the stock `usbserial.ko` in the firmware:

  ```
  2.6.30 SMP preempt mod_unload MIPS32_R1 32BIT
  ```

  This is produced by `UTS_RELEASE="2.6.30"` (no local/dirty suffix)
  plus `CONFIG_SMP=y`, `CONFIG_PREEMPT=y`, `CONFIG_MODULE_UNLOAD=y`,
  `CONFIG_32BIT=y`, and the MIPS ISA level (`CONFIG_CPU_MIPS32_R1=y`)
  — a much narrower set of options than the full struct-layout config,
  and one we can verify by inspecting the built module before ever
  touching the router (`modinfo` / `strings | grep vermagic`).

- Board Kconfig symbol confirmed real (not a guess): `BCM963268`
  ("963268 VDSL board") in `arch/mips/bcm963xx/Kconfig`, selects
  `DMA_NONCOHERENT`, `SYS_SUPPORTS_SMP`, `NR_CPUS_DEFAULT_2`,
  `BRCM_DCACHE_SHARED` — matches what `tools/re/probe/config.h`
  already has.

## What's NOT available in this mirror

No `targets/`/profile directory (the layer that normally generates a
board `.config` from a product-line definition) — only `kernel/linux`,
`bcmdrivers/`, `shared/`. No shipped `bcm963xx_defconfig` in
`arch/mips/configs/` either. A `.config` has to be built by hand from
Kconfig (`allnoconfig` + enable the needed symbols + `oldconfig`), not
copied from a default.

## What the script does (`tools/re/modules/build.sh`)

`allnoconfig`, then enables the board (`BCM963268` — confirmed real
Kconfig symbol, not a guess) plus the option set `tools/re/probe/config.h`
verified against the real kernel's struct layout, runs `oldconfig` and
`modules_prepare`, builds just `drivers/net/usb` (`usbnet.ko`,
`rndis_host.ko`, `cdc_ether.ko`), then checks each module's `vermagic=`
string against the router's own (read from stock `usbserial.ko` in the
firmware: `2.6.30 SMP preempt mod_unload MIPS32_R1 32BIT`). It refuses to
call the build a success if any module's vermagic doesn't match exactly.

No `CONFIG_MODVERSIONS`, matching the router kernel (confirmed: stock
`usbserial.ko` carries only the one `vermagic=` line, no per-symbol
`__crc_*`), so vermagic is the only cross-check that has to be exact —
not per-symbol CRCs.

```

## Loading on the router — safety rules

- **RAM-boot only**, never flash a kernel/module change untested.
- **Load manually over SSH/telnet after boot**, never from an rc
  script — a bad module must not be able to boot-loop the router.
- `insmod usbnet.ko && insmod cdc_ether.ko && insmod rndis_host.ko`
  (or `modprobe` if depmod has been run); watch `dmesg`/serial console
  for the first few seconds after each `insmod`.
- Have the serial console (115200 8N1) connected for this test — if
  the network stack wedges, that may be the only way to see what
  happened or to recover.

## Status: built, 2026-10-27

All three built and their `vermagic=` strings match the real router's own
shipped modules **exactly**, byte for byte (including a trailing space in
the string itself — confirmed against the actual bytes in the firmware's
stock `usbserial.ko`, not just eyeballed): `usbnet.ko`, `rndis_host.ko`,
`cdc_ether.ko`. Copies kept at `work/re/modules/out/*.ko` (outside the
cloned tree, which a future rebuild could disturb). **Tested on the router 2026-10-28/30** (plus `mii.ko`): load
cleanly, Android RNDIS phone works as `eth3G`; shipped in cyberponk since v1.1.1
(`tools/configure.py`, `tetherd`).

### The full Kconfig fix chain (for next time / a from-scratch rebuild)

`allnoconfig` + hand-picking options is fragile on this tree because the
Broadcom profile layer that would normally supply defaults and wiring is
missing from this GPL mirror. Every one of these was found by tracing an
actual `oldconfig` hang or a silently-disabled symbol back to its Kconfig
definition, not guessed — `tools/re/modules/build.sh` now bakes in all of
them for a clean from-scratch run:

1. Three Kconfig `int` symbols with no default at all (`BCM_SCHED_RT_PERIOD`,
   `BCM_SCHED_RT_RUNTIME`, `BCM_DEFAULT_CONSOLE_LOGLEVEL`) — `oldconfig`
   loops forever re-asking since blank never satisfies a defaultless int.
2. All 34 `*_IMPL` ("implementation index") symbols in
   `arch/mips/bcm963xx/Kconfig` — same defaultless-int problem, one per
   driver subsystem, reachable regardless of whether that subsystem is
   itself enabled.
3. `CONFIG_USB_ARCH_HAS_OHCI`/`EHCI` have no prompt of their own (pure
   `default`-computed, default `n` on non-PCI MIPS) — manually setting them
   in `.config` doesn't stick, `oldconfig` recomputes and discards it.
   Fixed with a `select` added directly to the `BCM963268` board Kconfig
   entry (`arch/mips/bcm963xx/Kconfig`) instead — justified independently
   by the real router's own shipped `ehci-hcd.ko`/`ohci-hcd.ko`.
4. `CONFIG_USB_SUPPORT` (the whole USB `menuconfig`) was written
   `# is not set` by the base `allnoconfig` and never touched again —
   `oldconfig` only reconsiders a symbol it hasn't already got an answer
   for, so everything nested inside (`USB`, the net-device USB menu, etc.)
   stayed invisible even once we set `CONFIG_USB=y`.
5. **`oldconfig` fully regenerates `.config` from its own resolved state
   each run — it is not an accumulating append-only log.** A hint for a
   symbol that's unreachable at the *start* of a run gets silently dropped
   from the canonical file `oldconfig` writes out, even if it was present
   (and even applied) in an earlier run. This bit us twice (`CONFIG_USB`,
   then the three USB-networking drivers) — the fix each time was just
   re-appending the value and running `oldconfig` again.
6. Kconfig does **one straight top-to-bottom pass** per invocation; a
   `depends on` referencing a symbol defined *later* in file-include order
   sees that symbol's value from *before this run started*, not its
   mid-run value. `drivers/net/Kconfig` (containing the USB-networking
   menu) is sourced before `drivers/usb/Kconfig` — so the first run where
   we set `CONFIG_USB=y` didn't open the networking menu; it only became
   visible on the *next* `oldconfig` invocation, once `USB=y` was already
   sitting in `.config` from the start.
7. `CONFIG_NETDEVICES` (master "Network device support" switch — distinct
   from `CONFIG_NET`, the protocol stack) was never set at all. Without it
   the entire `drivers/net/` tree, USB networking included, stays closed
   and isn't even written to `.config`, let alone prompted.
8. `CONFIG_USB_NET_RNDIS_HOST` specifically also `depends on EXPERIMENTAL`,
   off since `allnoconfig`.
9. **The actual last blocker, and the simplest one:** `make M=drivers/net/usb
   modules` only produces a `.ko` for symbols set to `m` (module) — `=y`
   (built into the kernel) compiles fine and silently produces nothing
   loadable at all. `CONFIG_USB_USBNET`/`RNDIS_HOST`/`CDCETHER` need `=m`;
   `CONFIG_USB`/`USB_SUPPORT` are fine staying `=y` (USB core built in,
   individual class drivers loadable — a very normal real-world config).

Also needed, non-Kconfig: `include/linux/compiler-gcc6.h` (this tree
predates GCC 5/6, `compiler-gcc.h`'s dispatch has no entry past gcc4 —
added a one-line shim including `compiler-gcc4.h`, API-compatible); and
`set +o pipefail` around `yes "" | make oldconfig` (`yes` dies of SIGPIPE
the instant `oldconfig` stops reading, which `pipefail` would otherwise
treat as the whole pipeline failing even though the build step itself
succeeded).
