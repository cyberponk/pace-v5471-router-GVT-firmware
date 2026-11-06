#!/bin/bash
# Send one shell command to the router's serial console and print what came back.
# Needs the background logger writing work/re/serial/router-serial.log.
#   tools/re/serial_cmd.sh 'cat /proc/mtd' [wait_seconds]
L=$(cd "$(dirname "$0")/../.." && pwd)/work/re/serial/router-serial.log
# the console treats '^' as the SysRq prefix ('^b' reboots at once)
case "$1" in *'^'*) echo "refused: command contains '^' (SysRq on this console)" >&2; exit 2;; esac
before=$(wc -c < "$L")
# the FTDI adapter re-enumerates as ttyUSB0/1/... after a USB reconnect
TTY=$(ls /dev/ttyUSB* 2>/dev/null | head -1)
[ -n "$TTY" ] || { echo "no /dev/ttyUSB* (serial adapter not attached to the VM?)" >&2; exit 1; }
printf '%s\r' "$1" > "$TTY"
timeout "${2:-3}" tail -f /dev/null
tail -c +$((before + 1)) "$L" | tr -d '\r'
