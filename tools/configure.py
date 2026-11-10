#!/usr/bin/env python3
"""Apply the cyberponk configuration to work/rootfs (run after strip.sh, under fakeroot).

- copies tools/overlay/ into the rootfs, generates pt_BR pages from en_US ones
- copies the USB tethering modules from work/re/modules/out (tools/re/modules/build.sh)
- sets factory defaults in router.conf (AP mode, 3G modem/WAN 6 skeleton)
- configd schema additions: LANDevice_N_IPInterface_N_Gateway, LANDevice_N_DNSServers
  (init.d/lanip already reads both), Device_OperatingMode (AP|Router)
- version string from VERSION (cyberponk-vX.Y.Z), "Pace v5471 Router" header, menu per operating mode,
  hides removed features, default web password "admin"
- /var tmpfs 24M so a firmware upload fits (web upgrade stages the image in /var/tmp)

  python3 -I tools/configure.py          (NI_VERSION=... overrides the version string)
"""
import json, os, re, shutil, subprocess, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'tools'))
from i18n_pt_BR import translate  # noqa: E402
import descriptions  # noqa: E402

RFS = os.path.join(ROOT, 'work', 'rootfs')
OVL = os.path.join(ROOT, 'tools', 'overlay')
B = os.path.join(RFS, 'etc', 'bewan')
IAD = os.path.join(B, 'iad')
LANGS = ('en_US', 'pt_BR')
with open(os.path.join(ROOT, 'VERSION')) as _f:
    VERSION = os.environ.get('NI_VERSION', 'cyberponk-v' + _f.read().strip())

# configd stores type="password" params AES-256-ECB encrypted (ModelAESEncrypt in sbin/configd):
# key = the 16-byte static password repeated twice, plaintext zero-padded to 16-byte blocks, hex.
PW_KEY = '0a2020427c2261db1278b29b27b2ce31' * 2


def bewan_encrypt(plain):
    raw = plain.encode()
    data = raw.ljust(-(-len(raw) // 16) * 16, b'\0')
    out = subprocess.run(['openssl', 'enc', '-e', '-aes-256-ecb', '-K', PW_KEY, '-nopad'],
                         input=data, capture_output=True, check=True).stdout
    return out.hex().upper()


WEB_PASSWORD = 'admin'

DEFAULTS = {
    'Device_Hostname': "'PaceAP'",
    'Device_OperatingMode': "'AP'",
    # router mode: phone on USB tethering takes over while the WAN is down (tetherd)
    'Device_TetherFailover': '1',
    # router mode, tetherd: addresses pinged through the WAN and the phone to check the Internet
    'Device_InternetProbes': "'1.1.1.1,8.8.8.8'",
    # router mode, tetherd: LAN clients can't reach the network on the WAN side
    'Device_WANIsolate': '0',
    # web admin (User_3, stock default gvt12345; the web page asks for a new one at the first login).
    # The SSH / Telnet user (User_2, uid 0) was also "admin" with the same password (login.cgi
    # changes the password by login name): now "shell", with its own password Device_ShellPassword
    # (Account Settings page; no login until it is set). The web pages can't write User_2 itself
    # (system entry, User=0: "forbidden to write on a rule that does not belong to you")
    'User_3_Password': "'%s'" % bewan_encrypt(WEB_PASSWORD),
    'User_2_Username': "'shell'",
    'User_2_Enable': '1',
    'User_2_Password': "''",
    'Device_ShellPassword': "''",
    # router mode, tetherd (lib/ni-guard): Wi-Fi devices isolated from the LAN by default (1) or
    # not (0), and per-device exceptions "mac=1,mac=0" (Wireless page, connected devices)
    'Device_WiFiIsolateDefault': '0',
    'Device_WiFiIsolate': "''",
    # per-device SSH host key (scripts/ssh-hostkey, hex), made at the first SSH start
    'Device_SSHHostKey': "''",
    'Hardware_VoIP': '0',
    # management IP: DHCP client on lan1, static values kept as template
    'LANDevice_1_IPInterface_1_AddressingType': "'DHCP'",
    'LANDevice_1_HostConfig_DHCPServerEnable': '0',
    'LANDevice_1_HostConfig6_RAServer_Enable': '0',
    # services
    'Services_Telnet_Enable': '0',
    'Services_SSH_Enable': '0',
    # DNS over TLS (scripts/dnsmasq-ni, dotproxy): off|cloudflare|quad9|google; rebinding protection
    'Services_DnsForwarder_DoT': "'off'",
    'Services_DnsForwarder_RebindProtect': '1',
    'Services_MiniUPnPd_Enable': '0',
    'Services_MiniUPnPd_EnableUPnP': '0',
    # iCam detection also started miniupnpd (UDP 1900) with UPnP off
    'Services_MiniUPnPd_EnableiCamDetection': '0',
    'Services_IgmpProxy_Enable': '0',
    'Services_WANAutoConfig_Enable': '0',
    # NTP through LAN 1 (AP mode, the default; the Operating Mode page switches it with the mode)
    'Services_Time_NTPInterfaceType': "'LANDevice'",
    'Services_Time_NTPInterfaces': '1',
    # Brazil dropped daylight saving time in 2019 (stock: BRT3BRST,M10.3.0/0,M2.3.0/0, one hour off)
    'Services_Time_LocalTimeZone': "'BRT3'",
    'Services_Time_LocalTimeZoneArea': "'BRT'",
    # router mode WAN = WANConnectionDevice 1 on the WAN port (eth4), set by config_internet.htm /
    # config_ap.htm; the GVT VoIP/VoD/IPTV connections and their VLANs (601/602/4000) are off
    # default: DHCP client, untagged (VID 0 = untagged in lib/vlan: eth4.0 gets the untagged frames;
    # WAN directly on eth4 receives nothing, the vlanctl untagged RX table defaults to DROP)
    'WANConnectionDevice_1_WANPPPConnection_Enable': '0',
    'WANConnectionDevice_1_WANPPPConnection_Username': "''",
    'WANConnectionDevice_1_WANPPPConnection_Password': "''",
    'WANConnectionDevice_1_WANIPConnection_Enable': '1',
    # WAN: no ping answers, no TR-069 port (7547, nothing listens: tr069 removed)
    'WANConnectionDevice_1_Firewall_AllowRemotePing': '0',
    'WANConnectionDevice_1_Service_1_Enable': '0',
    'WANConnectionDevice_1_WANIPConnection_AddressingType': "'DHCP'",
    'WANEthernetInterface_1_VLANInterface_1_VID': '0',
    'WANConnectionDevice_2_Enable': '0',
    'WANConnectionDevice_3_Enable': '0',
    'WANConnectionDevice_4_Enable': '0',
    'WANEthernetInterface_1_VLANInterface_2_Enable': '0',
    'WANEthernetInterface_1_VLANInterface_3_Enable': '0',
    'WANEthernetInterface_1_VLANInterface_4_Enable': '0',
    # wifi
    'WLANInterface_1_WPSEnable': '0',
    'WLANConfig_EasyPairing': '0',
    # 3G USB modem: ModemInterface 1 feeds WAN connection 6 (PPP, chat via scripts/modem3g)
    'ModemInterface_Count': '1',
    'ModemInterface_1_Enable': '0',
    'ModemInterface_1_Description': "'3G USB modem'",
    'ModemInterface_1_ModePref': "'3Gpref'",
    'WANConnectionDevice_6_Enable': '1',
    'WANConnectionDevice_6_Description': "'3G'",
    'WANConnectionDevice_6_User': '1',
    'WANConnectionDevice_6_Multicast': '0',
    'WANConnectionDevice_6_Multiplexed': '0',
    'WANConnectionDevice_6_PhysicalInterface_List': "'1'",
    'WANConnectionDevice_6_PhysicalInterface_1_Enable': '1',
    'WANConnectionDevice_6_PhysicalInterface_1_Type': "'ModemInterface'",
    'WANConnectionDevice_6_PhysicalInterface_1_Index': '1',
    'WANConnectionDevice_6_WANIPConnection_Enable': '0',
    'WANConnectionDevice_6_WANIP6Connection_Enable': '0',
    'WANConnectionDevice_6_WANPPPConnection_Enable': '1',
    'WANConnectionDevice_6_WANPPPConnection_IPv6CPEnable': '0',
    'WANConnectionDevice_6_WANPPPConnection_Username': "''",
    'WANConnectionDevice_6_WANPPPConnection_Password': "''",
    'WANConnectionDevice_6_DNSEnable': '1',
    'WANConnectionDevice_6_DNSOverrideAllowed': '1',
    'WANConnectionDevice_6_Firewall_Enable': '1',
}

# menu ids: always hidden / hidden in AP mode only
MENU_HIDE_ALWAYS = ['menu_wan_mode', 'menu_bbstats']
MENU_HIDE_AP = ['menu_internet', 'menu_3g', 'menu_lan', 'menu_applications', 'menu_firewall']
MENU_LABELS = {
    'en_US': {'menu_ap': 'Operating Mode', 'menu_3g': '3G Modem', 'menu_about': 'About', 'menu_ddns': 'Dynamic DNS', 'menu_ntp': 'NTP Server',
              'menu_backup': 'Backup / Restore',
              'menu_applications': 'Port Forwarding'},
    'pt_BR': {'menu_ap': 'Modo de Opera&ccedil;&atilde;o', 'menu_3g': 'Modem 3G', 'menu_about': 'Sobre',
              'menu_ddns': 'DNS Din&acirc;mico', 'menu_ntp': 'Servidor NTP', 'menu_backup': 'Backup / Restaura&ccedil;&atilde;o', 'menu_applications': 'Redirecionamento de Portas'},
}
# menu order (ids not listed, the hidden ones, follow)
MENU_ORDER = {
    'menu_settings': ['menu_ap', 'menu_internet', 'menu_3g', 'menu_lan', 'menu_ddns', 'menu_wireless', 'menu_advanced', 'menu_ntp',
                      'menu_firewall', 'menu_applications', 'menu_usb'],
    'menu_management': ['menu_admin_password', 'menu_resets', 'menu_backup', 'menu_utilities', 'menu_logread', 'menu_languages',
                        'menu_firmware', 'menu_changelog'],
}
NEW_PAGES = ['config_ap.htm', 'config_3g.htm', 'config_internet.htm', 'config_usb.htm', 'config_ddns.htm', 'ddns_log.htm',
             'config_ntp.htm', 'ntp_log.htm', 'fwupdate_log.htm', 'config_backup.htm']

CHANGELOG = '''<h4>%s</h4>
<p>* Based on Alacn-181231 (firmware <b>GVT-104452</b>).</p>
<p>* Operating modes: access point (default) and router. Page Operating Mode.</p>
<p>* Access point: management IP by DHCP or static, rescue address 169.254.25.1.</p>
<p>* Router mode: Internet on the WAN port by PPPoE (service name, VLAN, MAC clone), DHCP or fixed IP.</p>
<p>* Android USB tethering (RNDIS/CDC Ethernet): automatic failover while the WAN is down, setting on the USB Devices page, status on the Status page.</p>
<p>* Router mode: 3G USB modem page (APN, PIN, login, Internet source).</p>
<p>* Removed: DSL, VoIP, HPNA, TR-069, Samba, DLNA, USB storage, GVT hotspot/STB, diag shell.</p>
<p>* Kept: USB printer server, 3G modem support, firmware upgrade page.</p>
<p>* Security: dnsmasq 2.93, dropbear 2026.94 SSH with a per-device host key, optional DNS over TLS
(Cloudflare, Quad9, Google) and DNS rebinding protection, Wi-Fi client isolation (default and per device),
phone (USB tethering) link firewalled like the WAN, acsd port closed, no WAN ping / TR-069 port.</p>
<p>* Defaults: WPS, Telnet, SSH, UPnP, IGMP proxy off. Web password: admin (a new one is asked at the first login);
the SSH / Telnet user "shell" has its own password.</p>

''' % VERSION

NI_CSS = '''
/* header: product name as text on a solid grey (the inactive menu item colour) */
#header-gateway{ background:#bcbcbc; height:50px; padding-top:12px; }
.ni-logo{ font:bold 24px/40px Arial, Helvetica, sans-serif; color:#fff; padding-left:25px; letter-spacing:1px; }
#header-gateway .lang-menu{ margin-top:10px; }
/* cyberponk: page aligned left, no blue gradients (side ones on #content, top band on body) */
body{ background:#fff; }
#content{ background:none; }
/* menu 192 + content 1040 + 20 padding (a settings table with its description column is 1020);
   #conteudo-gateway adds 2x25 padding */
.wrap{ margin:0; width:1320px; }
#conteudo-gateway{ width:1260px; }
.col-722{ width:1040px; }
/* cyberponk: setting descriptions. In the HTML they sit under the label (small.ni-desc);
   menu.js moves them into their own last column (td.ni-desc-col) of a widened table */
.ni-desc{ display:block; font-size:11px; line-height:14px; color:#777; font-weight:normal; text-transform:none; margin-top:3px; }
/* every settings and list table the same width (the ones with a description column included) */
table.setupWifiTable, table.setupWifiTable.ni-wide, table.data-table{ width:1020px; }
/* Status page: colours instead of the fixed-height row image, so rows grow with their lines */
#status{ width:1020px; border-collapse:separate; border-spacing:0 5px; }
#status th{ background:#F68B1F; border-radius:5px 0 0 5px; height:auto; min-height:43px; vertical-align:middle;
    border-right:2px solid #e57317; }
#status th{ text-align:left; white-space:nowrap; }
#status th span{ float:none; display:inline-block; vertical-align:middle; padding:0 0 0 4px; }
#status th img{ float:none; vertical-align:middle; margin:5px 8px 5px 5px; }
#status td{ background:#f2f2f2; padding:6px 0; vertical-align:middle; }
#status td.status-link{ border-radius:0 5px 5px 0; border-left:2px solid #fff; }
#status .status-line-2{ width:150px; padding-bottom:2px; }
#status .status-detail{ margin-right:10px; }
#status .ni-ok{ color:#3a9a1a; } #status .ni-bad{ color:#d00; }
/* Advanced: mDNS name next to its switch */
#Services_MDNSResponder_Enable{ display:inline-block; vertical-align:middle; }
/* Wireless: connected devices */
#niWifiClients tr.ni-head td, #niWifiClients tr.ni-head td:first-child{ font-weight:bold; text-align:center; background:#e0e2e4;
    padding:8px 4px; }
#niWifiClients tbody#niWifiList td, #niWifiClients tbody#niWifiList td:first-child{ text-align:center; font-weight:normal;
    padding:8px 4px; }
#niWifiClients td .btn-default-orange-small{ float:none; display:inline-block; }
.ni-warn{ background:#fdecea; border:1px solid #e0a39c; color:#a12c1f; padding:8px 10px; margin:0 0 10px; }
.ni-ok{ background:#e9f6ec; border:1px solid #9ccfa8; color:#1d6b33; padding:8px 10px; margin:0 0 10px; }
.ni-pwgen{ float:none !important; display:inline-block; margin-left:6px; vertical-align:middle; }
.ni-pw{ display:inline-block; width:140px; height:6px; margin-top:6px; background:#ddd; border-radius:3px; vertical-align:middle; overflow:hidden; }
.ni-pw span{ display:block; height:100%; width:0; border-radius:3px; }
#niIsoDef{ margin-left:6px; }
.ni-errors{ color:#c0392b; font-weight:bold; margin:12px 0 0; }
.ni-errors.done{ color:#27ae60; }
.ni-errors a{ font-weight:normal; text-decoration:underline; cursor:pointer; }
#ni-err-list{ color:#444; font-weight:normal; font-size:11px; white-space:pre-wrap; background:#f4f4f4; padding:8px; margin-top:6px; }
#niWifiClients td.ni-isodef{ text-align:left; padding:8px 14px; }
#niWifiClients td.ni-isodef small{ font-weight:normal; display:block; margin-top:4px; }
/* tab bars as wide as the tables: 1016 + 2x2 padding; tab = share - 20 padding - 2 border */
#menu-configLan ul, #menu-configWifi ul{ width:1016px; }
#menu-configLan ul li a{ width:232px; }
#menu-configWifi ul li a{ width:486px; }
/* DDNS page: action icons and update log */
table.data-table td.ni-actions{ white-space:nowrap; text-align:center; }
table.data-table td.ni-actions img{ cursor:pointer; margin:0 5px; vertical-align:middle; }
/* DDNS page: update log */
table.setupWifiTable tbody td.ni-log-cell, table.setupWifiTable tbody td.ni-log-cell:first-child{ text-align:left; font-weight:normal;
    background:#fff; padding:10px 14px; }
pre.ni-log{ margin:0; white-space:pre-wrap; font:12px/17px Consolas, "DejaVu Sans Mono", monospace; color:#444; }
table.setupWifiTable td.ni-desc-row, table.setupWifiTable tbody td.ni-desc-row:first-child{ font-size:11px; line-height:15px; color:#777; font-weight:normal;
    text-align:left; padding:8px 14px; background:#f8f8f9; }
/* on/off switches: the stock widget (div.switchButton, state attribute set by the page scripts)
   and the ni pages' checkbox (label.ni-switch) drawn as the same modern toggle */
.switchButton{ background:#c9c9c9 none !important; width:44px; height:24px; border-radius:12px; position:relative;
    transition:background-color .2s; }
.switchButton:after, .ni-switch span:after{ content:""; position:absolute; top:3px; left:3px; width:18px; height:18px;
    border-radius:50%; background:#fff; box-shadow:0 1px 2px rgba(0,0,0,.35); transition:left .2s; }
.switchButton[state="1"]{ background-color:#F68B1F !important; }
.switchButton[state="1"]:after{ left:23px; }
.ni-switch{ position:relative; display:inline-block; width:44px; height:24px; vertical-align:middle; cursor:pointer; }
.ni-switch input{ position:absolute; opacity:0; width:0; height:0; }
.ni-switch span{ position:absolute; top:0; left:0; right:0; bottom:0; border-radius:12px; background:#c9c9c9;
    transition:background-color .2s; }
.ni-switch input:checked + span{ background:#F68B1F; }
.ni-switch input:checked + span:after{ left:23px; }
table.setupWifiTable tbody td.ni-desc-col{ width:330px; font-size:11px; line-height:15px; color:#777; font-weight:normal;
    text-align:left; padding:6px 12px; background:#f8f8f9; }
'''


def read(path):
    with open(path, encoding='utf-8', errors='surrogateescape') as f:
        return f.read()


def write(path, txt):
    mode = os.stat(path).st_mode if os.path.exists(path) else 0o644
    if os.path.exists(path):
        os.chmod(path, mode | 0o200)  # some web files are 0444
    with open(path, 'w', encoding='utf-8', errors='surrogateescape') as f:
        f.write(txt)
    os.chmod(path, mode)


def edit(path, fn):
    old = read(path)
    new = fn(old)
    if new != old:
        write(path, new)
        print('edited', os.path.relpath(path, RFS))


def sub1(pattern, repl, txt, what, flags=0, count=1):
    """re.subn that insists on exactly `count` matches (0 = at least one)."""
    new, n = re.subn(pattern, repl, txt, flags=flags)
    if (count and n != count) or n == 0:
        sys.exit(f'{what}: expected {count or ">=1"} match(es), got {n}')
    return new


def tether_busybox():
    """busybox copy for the tethering udhcpc, with DHCP option 43 disabled.
    Bewan added a vendor-specific (43) parser (type 0x0c) to udhcpc; Android tethering sends
    43 = "ANDROID_METERED" and udhcpc segfaults right after the lease, before the script runs.
    Renumber 43 to 254 in dhcp_optflags (pairs of flags, code) so it is ignored."""
    d = bytearray(open(os.path.join(RFS, 'bin', 'busybox'), 'rb').read())
    sig = bytes.fromhex('110107023103310621072109130c050d130f')  # subnet, timezone, router...
    if d.count(sig) != 1:
        sys.exit('busybox: dhcp_optflags table not found')
    off = d.find(sig) + 2 * 17  # 18th entry: vendorspecific
    if d[off:off + 2] != b'\x0c\x2b':
        sys.exit('busybox: unexpected option 43 entry %s' % d[off:off + 2].hex())
    d[off + 1] = 0xfe
    dst = os.path.join(RFS, 'usr', 'lib', 'tether', 'busybox')
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    with open(dst, 'wb') as f:
        f.write(d)
    os.chmod(dst, 0o755)
    print('tether busybox, option 43 off at', hex(off + 1))


def copy_overlay():
    for d, _, files in os.walk(OVL):
        rel = os.path.relpath(d, OVL)
        os.makedirs(os.path.join(RFS, rel), exist_ok=True)
        for fn in files:
            dst = os.path.join(RFS, rel, fn)
            if os.path.lexists(dst):
                os.remove(dst)  # stock pages replaced by the overlay are read-only
            shutil.copyfile(os.path.join(d, fn), dst)
            os.chmod(dst, 0o755 if '/iad/' not in dst else 0o644)
            print('overlay', os.path.join(rel, fn))
    # USB tethering modules, built by tools/re/modules/build.sh (not in git)
    kmod = os.path.join(RFS, 'lib', 'modules', '2.6.30', 'kernel', 'drivers', 'net')
    os.makedirs(os.path.join(kmod, 'usb'), exist_ok=True)
    for ko in ('mii', 'usb/usbnet', 'usb/cdc_ether', 'usb/rndis_host'):
        src = os.path.join(ROOT, 'work', 're', 'modules', 'out', os.path.basename(ko) + '.ko')
        if not os.path.isfile(src):
            sys.exit(f'{src} missing: run tools/re/modules/build.sh')
        shutil.copyfile(src, os.path.join(kmod, ko + '.ko'))
        os.chmod(os.path.join(kmod, ko + '.ko'), 0o644)
        print('module', ko + '.ko')
    tether_busybox()
    # static curl (TLS 1.2/1.3) + CA bundle for the dynamic DNS updates, built by tools/re/curl/build.sh
    out = os.path.join(ROOT, 'work', 're', 'curl', 'out')
    for src, dst, mode in (('curl', 'usr/bin/curl', 0o755), ('ca-certificates.crt', 'etc/ssl/certs/ca-certificates.crt', 0o644)):
        if not os.path.isfile(os.path.join(out, src)):
            sys.exit(f'{out}/{src} missing: run tools/re/curl/build.sh')
        os.makedirs(os.path.dirname(os.path.join(RFS, dst)), exist_ok=True)
        shutil.copyfile(os.path.join(out, src), os.path.join(RFS, dst))
        os.chmod(os.path.join(RFS, dst), mode)
        print('copied', dst)
    net_bins()
    for page in NEW_PAGES:
        src = read(os.path.join(IAD, 'en_US', 'admin', page))
        dst = os.path.join(IAD, 'pt_BR', 'admin', page)
        write(dst, translate(page, src))
        print('generated', os.path.relpath(dst, RFS))


def net_bins():
    # tools/re/net/build.sh: dnsmasq 2.93 (stock 2.45 kept as the fallback of scripts/dnsmasq-ni),
    # dropbear 2026.94 for the stock 0.52 sshd and its DSS host key shared by all units, dotproxy
    out = os.path.join(ROOT, 'work', 're', 'net', 'out')
    for f in ('dnsmasq', 'dropbearmulti', 'dotproxy'):
        if not os.path.isfile(os.path.join(out, f)):
            sys.exit(f'{out}/{f} missing: run tools/re/net/build.sh')
    old = os.path.join(RFS, 'sbin', 'dnsmasq-2.45')
    if not os.path.exists(old):
        os.rename(os.path.join(RFS, 'sbin', 'dnsmasq'), old)
    for src, dst in (('dnsmasq', 'sbin/dnsmasq'), ('dropbearmulti', 'usr/sbin/dropbearmulti'), ('dotproxy', 'usr/sbin/dotproxy')):
        d = os.path.join(RFS, dst)
        if os.path.lexists(d):
            os.remove(d)
        shutil.copyfile(os.path.join(out, src), d)
        os.chmod(d, 0o755)
        print('copied', dst)
    for link in ('dropbear', 'dropbearkey'):
        d = os.path.join(RFS, 'usr', 'sbin', link)
        if os.path.lexists(d):
            os.remove(d)
        os.symlink('dropbearmulti', d)
    for f in ('usr/sbin/sshd', 'etc/bewan/dsskey.bin'):
        if os.path.lexists(os.path.join(RFS, f)):
            os.remove(os.path.join(RFS, f))
            print('removed', f)


def diag_user(txt):
    # the shell user (User_2 "shell") takes its password from Device_ShellPassword; none = no login
    return sub1(r'(\ndiag_generate_user\(\) \{\n\tlocal user="\$1" pass="\$2" shell=[^\n]*\n)',
                lambda m: m.group(1) + '\tif [ "$user" = shell ]; then\n\t\tpass=${Device_ShellPassword:-}\n'
                '\t\t[ -n "$pass" ] || return 0\n\tfi\n', txt, 'user.d/diag shell password')


def dhcpclient_lib(txt):
    # LAN DHCP client (AP mode management address): send the host name (option 12) and a vendor
    # class (option 60), so the main router lists the device by name
    return sub1(r'(\n([ \t]*)# Activate DHCP option 60 \(Vendor Class\)\n\s*local vendorclass; eval vendorclass=[^\n]*\n)',
                lambda m: m.group(1) + m.group(2) + '[ -n "$vendorclass" ] || vendorclass="Pace V5471"\n' +
                m.group(2) + 'cmdline_args="$cmdline_args -H ${Device_Hostname:-PaceAP}"\n', txt, 'lib/dhcpclient lan hostname')


def lan_initd(txt):
    # AP mode: the LAN bridge (the management interface) takes the unit's base MAC (WAN port and
    # Wi-Fi, Pace OUI 84:e0:58) instead of the lowest port MAC (locally administered 06:..., no
    # manufacturer in the main router's ARP list); set before the DHCP client starts
    # (factory data: pzinfo lanmac; eth4 still has a placeholder 00:0c:c3:... at this point)
    return sub1(r'(\n([ \t]*)brctl addbr \$ifname\n)', lambda m: m.group(1) + m.group(2) +
                'if [ "$ifname" = lan1 ] && [ "${Device_OperatingMode:-AP}" != Router ]; then\n' +
                m.group(2) + "  local nimac=$(pzinfo -a 2>/dev/null | sed -n 's/^lanmac : //p' | tr 'A-F' 'a-f')\n" +
                m.group(2) + '  case "$nimac" in [0-9a-f][0-9a-f]:*:*:*:*:[0-9a-f][0-9a-f]) ip link set $ifname address $nimac ;; esac\n' +
                m.group(2) + 'fi\n', txt, 'init.d/lan bridge mac')


def ntp_initd(txt):
    # every synchronisation (boot, every 2 min until synced, daily) records its time and outcome in
    # /var/status/ntpsync for the Status page (scripts/ntp-now writes it too)
    # (no tee in this busybox: a missing command in /bin/sh = patched dash stops the softdog = reboot)
    return sub1(r'(\n(\s*)ntpd -1sdf \$ntpcnf -i \\\$ifname \\\$dns -n \\\$sync_status) 2>&1 \| \$logger\n',
                lambda m: m.group(1) + ' > /var/run/ntp.out 2>&1\n' + m.group(2) + '$logger < /var/run/ntp.out\n' + m.group(2) +
                "r=failed; grep -q 'reply from' /var/run/ntp.out && r=ok\n" + m.group(2) +
                "mkdir -p /var/status; printf 'last=%s\\\\nresult=%s\\\\n' \"\\$(date '+%Y-%m-%d %H:%M:%S %Z')\" \\$r > /var/status/ntpsync\n",
                txt, 'init.d/ntp sync status')


def inetd(txt):
    # the stock script also opened Telnet and SSH whenever the kernel command line has console=
    # (alacn's kernel always has it); SSH is dropbear with the per-device key (scripts/ssh-hostkey)
    txt = sub1(r'\n\s*\[ "\$\?" = "0" \] && test_console_enable=1\n', '\n', txt, 'inetd test console')
    return sub1(r'(\n[ \t]*)if \[ "\$Services_SSH_Enable" = 1 -o "\$\{test_console_enable\}" = 1 \] && \[ -f /usr/sbin/sshd \]; then\n'
                r'\s*echo "ssh stream \$\{tcp_proto\} nowait root /usr/sbin/sshd sshd -i -d /etc/bewan/dsskey\.bin" >>\$conf_file\n',
                lambda m: m.group(1) + '# Backup / Restore page: settings server (scripts/ni-settings; LAN only, lib/ni-guard)' +
                m.group(1) + 'echo "8090 stream ${tcp_proto} nowait root /etc/bewan/scripts/ni-settings ni-settings" >>$conf_file' +
                m.group(1) + 'if [ "$Services_SSH_Enable" = 1 ] && [ -f /usr/sbin/dropbear ] && /etc/bewan/scripts/ssh-hostkey; then' +
                m.group(1) + '  echo "ssh stream ${tcp_proto} nowait root /usr/sbin/dropbear dropbear -i -r /var/bewan/ssh/dropbear_ed25519_host_key" >>$conf_file\n',
                txt, 'inetd ssh')


def dnsmasq_initd(txt):
    return sub1(r'\n(\s*)local cmd="/sbin/dnsmasq -C \$conf_file"\n', lambda m:
                '\n' + m.group(1) + 'local bin=$(/etc/bewan/scripts/dnsmasq-ni $conf_file "${Services_DnsForwarder_DoT:-off}" '
                '"${Services_DnsForwarder_RebindProtect:-1}" "${Services_DnsForwarder_Enable:-0}")\n' +
                m.group(1) + 'local cmd="${bin:-/sbin/dnsmasq-2.45} -C $conf_file"\n', txt, 'init.d/dnsmasq cmd')


def router_conf(txt):
    for k, v in DEFAULTS.items():
        line = f'{k}={v}'
        txt, n = re.subn(rf'^{re.escape(k)}=.*$', lambda m: line, txt, flags=re.M)
        if n == 0:
            txt = txt.rstrip('\n') + '\n' + line + '\n'
        elif n > 1:
            sys.exit(f'{k} defined {n} times')
    return txt


def router_xml(txt):
    txt = sub1(r'(\n(\s*)<ACLEnable type="int" writable="1" required="1" onchange="/etc/bewan/init\.d/wifiacl"[^\n]*\n)',
               lambda m: m.group(1) + m.group(2) +
               '<ACLMode type="string" values="allow,deny" writable="1" onchange="/etc/bewan/init.d/wifiacl" oid="110">allow</ACLMode>\n',
               txt, 'router.xml WLANInterface ACLMode')
    # NTP page Update now button (any new value): scripts/ntp-now
    txt = sub1(r'(\n(\s*)<NTPSynchronized type="bool"[^\n]*\n)', lambda m: m.group(1) + m.group(2) +
               '<UpdateNow type="string" writable="1" onchange="/etc/bewan/init.d/ntp-now" oid="10"/>\n', txt,
               'router.xml Time UpdateNow')
    txt = sub1(r'(\n(\s*)<FilterSRVRequest type="bool"[^\n]*init\.d/dnsmasq[^\n]*\n)',
               lambda m: m.group(1) + m.group(2) +
               '<DoT type="string" values="off,cloudflare,quad9,google" writable="1" onchange="/etc/bewan/init.d/dnsmasq" oid="11">off</DoT>\n' +
               m.group(2) + '<RebindProtect type="bool" writable="1" onchange="/etc/bewan/init.d/dnsmasq" oid="12">1</RebindProtect>\n',
               txt, 'router.xml DnsForwarder DoT')
    txt = sub1(r'(<Server type="string" values="dyndns,dyndns\.it,easydns,no-ip,ezip,dtdns,athos)"',
               r'\1,dynv6,nsupdate4,nsupdate6,customget"', txt, 'router.xml DynDNS Server values')
    txt = sub1(r'(\n(\s*)<RetryInterval type="int" values="0:59"[^\n]*init\.d/dyndns[^\n]*\n)',
               lambda m: m.group(1) + m.group(2) +
               '<URL type="string" writable="1" onchange="/etc/bewan/init.d/dyndns" oid="18"/>\n' + m.group(2) +
               # written by the DDNS page's Update now button (any new value): forced update
               '<UpdateNow type="string" writable="1" onchange="/etc/bewan/init.d/dyndns-now" oid="19"/>\n', txt,
               'router.xml DynDNS URL')
    m = re.search(r'(\n(\s*)<AddressingType type="string" values="Static,DHCP"[^\n]*'
                  r'init\.d/lanip[^\n]*\n)(\s*</IPInterface>)', txt)
    if not m:
        sys.exit('router.xml: LAN IPInterface anchor not found')
    gw = f'{m.group(2)}<Gateway type="ip4" writable="1" onchange="/etc/bewan/init.d/lanip" withparam="1" oid="5"/>\n'
    txt = txt[:m.end(1)] + gw + txt[m.end(1):]
    # LANDevice level DNSServers: next free oid after IPv6Status (33)
    m = re.search(r'(\n(\s*)<IPv6Status type="obj" status="lan_infos\.so!get_ip6status".*?</IPv6Status>\n)(\s*</LANDevice>)', txt, re.S)
    if not m:
        sys.exit('router.xml: LANDevice end anchor not found')
    dns = f'{m.group(2)}<DNSServers type="ips" writable="1" onchange="/etc/bewan/init.d/lanip" oid="34"/>\n'
    txt = txt[:m.end(1)] + dns + txt[m.end(1):]
    # Device_OperatingMode: flag only, the web page writes the dependent params and reboots
    return sub1(r'(\n(\s*)<IPv6SkipInterfaces [^\n]*\n)(\s*</Device>\n\s*<Services )',
                lambda m: m.group(1) + m.group(2) +
                '<OperatingMode type="string" values="AP,Router" writable="1" oid="40">AP</OperatingMode>\n' +
                # read by tetherd every round (cli get), no onchange handler needed
                m.group(2) + '<TetherFailover type="bool" writable="1" oid="41">1</TetherFailover>\n' +
                m.group(2) + '<InternetProbes type="string" writable="1" oid="42">1.1.1.1,8.8.8.8</InternetProbes>\n' +
                m.group(2) + '<WANIsolate type="bool" writable="1" oid="43">0</WANIsolate>\n' +
                m.group(2) + '<WiFiIsolateDefault type="bool" writable="1" oid="44">0</WiFiIsolateDefault>\n' +
                m.group(2) + '<WiFiIsolate type="string" writable="1" oid="45"/>\n' +
                m.group(2) + '<SSHHostKey type="string" writable="1" oid="46"/>\n' +
                m.group(2) + '<ShellPassword type="password" writable="1" onchange="/etc/bewan/init.d/users" oid="47"/>\n' +
                # Status page "Mark as examined" (any new value): scripts/errors-ack
                m.group(2) + '<ErrorsAck type="string" writable="1" onchange="/etc/bewan/init.d/errors-ack" oid="48"/>\n' +
                # Firmware page online update buttons ("check.<n>", "install.<n>"): scripts/fwupdate
                m.group(2) + '<FwUpdate type="string" writable="1" onchange="/etc/bewan/init.d/fwupdate" oid="49"/>\n' +
                # Backup / Restore page: one-time ticket for scripts/ni-settings (32 hex; "0" = spent)
                m.group(2) + '<SettingsTicket type="string" writable="1" oid="50"/>\n' + m.group(3),
                txt, 'router.xml Device end')


def wifi_lib(txt):
    # MAC filter mode: allow (stock, only the listed devices) or deny (the listed devices are blocked:
    # the Wireless page's client list Block button)
    return sub1(r'\n(\s*)ssid_conf_set wlFltMacMode allow\n', lambda m:
                '\n' + m.group(1) + "local aclmode; eval aclmode=\\${'WLANInterface_'$ETHID'_ACLMode':-allow}\n" +
                m.group(1) + '[ "$aclmode" = deny ] || aclmode=allow\n' +
                m.group(1) + 'ssid_conf_set wlFltMacMode $aclmode\n', txt, 'lib/wifi wlFltMacMode')


def dyndns_lib(txt):
    # providers added in lib/dyndns-ni (overlay)
    return sub1(r'(\ncreate_dyndns\(\) \{\n)', lambda m: m.group(1) +
                '  case "${server:-}" in dynv6|nsupdate4|nsupdate6|customget)\n'
                '    [ "${DYNDNS_NI_LIB:-0}" = 1 ] || . /etc/bewan/lib/dyndns-ni\n'
                '    create_dyndns_ni\n'
                '    return ;;\n'
                '  esac\n', txt, 'lib/dyndns create_dyndns')


def rc(txt):
    # rcS mounts /var with size=8M; a firmware upload (9-14 MB) is staged in /var/tmp.
    # Give type and device: a bare `mount -o remount` makes busybox 1.17 copy "relatime" from
    # /proc/mounts into the tmpfs data, and the kernel rejects the whole remount.
    return sub1(r'(\ntest -z "\$\(mount -t tmpfs \| grep /var\)" && mount -t tmpfs -o size=8M shm /var\n)',
                r'\1mount -t tmpfs -o remount,size=24M shm /var\n', txt, 'rc /var mount', count=1)


PRODUCT = 'Pace v5471 Router'
PRODUCT_AP = 'Pace v5471 Access Point'


def branding(txt):
    txt = re.sub(r'<a href="http://www\.gvt\.com\.br"><img src="\.\./\.\./img/logo-gvt\.png"[^>]*></a>',
                 '<span class="ni-logo left">%s</span>' % PRODUCT, txt)
    txt = txt.replace('<span class="ni-logo left">NI</span>', '<span class="ni-logo left">%s</span>' % PRODUCT)
    txt = re.sub(r'\n?[ \t]*<img src="\.\./\.\./img/power-box\.png"[^>]*>', '', txt)
    return txt.replace('<title>GVT</title>', '<title>Pace v5471</title>')


def menu_js(lang):
    labels = MENU_LABELS[lang]

    def item(mid, href):
        return f"'<li id=\"{mid}\"><a href=\"{href}\"><strong>{labels[mid]}</strong></a></li>',"

    def fn(txt):
        txt = sub1(r"(\n(\s*)'<li id=\"menu_lan\">[^\n]*\n)",
                   lambda m: m.group(1) + m.group(2) + item('menu_ddns', 'config_ddns.htm') + '\n' +
                   m.group(2) + item('menu_ntp', 'config_ntp.htm') + '\n' +
                   m.group(2) + item('menu_ap', 'config_ap.htm') + '\n', txt, 'menu_lan')
        txt = sub1(r"(\n(\s*)'<li id=\"menu_internet\">[^\n]*\n)",
                   lambda m: m.group(1) + m.group(2) + item('menu_3g', 'config_3g.htm') + '\n', txt, 'menu_internet')
        txt = sub1(r"(\n(\s*)'<li id=\"menu_resets\">[^\n]*\n)",
                   lambda m: m.group(1) + m.group(2) + item('menu_backup', 'config_backup.htm') + '\n', txt, 'menu_resets')
        txt = sub1(r'(id="menu_about"><a class="menu-header" href="about\.htm">)[^<]*', r'\g<1>' + labels['menu_about'],
                   txt, 'menu_about')
        flt = ('\n// cyberponk: hide pages of removed features, and router pages in AP mode\n'
               '(function() {\n'
               '    var mode = "AP";\n'
               '    try { mode = eval(\'(<!--#echo jsonvar="cli=Device_OperatingMode"-->)\') || "AP"; } catch (e) {}\n'
               f'    var hide = {MENU_HIDE_ALWAYS!r};\n'
               f'    if (mode != "Router") hide = hide.concat({MENU_HIDE_AP!r});\n'
               '    var out = [], i, j, keep;\n'
               '    for (i = 0; i < menuArr.length; i++) {\n'
               '        keep = true;\n'
               '        for (j = 0; j < hide.length; j++) {\n'
               '            if (menuArr[i].indexOf(\'id="\' + hide[j] + \'"\') >= 0) keep = false;\n'
               '        }\n'
               '        if (keep) out.push(menuArr[i]);\n'
               '    }\n'
               '    menuArr = out;\n'
               '    // header: "Pace v5471 Router" / "Pace v5471 Access Point" by mode\n'
               '    function title() {\n'
               '        var sp = document.getElementsByTagName("span"), k;\n'
               '        for (k = 0; k < sp.length; k++) if (/(^| )ni-logo( |$)/.test(sp[k].className))\n'
               f'            sp[k].innerHTML = mode == "Router" ? "{PRODUCT}" : "{PRODUCT_AP}";\n'
               '    }\n'
               '    if (document.addEventListener) document.addEventListener("DOMContentLoaded", title, false);\n'
               '    else if (window.attachEvent) window.attachEvent("onload", title);\n'
               '})();\n')
        # rename Games & Applications (preset port forwarding rules)
        txt = sub1(r"(<li id=\"menu_applications\"><a href=\"config_apps\.htm\"><strong>)[^<]*",
                   lambda m: m.group(1) + labels['menu_applications'], txt, 'menu_applications')
        # reorder the Settings and Management lists; the GVT access-class SSI checks inside them go
        for group, order in MENU_ORDER.items():
            m = re.search(r"(id=\"%s\">',\n\s*'<a class=\"menu-header\"[^\n]*\n(\s*)'<ul class=\"ulmenu\">',\n)(.*?)(\n\s*'</ul>',)"
                          % group, txt, re.S)
            if not m:
                sys.exit(f'menu.js: {group} not found')
            items = {}
            for line in m.group(3).split('\n'):
                s = line.strip()
                if not s or s.startswith('<!--#'):
                    continue
                mm = re.match(r"'<li id=\"(menu_[a-z0-9_]+)\">.*',$", s)
                if not mm:
                    sys.exit(f'menu.js: unexpected line in {group}: {s}')
                items[mm.group(1)] = s
            ind = m.group(2) + '    '
            missing = [i for i in order if i not in items]
            if missing:
                sys.exit(f'menu.js: {group} lacks {missing}')
            lines = [items.pop(i) for i in order] + list(items.values())
            txt = txt[:m.start(3)] + '\n'.join(ind + l for l in lines) + txt[m.end(3):]
        # header language switch: save the choice (the front page and the next visits use it), then
        # switch on the same host (the stock code went to the configured LAN IP)
        lang_fn = ('function changeLanguage(lg) {\n'
                   '    var last = document.URL.lastIndexOf(\'/\');\n'
                   '    var currentPage = document.URL.substring(last+1, document.URL.length);\n'
                   '    var done = false, go = function() { if (!done) { done = true; document.location.href = \'/\' + lg + \'/admin/\' + currentPage; } };\n'
                   '    try {\n'
                   '        var tok = eval(\'(<!--#echo jsonvar="token=Services_IADConfigurator_CurrentLanguage"-->)\');\n'
                   '        ConfigAccess(tok).rollback().write("Services_IADConfigurator_CurrentLanguage", lg).commit(go, go);\n'
                   '        setTimeout(go, 3000);\n'
                   '    } catch (e) { go(); }\n'
                   '}\n')
        # the stock closing brace has trailing spaces: stop there, not at the next function's end
        txt = sub1(r'function changeLanguage\(lg\) \{\n.*?\n\}[ \t]*\n', lambda m: lang_fn, txt, 'menu changeLanguage', flags=re.S)
        for f in ('function toggleMenuItem(', 'function initMenu(', 'function ImportMenu('):
            if f not in txt:
                sys.exit(f'menu.js: {f} lost')
        return sub1(r'(\nvar menuArr = \[\n.*?\n\];\n)', lambda m: m.group(1) + flt + DESC_JS, txt, 'menuArr', flags=re.S)
    return fn


WIFI_TXT = {
    'en_US': {'title': 'Connected devices', 'intro': 'Devices connected to this Wi-Fi network right now (updated every 5 seconds on the router; reload the page to refresh). Isolate limits the device to the Internet; Block adds it to the MAC filter so it can no longer connect; Fixed IP reserves its current address in the DHCP server (Local Network page).',
              'name': 'Device', 'ip': 'IP address', 'mac': 'MAC address', 'mode': 'Wi-Fi mode', 'since': 'Connected',
              'signal': 'Signal', 'rate': 'Rate (tx/rx)', 'actions': 'Actions', 'none': 'No device connected.',
              'block': 'Block', 'fixip': 'Fixed IP', 'reserved': 'reserved', 'excellent': 'excellent', 'good': 'good',
              'fair': 'fair', 'weak': 'weak', 'blocked': 'Device blocked: it is in the MAC filter list (Advanced tab).',
              'removed': 'Device blocked: removed from the allowed devices of the MAC filter (Advanced tab).',
              'fixed': 'Address reserved for this device (Local Network page, DHCP).', 'noip': 'This device has no IP address yet.',
              'already': 'This device already has a reserved address.',
              'aclmode': 'MAC filter mode:', 'aclmode_d': 'Allow: only the devices in the list below can connect. Block: the devices in the list are blocked, all others can connect. Saved at once.',
              'allow': 'Allow only the listed devices', 'deny': 'Block the listed devices', 'modesaved': 'MAC filter mode saved.',
              'isolate': 'Isolate', 'isodef': 'Default for Wi-Fi devices:', 'isodef_allow': 'Allow access to the local network',
              'isodef_iso': 'Isolate from the local network (Internet only)',
              'isodef_d': 'Isolated devices reach only the Internet and the router\'s DNS and DHCP: not the wired computers, not the router\'s settings and not the network on the WAN side. The Isolate switch of each device overrides this default. While any device is isolated, Wi-Fi devices can\'t reach each other either (driver limitation); the wired ones still reach the allowed devices.',
              'isolated': 'Device isolated: it now reaches only the Internet (applied within 5 seconds).',
              'allowed': 'Device allowed on the local network (applied within 5 seconds).', 'isodefsaved': 'Default for Wi-Fi devices saved.',
              'gen': 'Generate', 'pw_short': 'too short (8 characters minimum)', 'pw_weak': 'weak', 'pw_fair': 'fair',
              'pw_good': 'good', 'pw_strong': 'strong', 'pw_gen': 'New random password: save, then reconnect your devices with it.',
              'best': 'best'},
    'pt_BR': {'title': 'Dispositivos conectados', 'intro': 'Dispositivos conectados agora a esta rede Wi-Fi (atualizado a cada 5 segundos no roteador; recarregue a p&aacute;gina para atualizar). Isolar limita o dispositivo &agrave; Internet; Bloquear p&otilde;e o dispositivo no filtro de MAC para que n&atilde;o conecte mais; IP fixo reserva o endere&ccedil;o atual dele no servidor DHCP (p&aacute;gina Rede Local).',
              'name': 'Dispositivo', 'ip': 'Endere&ccedil;o IP', 'mac': 'Endere&ccedil;o MAC', 'mode': 'Modo Wi-Fi', 'since': 'Conectado',
              'signal': 'Sinal', 'rate': 'Taxa (tx/rx)', 'actions': 'A&ccedil;&otilde;es', 'none': 'Nenhum dispositivo conectado.',
              'block': 'Bloquear', 'fixip': 'IP fixo', 'reserved': 'reservado', 'excellent': 'excelente', 'good': 'bom',
              'fair': 'regular', 'weak': 'fraco', 'blocked': 'Dispositivo bloqueado: ele est&aacute; na lista do filtro de MAC (aba Avan&ccedil;ado).',
              'removed': 'Dispositivo bloqueado: removido dos dispositivos permitidos do filtro de MAC (aba Avan&ccedil;ado).',
              'fixed': 'Endere&ccedil;o reservado para este dispositivo (p&aacute;gina Rede Local, DHCP).', 'noip': 'Este dispositivo ainda n&atilde;o tem endere&ccedil;o IP.',
              'already': 'Este dispositivo j&aacute; tem endere&ccedil;o reservado.',
              'aclmode': 'Modo do filtro de MAC:', 'aclmode_d': 'Permitir: s&oacute; os dispositivos da lista abaixo conectam. Bloquear: os dispositivos da lista s&atilde;o bloqueados, os outros conectam. Salvo na hora.',
              'allow': 'Permitir s&oacute; os da lista', 'deny': 'Bloquear os da lista', 'modesaved': 'Modo do filtro de MAC salvo.',
              'isolate': 'Isolar', 'isodef': 'Padr&atilde;o para dispositivos Wi-Fi:', 'isodef_allow': 'Permitir acesso &agrave; rede local',
              'isodef_iso': 'Isolar da rede local (s&oacute; Internet)',
              'isodef_d': 'Dispositivos isolados acessam s&oacute; a Internet e o DNS e DHCP do roteador: n&atilde;o os computadores cabeados, n&atilde;o as configura&ccedil;&otilde;es do roteador e n&atilde;o a rede do lado WAN. A chave Isolar de cada dispositivo substitui este padr&atilde;o. Enquanto algum dispositivo estiver isolado, os dispositivos Wi-Fi tamb&eacute;m n&atilde;o se acessam entre si (limita&ccedil;&atilde;o do driver); os cabeados continuam acessando os permitidos.',
              'isolated': 'Dispositivo isolado: agora acessa s&oacute; a Internet (aplicado em at&eacute; 5 segundos).',
              'allowed': 'Dispositivo liberado na rede local (aplicado em at&eacute; 5 segundos).', 'isodefsaved': 'Padr&atilde;o para dispositivos Wi-Fi salvo.',
              'gen': 'Gerar', 'pw_short': 'curta demais (m&iacute;nimo 8 caracteres)', 'pw_weak': 'fraca', 'pw_fair': 'razo&aacute;vel',
              'pw_good': 'boa', 'pw_strong': 'forte', 'pw_gen': 'Nova senha aleat&oacute;ria: salve e depois reconecte os seus dispositivos com ela.',
              'best': 'melhor'},
}

# Wireless page, Basic tab: connected devices (tetherd writes the stations to /var/status/wifi:
# sta=MAC|RSSI|mode|width|seconds|tx kbps|rx kbps) with Block (MAC filter) and Fixed IP (DHCP
# reservation) buttons; Advanced tab: the MAC filter mode (WLANInterface_1_ACLMode allow/deny)
WIFI_HTML = r"""
<table class="setupWifiTable" id="niWifiClients">
<thead><tr><th colspan="9">%(title)s</th></tr></thead>
<tbody>
<tr><td colspan="9" class="ni-desc-row">%(intro)s</td></tr>
<tr><td colspan="9" class="ni-isodef">%(isodef)s <select id="niIsoDef" style="width:auto"><option value="0">%(isodef_allow)s</option><option value="1">%(isodef_iso)s</option></select>
<br/><small>%(isodef_d)s</small></td></tr>
<tr class="ni-head"><td>%(name)s</td><td>%(ip)s</td><td>%(mac)s</td><td>%(mode)s</td><td>%(since)s</td><td>%(signal)s</td><td>%(rate)s</td><td>%(isolate)s</td><td>%(actions)s</td></tr>
</tbody>
<tbody id="niWifiList"><tr><td colspan="9">-</td></tr></tbody>
</table>
<pre id="niWifiRaw" style="display:none"><!--#include file="wifi.inc" --></pre>
<script type="text/javascript">
var NiWifi = (function() {
    function el(id) { return document.getElementById(id); }
    function esc(v) { return String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
    function cli(s) { try { return eval("(" + s + ")"); } catch (e) { return undefined; } }
    var token = cli('<!--#echo jsonvar="token=LANDevice,WLANInterface,Device_WiFiIsolateDefault,Device_WiFiIsolate"-->');
    // isolation (lib/ni-guard): default 0/1 and per-device exceptions "mac=1,mac=0"
    var isoDef = cli('<!--#echo jsonvar="cli=Device_WiFiIsolateDefault"-->') == "1" ? "1" : "0";
    var isoList = cli('<!--#echo jsonvar="cli=Device_WiFiIsolate"-->') || "";
    var hosts = cli('<!--#echo jsonvar="cli=LANDevice_1_Hosts"-->') || {};
    var resv = cli('<!--#echo jsonvar="cli=LANDevice_1_HostConfig_ClientTable"-->') || {};
    var acl = cli('<!--#echo jsonvar="cli=LANDevice_1_AccessControl"-->') || {};
    var aclOn = cli('<!--#echo jsonvar="cli=WLANInterface_1_ACLEnable"-->'), aclMode = cli('<!--#echo jsonvar="cli=WLANInterface_1_ACLMode"-->') || "allow";
    var sta = [];
    function msg(kind, m) { try { App.MessageUtil.clearAll(); App.MessageUtil[kind](m); } catch (e) {} }
    function list(o) { return (o.List || "").split(",").filter ? (o.List || "").split(",").filter(function(x) { return x; }) : []; }
    function byMac(o, mac) {
        var l = list(o), i;
        for (i = 0; i < l.length; i++) if (o[l[i]] && (o[l[i]].MACAddress || "").toLowerCase() == mac) return l[i];
        return null;
    }
    function isoMap() {
        var m = {}, l = isoList.split(","), i, p;
        for (i = 0; i < l.length; i++) {
            p = l[i].split("=");
            if (p.length == 2 && /^([0-9a-f]{2}:){5}[0-9a-f]{2}$/.test(p[0].toLowerCase()) && (p[1] == "0" || p[1] == "1")) m[p[0].toLowerCase()] = p[1];
        }
        return m;
    }
    function isIso(mac) { var m = isoMap(); return (m.hasOwnProperty(mac) ? m[mac] : isoDef) == "1"; }
    function host(mac) {
        for (var i = 1; i <= (+hosts.Count || 0); i++) if (hosts[i] && (hosts[i].MACAddress || "").toLowerCase() == mac) return hosts[i];
        return {};
    }
    function dur(s) {
        s = +s || 0; var d = Math.floor(s / 86400), h = Math.floor(s %% 86400 / 3600), m = Math.floor(s %% 3600 / 60);
        return (d ? d + "d " : "") + (d || h ? h + "h " : "") + m + "min";
    }
    function since(s) {
        var t = new Date(new Date().getTime() - (+s || 0) * 1000), p = function(n) { return (n < 10 ? "0" : "") + n; };
        return p(t.getDate()) + "/" + p(t.getMonth() + 1) + " " + p(t.getHours()) + ":" + p(t.getMinutes());
    }
    function quality(r) {
        r = +r;
        if (!r) return "-";
        return r + " dBm (" + (r >= -55 ? "%(excellent)s" : r >= -67 ? "%(good)s" : r >= -75 ? "%(fair)s" : "%(weak)s") + ")";
    }
    function render() {
        var raw = (el("niWifiRaw").innerHTML || "").split("\n"), i, m, f, h = "";
        sta = [];
        for (i = 0; i < raw.length; i++) {
            m = /^sta=(.*)$/.exec(raw[i].replace(/^\s+|\s+$/g, ""));
            if (m) { f = m[1].split("|"); sta.push({ mac: (f[0] || "").toLowerCase(), rssi: f[1], mode: f[2], width: f[3], secs: f[4], tx: f[5], rx: f[6] }); }
        }
        for (i = 0; i < sta.length; i++) {
            var s = sta[i], ho = host(s.mac), res = byMac(resv, s.mac);
            h += "<tr><td>" + esc(ho.Hostname || "-") + "</td><td>" + esc(ho.IPAddress || "-") + "</td><td>" + esc(s.mac) + "</td>" +
                "<td>802.11" + esc(s.mode || "?") + (s.mode == "n" && s.width ? " (" + esc(s.width) + " MHz)" : "") + "</td>" +
                "<td>" + dur(s.secs) + "<br/><small>" + since(s.secs) + "</small></td><td>" + quality(s.rssi) + "</td>" +
                "<td>" + (s.tx ? Math.round(s.tx / 1000) : "-") + " / " + (s.rx ? Math.round(s.rx / 1000) : "-") + " Mbps</td>" +
                '<td><label class="ni-switch"><input type="checkbox" onclick="NiWifi.iso(' + i + ')"' + (isIso(s.mac) ? ' checked="checked"' : "") + ' /><span></span></label></td>' +
                '<td style="white-space:nowrap"><a class="btn-default-orange-small" onclick="NiWifi.block(' + i + ')"><span>%(block)s</span></a> ' +
                (res ? "<small>%(reserved)s</small>" : '<a class="btn-default-orange-small" onclick="NiWifi.fix(' + i + ')"><span>%(fixip)s</span></a>') + "</td></tr>";
        }
        el("niWifiList").innerHTML = h || '<tr><td colspan="9">%(none)s</td></tr>';
    }
    function next(o, base) {
        var l = list(o), mx = base, i;
        for (i = 0; i < l.length; i++) if (+l[i] > mx) mx = +l[i];
        return mx + 1;
    }
    function block(i) {
        var s = sta[i], c = ConfigAccess(token).rollback(), idx = byMac(acl, s.mac), done;
        if (aclOn == "1" && aclMode != "deny") {
            // allow list: drop the device from it
            if (idx) c.remove("LANDevice_1_AccessControl_" + idx);
            done = "%(removed)s";
        } else {
            if (aclOn != "1") { c.write("WLANInterface_1_ACLEnable", "1"); c.write("WLANInterface_1_ACLMode", "deny"); }
            if (!idx) {
                idx = next(acl, 0);
                c.create("LANDevice_1_AccessControl_" + idx);
                c.write("LANDevice_1_AccessControl_" + idx + "_MACAddress", s.mac);
                c.write("LANDevice_1_AccessControl_" + idx + "_ClientName", host(s.mac).Hostname || s.mac);
                c.write("LANDevice_1_AccessControl_" + idx + "_Enable", "1");
            }
            done = "%(blocked)s";
        }
        c.commit(function(res) { if (res.error) msg("error", res.error); else msg("info", done); });
    }
    function fix(i) {
        var s = sta[i], ho = host(s.mac);
        if (!ho.IPAddress) { msg("error", "%(noip)s"); return; }
        if (byMac(resv, s.mac)) { msg("info", "%(already)s"); return; }
        var idx = next(resv, 1000), P = "LANDevice_1_HostConfig_ClientTable_" + idx + "_";
        ConfigAccess(token).rollback().create("LANDevice_1_HostConfig_ClientTable_" + idx)
            .write(P + "IPAddress", ho.IPAddress).write(P + "MACAddress", s.mac).write(P + "Hostname", ho.Hostname || "")
            .write(P + "User", "1").commit(function(res) {
                if (res.error) { msg("error", res.error); return; }
                resv[idx] = { MACAddress: s.mac }; resv.List = (resv.List ? resv.List + "," : "") + idx;
                render(); msg("info", "%(fixed)s");
            });
    }
    function iso(i) {
        var s = sta[i], m = isoMap(), want = isIso(s.mac) ? "0" : "1", k, out = [];
        if (want == isoDef) delete m[s.mac]; else m[s.mac] = want;
        for (k in m) if (m.hasOwnProperty(k)) out.push(k + "=" + m[k]);
        var nl = out.join(",");
        ConfigAccess(token).rollback().write("Device_WiFiIsolate", nl).commit(function(res) {
            if (res.error) { msg("error", res.error); render(); return; }
            isoList = nl; render(); msg("info", want == "1" ? "%(isolated)s" : "%(allowed)s");
        });
    }
    function isodef() {
        var v = el("niIsoDef").value;
        ConfigAccess(token).rollback().write("Device_WiFiIsolateDefault", v).commit(function(res) {
            if (res.error) { msg("error", res.error); return; }
            isoDef = v; render(); msg("info", "%(isodefsaved)s");
        });
    }
    function mode() {
        var v = el("niAclMode").value;
        ConfigAccess(token).rollback().write("WLANInterface_1_ACLMode", v).commit(function(res) {
            if (res.error) { msg("error", res.error); return; }
            aclMode = v; msg("info", "%(modesaved)s");
        });
    }
    if (el("niAclMode")) { el("niAclMode").value = aclMode == "deny" ? "deny" : "allow"; el("niAclMode").onchange = mode; }
    el("niIsoDef").value = isoDef; el("niIsoDef").onchange = isodef;
    render();
    return { block: block, fix: fix, iso: iso };
})();
</script>"""

# Wi-Fi password: strength meter (rough entropy: length x character classes, capped for
# repeats / common sequences) and a random password generator (crypto.getRandomValues)
PW_TOOL = r"""
                                    <a class="btn-default-orange-small ni-pwgen" id="niPwGen"><span>%(gen)s</span></a><br/>
                                    <span class="ni-pw"><span id="niPwBar"></span></span> <small id="niPwTxt"></small>
<script type="text/javascript">
(function() {
    var f = document.getElementById("%(field)s"), f2 = document.getElementById("%(confirm)s"), bar = document.getElementById("niPwBar"),
        t = document.getElementById("niPwTxt"), last = null;
    var A = "ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789";
    function bits(p) {
        var pool = 0, b;
        if (/[a-z]/.test(p)) pool += 26;
        if (/[A-Z]/.test(p)) pool += 26;
        if (/[0-9]/.test(p)) pool += 10;
        if (/[^a-zA-Z0-9]/.test(p)) pool += 33;
        b = pool ? p.length * Math.log(pool) / Math.LN2 : 0;
        if (/^(.)\1*$/.test(p)) b = Math.min(b, 8);
        if (/0123|1234|2345|3456|4567|5678|6789|abcd|qwer|asdf|senha|password|admin|wifi/i.test(p)) b = Math.min(b, 30);
        return b;
    }
    function show() {
        var p = f.value || "", b = bits(p), lv;
        if (p === last) return;
        last = p;
        if (!p) { bar.style.width = "0"; t.innerHTML = ""; return; }
        lv = p.length < 8 ? ["#c0392b", 10, "%(pw_short)s"] : b < 45 ? ["#c0392b", 25, "%(pw_weak)s"] : b < 60 ? ["#e67e22", 50, "%(pw_fair)s"] :
            b < 80 ? ["#9bbf2a", 75, "%(pw_good)s"] : ["#27ae60", 100, "%(pw_strong)s"];
        bar.style.width = lv[1] + "%%"; bar.style.backgroundColor = lv[0];
        t.innerHTML = lv[2] + " (~" + Math.round(b) + " bits)";
    }
    function gen() {
        var out = "", r = new Uint8Array(64), i, c = window.crypto || window.msCrypto;
        // 16 characters with letters and digits (the account page requires both)
        while (out.length < 16 || !/[0-9]/.test(out) || !/[a-zA-Z]/.test(out)) {
            if (out.length >= 16) out = "";
            if (c && c.getRandomValues) c.getRandomValues(r); else for (i = 0; i < r.length; i++) r[i] = Math.floor(Math.random() * 256);
            for (i = 0; i < r.length && out.length < 16; i++) if (r[i] < 228) out += A.charAt(r[i] %% A.length);
        }
        f.value = out;
        if (f2) f2.value = out;
        try { var e = document.createEvent("HTMLEvents"); e.initEvent("change", true, true); f.dispatchEvent(e); } catch (x) {}
        show();
        try { App.MessageUtil.clearAll(); App.MessageUtil.info("%(pw_gen)s".replace("{pw}", out)); } catch (x) {}
    }
    document.getElementById("niPwGen").onclick = gen;
    f.onkeyup = show;
    setInterval(show, 500);
})();
</script>"""


def pw_tool(s, field, confirm, gen_msg):
    """strength meter + random password generator after the input `field` (and its `confirm` copy)"""
    return PW_TOOL % dict(s, field=field, confirm=confirm, pw_gen=gen_msg)


WIFI_MODE_ROW = r"""
                            <tr id="niAclModeRow">
                                <td>%(aclmode)s<small class="ni-desc">%(aclmode_d)s</small></td>
                                <td><select id="niAclMode" style="width:auto"><option value="allow">%(allow)s</option><option value="deny">%(deny)s</option></select></td>
                            </tr>"""


def wireless(lang):
    s = WIFI_TXT[lang]

    def fn(txt):
        txt = sub1(r'(<tr id="MACFiltering">.*?</tr>)', lambda m: m.group(1) + WIFI_MODE_ROW % s, txt, 'wireless MAC filter mode',
                   flags=re.S)
        txt = sub1(r'<input type="text" id="wirelessPassword" />',
                   lambda m: m.group(0) + pw_tool(s, 'wirelessPassword', '', s['pw_gen']), txt, 'wireless password')
        return sub1(r'(<div id="tab-01" class="tab">.*?</table>)', lambda m: m.group(1) + WIFI_HTML % s, txt,
                    'wireless clients table', flags=re.S)
    return fn


def wifi_js(lang):
    # security mode list: WPA2 first and marked best (WPA/WPA2 mixed allows TKIP clients)
    best = WIFI_TXT[lang]['best']

    def fn(txt):
        return sub1(r"'<option value=\"WPA-Auto\">WPA/WPA2</option>',(\n\s*)'<option value=\"WPA2\">WPA2</option>',",
                    lambda m: "'<option value=\"WPA2\">WPA2 (%s)</option>',%s'<option value=\"WPA-Auto\">WPA/WPA2</option>'," % (best, m.group(1)),
                    txt, 'wireless js WPA2 option', count=4)
    return fn


ACCOUNT_TXT = {
    'en_US': {'title': 'Shell access (SSH / Telnet)', 'intro': 'Command line access to the router for maintenance, from the local network only (never from the Internet). User name <b>shell</b>, with its own password, separate from this web interface\'s. Off by default.',
              'ssh_d': 'Encrypted remote shell (port 22). The router has its own host key, made the first time SSH is turned on.',
              'telnet_d': 'Unencrypted remote shell (port 23): the password crosses the network in clear text. Not recommended.',
              'user': 'User name:', 'user_d': 'Log in with this name (full administrator rights).',
              'pw': 'Shell password:', 'pw_d': 'At least 8 characters. Leave empty to keep the current one.', 'pw2': 'Shell password (confirm):',
              'save': 'Save', 'set': 'A password is set.', 'unset': 'No password yet: SSH and Telnet can\'t be turned on until you set one.',
              'need': 'Set a shell password first.', 'short': 'The shell password must have at least 8 characters.',
              'nomatch': 'The shell passwords don\'t match.', 'saved': 'Shell access saved.', 'fp': 'Host key fingerprint:',
              'factory': 'You are using the factory password (admin). Please set a new password before continuing.',
              'lock': ' After 5 wrong attempts, login is blocked for 30 minutes.',
              'pw_gen_admin': 'New password: <b>{pw}</b> (also typed in the confirm field). Write it down, then click Save.'},
    'pt_BR': {'title': 'Acesso ao shell (SSH / Telnet)', 'intro': 'Acesso de linha de comando ao roteador para manuten&ccedil;&atilde;o, s&oacute; pela rede local (nunca pela Internet). Usu&aacute;rio <b>shell</b>, com senha pr&oacute;pria, separada da desta interface web. Desligado por padr&atilde;o.',
              'ssh_d': 'Shell remoto criptografado (porta 22). O roteador tem chave pr&oacute;pria, criada na primeira vez que o SSH &eacute; ligado.',
              'telnet_d': 'Shell remoto sem criptografia (porta 23): a senha passa pela rede em texto puro. N&atilde;o recomendado.',
              'user': 'Usu&aacute;rio:', 'user_d': 'Entre com este nome (direitos completos de administrador).',
              'pw': 'Senha do shell:', 'pw_d': 'Pelo menos 8 caracteres. Deixe vazio para manter a atual.', 'pw2': 'Senha do shell (confirmar):',
              'save': 'Salvar', 'set': 'H&aacute; uma senha definida.', 'unset': 'Sem senha ainda: SSH e Telnet s&oacute; podem ser ligados depois de definir uma.',
              'need': 'Defina antes uma senha para o shell.', 'short': 'A senha do shell deve ter pelo menos 8 caracteres.',
              'nomatch': 'As senhas do shell n&atilde;o conferem.', 'saved': 'Acesso ao shell salvo.', 'fp': 'Impress&atilde;o digital da chave:',
              'factory': 'Voc&ecirc; est&aacute; usando a senha de f&aacute;brica (admin). Defina uma nova senha antes de continuar.',
              'lock': ' Depois de 5 tentativas erradas, o login fica bloqueado por 30 minutos.',
              'pw_gen_admin': 'Nova senha: <b>{pw}</b> (tamb&eacute;m digitada na confirma&ccedil;&atilde;o). Anote e depois clique em Salvar.'},
}

# Account settings: shell user (User_2 "shell", password Device_ShellPassword) and the SSH / Telnet switches; the
# notice when logged in with the factory password
ACCOUNT_HTML = r"""
<p id="niFactory" class="ni-warn" style="display:none">%(factory)s</p>
<table class="setupWifiTable" cellspacing="0" cellpadding="0" id="niShell">
<thead><tr><th colspan="2" class="upper">%(title)s</th></tr></thead>
<tbody>
<tr class="header"><td colspan="2">%(intro)s</td></tr>
<tr><td class="firstChild">SSH:<small class="ni-desc">%(ssh_d)s</small></td>
    <td><label class="ni-switch"><input type="checkbox" id="niSsh" /><span></span></label> <small id="niFp"></small></td></tr>
<tr><td class="firstChild">Telnet:<small class="ni-desc">%(telnet_d)s</small></td>
    <td><label class="ni-switch"><input type="checkbox" id="niTelnet" /><span></span></label></td></tr>
<tr><td class="firstChild">%(user)s<small class="ni-desc">%(user_d)s</small></td><td><b>shell</b></td></tr>
<tr><td class="firstChild">%(pw)s<small class="ni-desc">%(pw_d)s</small></td>
    <td><input type="password" id="niShellPw" value="" /><br/><small id="niShellState"></small></td></tr>
<tr><td class="firstChild">%(pw2)s</td><td><input type="password" id="niShellPw2" value="" /></td></tr>
</tbody>
<tfoot><tr><td colspan="2"><a class="btn-default-orange-small right" id="niShellSave"><span>%(save)s</span></a></td></tr></tfoot>
</table>
<pre id="niSshKey" style="display:none"><!--#include file="sshkey.inc" --></pre>
<script type="text/javascript">
var NiShell = (function() {
    function el(id) { return document.getElementById(id); }
    function cli(s) { try { return eval("(" + s + ")"); } catch (e) { return undefined; } }
    var token = cli('<!--#echo jsonvar="token=Services_SSH,Services_Telnet,Device_ShellPassword"-->');
    var ssh = cli('<!--#echo jsonvar="cli=Services_SSH_Enable"-->'), tel = cli('<!--#echo jsonvar="cli=Services_Telnet_Enable"-->');
    var hasPw = !!cli('<!--#echo jsonvar="cli=Device_ShellPassword"-->');
    function msg(kind, m) { try { App.MessageUtil.clearAll(); App.MessageUtil[kind](m); } catch (e) {} }
    function state() {
        el("niShellState").innerHTML = hasPw ? "%(set)s" : "%(unset)s";
        var fp = /fingerprint=(\S+)/.exec(el("niSshKey").innerHTML || "");
        el("niFp").innerHTML = fp && el("niSsh").checked ? "%(fp)s " + fp[1] : "";
    }
    function save() {
        var pw = el("niShellPw").value, pw2 = el("niShellPw2").value, s = el("niSsh").checked ? "1" : "0", t = el("niTelnet").checked ? "1" : "0";
        if (pw && pw.length < 8) { msg("error", "%(short)s"); return; }
        if (pw != pw2) { msg("error", "%(nomatch)s"); return; }
        if ((s == "1" || t == "1") && !hasPw && !pw) { msg("error", "%(need)s"); return; }
        var c = ConfigAccess(token).rollback().write({ "Services_SSH_Enable": s, "Services_Telnet_Enable": t });
        if (pw) c.encrypt("Device_ShellPassword", pw);
        c.commit(function(res) {
            if (res.error) { msg("error", res.error); return; }
            if (pw) hasPw = true;
            el("niShellPw").value = ""; el("niShellPw2").value = "";
            state(); msg("info", "%(saved)s");
        });
    }
    el("niSsh").checked = ssh == "1"; el("niTelnet").checked = tel == "1";
    el("niShellSave").onclick = save;
    try { if (sessionStorage.getItem("niDefaultPw") == "1") el("niFactory").style.display = ""; } catch (e) {}
    state();
    return { save: save };
})();
</script>"""


def account(lang):
    s = ACCOUNT_TXT[lang]

    def fn(txt):
        w = WIFI_TXT[lang]
        txt = sub1(r'<input  id="changePass" type="password" name="radio1" value="" />',
                   lambda m: m.group(0) + pw_tool(w, 'changePass', 'changeConfirmPass', s['pw_gen_admin']), txt, 'account password tool')
        return sub1(r'(</table>\s*\n\s*</div><!--col-722-->)', lambda m: '</table>\n' + ACCOUNT_HTML % s + '\n' + m.group(1)[len('</table>'):],
                    txt, 'account shell section')
    return fn


def account_js(lang):
    # password changed: the factory password notice / redirect (menu.js) ends
    def fn(txt):
        return sub1(r"(\n(\s*)Messages\.info\('(Successfully changed password|Senha alterada com sucesso)'\);)",
                    lambda m: m.group(1) + '\n' + m.group(2) + 'try { sessionStorage.removeItem("niDefaultPw"); document.getElementById("niFactory").style.display = "none"; } catch (e) {}',
                    txt, 'admin_password js success')
    return fn


AUTH_ENTER = '''
(function() {
    function key(e) {
        e = e || window.event;
        if ((e.keyCode || e.which) != 13) return true;
        if (e.preventDefault) e.preventDefault();
        if (checkSubmit()) document.login_form.submit();
        return false;
    }
    var u = document.getElementById("login"), p = document.getElementById("password");
    if (u) u.onkeydown = key;
    if (p) p.onkeydown = key;
})();'''


def auth(lang):
    s = ACCOUNT_TXT[lang]

    def fn(txt):
        # login lockout (Services_IADConfigurator MaxTry 5 / TryDelay 1800 s, in the ssi CGI): say so
        txt = sub1(r"(document\.getElementById\('errorMsg'\)\.innerHTML ='[^']*)'", lambda m: m.group(1) + s['lock'] + "'", txt, 'auth error lockout')
        # Enter in the user or password field logs in (stock: keypress on the password field only, did nothing)
        txt = sub1(r' onkeypress="actionOnEnter\(event\);"', '', txt, 'auth onkeypress')
        txt = sub1(r'(\n</script>\s*)$', lambda m: AUTH_ENTER + m.group(1), txt, 'auth enter')
        # factory password: remembered for this browser session, menu.js sends to Account settings
        return sub1(r'(\n(\s*)encrypt_form\(lVal, pVal, level_auth, elm\.value\);)', lambda m: m.group(1) + '\n' + m.group(2) +
                    'try { if (pVal == "admin") sessionStorage.setItem("niDefaultPw", "1"); else sessionStorage.removeItem("niDefaultPw"); } catch (e) {}',
                    txt, 'auth factory password')
    return fn


LOG_ORDER = {'en_US': ('Newest first', 'Oldest first'), 'pt_BR': ('Mais recentes primeiro', 'Mais antigos primeiro')}


def logread_js(txt):
    # System Logs: order selector (#logOrder), newest first by default; the log buffer is in
    # arrival order, the real time order even across the 2009 boot clock
    txt = sub1(r'(\nvar Page = \(function\(\$, App\) \{)', lambda m:
               '\n// cyberponk: log order\nfunction niOrder(r) {\n    r = (r || []).slice(0);\n'
               '    var o = document.getElementById("logOrder");\n    if (!o || o.value != "old") r.reverse();\n    return r;\n}\n' +
               m.group(1), txt, 'logread niOrder')
    txt = sub1(r'records = recs\.slice\(0\) \|\| \[\],', 'records = niOrder(recs),', txt, 'logread paginator records')
    txt = sub1(r'records = \(recs \|\| \[\]\)\.slice\(0\);', 'records = niOrder(recs);', txt, 'logread setRecords')
    return sub1(r'(\n(\s*)\$\("#logLevel"\)\.bind\("change", showLogs\);)',
                lambda m: m.group(1) + '\n' + m.group(2) + '$("#logOrder").bind("change", showLogs);', txt, 'logread order bind')


def logread_htm(lang):
    new, old = LOG_ORDER[lang]

    def fn(txt):
        return sub1(r'(<select id="logLevel">.*?</select>)', lambda m: m.group(1) +
                    '\n                                <select id="logOrder" style="width:auto"><option value="new">%s</option>'
                    '<option value="old">%s</option></select>' % (new, old), txt, 'logread order select', flags=re.S)
    return fn


FW_TXT = {
    'en_US': {'ok': 'Firmware written. The device is restarting with the new version; this takes about 2 minutes. '
                    'Reload this page afterwards.',
              'fail': 'The firmware was not written (see the messages below). The device keeps the current version.',
              'none': 'No result from fwburn in the log. Check the messages below; restart the device from Reset '
                      'only if they end with "operation successful".',
              'never': 'Not checked yet.', 'checking': 'Checking GitHub...',
              'uptodate': 'Up to date: {v} is the latest version.',
              'available': 'New version available: {v} (published {d}). Current: {c}.',
              'error': 'Error: ', 'rebooting': 'Firmware written. The device is restarting with the new version; '
              'this takes about 2 minutes. Reload this page afterwards.',
              'timeout': 'no answer from the device; check again later.',
              'confirm': 'Download version {v} from GitHub, write it to the flash and restart the device?',
              'steps': {'downloading': 'Downloading the new version...', 'checking the image': 'Checking the image...',
                        'writing to flash (do not power off)': 'Writing to the flash, do not power off...'},
              'h': 'Online Update', 'src': 'Source:',
              'src_d': 'Releases of the project on GitHub, downloaded over HTTPS with certificate checks; fwburn checks '
                       'the image (checksum, hardware) before it is written to the other flash bank.',
              'state': 'Status:', 'notes': 'Release notes:', 'check': 'Check for update', 'install': 'Install'},
    'pt_BR': {'ok': 'Firmware gravada. O aparelho está reiniciando com a nova versão; isso leva cerca de 2 minutos. '
                    'Depois recarregue esta página.',
              'fail': 'A firmware não foi gravada (veja as mensagens abaixo). O aparelho continua com a versão atual.',
              'none': 'Nenhum resultado do fwburn no log. Veja as mensagens abaixo; reinicie o aparelho em Reset '
                      'somente se terminarem com "operation successful".',
              'never': 'Ainda não verificado.', 'checking': 'Consultando o GitHub...',
              'uptodate': 'Atualizado: {v} é a versão mais recente.',
              'available': 'Nova versão disponível: {v} (publicada em {d}). Atual: {c}.',
              'error': 'Erro: ', 'rebooting': 'Firmware gravada. O aparelho está reiniciando com a nova versão; '
              'isso leva cerca de 2 minutos. Depois recarregue esta página.',
              'timeout': 'sem resposta do aparelho; verifique novamente mais tarde.',
              'confirm': 'Baixar a versão {v} do GitHub, gravá-la na flash e reiniciar o aparelho?',
              'steps': {'downloading': 'Baixando a nova versão...', 'checking the image': 'Verificando a imagem...',
                        'writing to flash (do not power off)': 'Gravando na flash, não desligue o aparelho...'},
              'h': 'Atualização Online', 'src': 'Origem:',
              'src_d': 'Versões publicadas do projeto no GitHub, baixadas por HTTPS com verificação de certificado; o '
                       'fwburn verifica a imagem (checksum, hardware) antes de gravá-la no outro banco da flash.',
              'state': 'Estado:', 'notes': 'Notas da versão:', 'check': 'Verificar atualização', 'install': 'Instalar'},
}

# online update source (scripts/fwupdate has the same name)
FW_REPO = 'cyberponk/pace-v5471-router-GVT-firmware'

FW_ONLINE_HTML = '''
<table class="setupWifiTable" id="niOnline" style="margin-top:20px">
	<thead>
		<tr><th colspan="2">%(h)s</th></tr>
	</thead>
	<tbody>
		<tr>
			<td width="200">%(src)s<small class="ni-desc">%(src_d)s</small></td>
			<td><a href="https://github.com/%(repo)s/releases" target="_blank">github.com/%(repo)s</a></td>
		</tr>
		<tr>
			<td>%(state)s</td>
			<td id="niUpState"></td>
		</tr>
		<tr id="niUpNotesRow" style="display:none">
			<td>%(notes)s</td>
			<td><pre id="niUpNotes" style="white-space:pre-wrap; margin:0"></pre></td>
		</tr>
	</tbody>
	<tfoot>
		<tr>
			<td colspan="2"><a id="niUpInstall" class="btn-default-orange-small right" style="display:none; margin-left:10px" onclick="fwOnline('install')"><span>%(install)s</span></a><a id="niUpCheck" class="btn-default-orange-small right" onclick="fwOnline('check')"><span>%(check)s</span></a></td>
		</tr>
	</tfoot>
</table>
<pre id="niUpRaw" style="display:none"><!--#include file="fwupdate.inc" --></pre>
'''

FW_ONLINE_JS = r'''
// online update: Device_FwUpdate = "check.<n>" / "install.<n>" starts scripts/fwupdate, which writes
// /var/status/fwupdate ("key: value" lines, "state:" when done), polled through fwupdate_log.htm
var gUpTok = null, gUpPoll = null, gUpLatest = '';
function upEsc(s) { return String(s).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function upParse(t)
{
	var r = { notes: [] }, ls = String(t || '').split('\n'), i, m;
	for (i = 0; i < ls.length; i++) {
		m = ls[i].match(/^(id|current|latest|date|state|step|error|notes): ?(.*)$/);
		if (!m) continue;
		if (m[1] == 'notes') r.notes.push(m[2]); else r[m[1]] = m[2];
	}
	return r;
}
function upShow(r)
{
	var T = gFwTxt, s, st = r.state, el = function(i) { return document.getElementById(i); };
	if (!r.id) s = T.never;
	else if (!st) s = (r.step && T.steps[r.step]) || T.checking;
	else if (st == 'uptodate') s = T.uptodate.replace('{v}', r.current || '');
	else if (st == 'available') s = T.available.replace('{v}', r.latest || '').replace('{d}', r.date || '-').replace('{c}', r.current || '');
	else if (st == 'rebooting') s = T.rebooting;
	else s = T.error + (r.error || st);
	el('niUpState').innerHTML = upEsc(s);
	el('niUpState').style.color = st == 'error' ? '#a12c1f' : (st == 'available' || st == 'rebooting') ? '#1d6b33' : '';
	var notes = st == 'available' ? r.notes.join('\n').replace(/\s+$/, '') : '';
	el('niUpNotes').innerHTML = upEsc(notes);
	el('niUpNotesRow').style.display = notes ? '' : 'none';
	gUpLatest = st == 'available' ? r.latest : '';
	el('niUpInstall').style.display = gUpLatest ? '' : 'none';
	el('niUpCheck').style.display = (r.id && !st) || st == 'rebooting' ? 'none' : '';
}
function fwOnline(a)
{
	if (gUpPoll || !gUpTok) return;
	if (a == 'install' && !confirm(gFwTxt.confirm.replace('{v}', gUpLatest))) return;
	var id = a + '.' + new Date().getTime(), n = 0;
	ConfigAccess(gUpTok).write('Device_FwUpdate', id).commit(function(res) {
		if (res && res.error) { upShow({ id: id, state: 'error', error: res.error, notes: [] }); return; }
		upShow({ id: id, notes: [] });
		gUpPoll = setInterval(function() {
			var x = new XMLHttpRequest();
			x.onreadystatechange = function() {
				if (x.readyState != 4 || !gUpPoll) return;
				var r = upParse(x.status == 200 ? x.responseText : '');
				if (r.id == id) upShow(r);
				// done, or 20 minutes without a result (a download can take a while)
				if ((r.id == id && r.state) || ++n > 600) {
					clearInterval(gUpPoll); gUpPoll = null;
					if (r.id != id || !r.state) upShow({ id: id, state: 'error', error: gFwTxt.timeout, notes: [] });
				}
			};
			x.open('GET', 'fwupdate_log.htm?t=' + new Date().getTime(), true);
			x.send(null);
		}, 2000);
	});
}
'''


def firmware(lang):
    # Firmware page: firmware.cgi only pipes the upload into fwburn (to the other bank) and never
    # reboots. After the upload the page reads fwburn's log lines again and, when the newest one is
    # a new "operation successful", reboots so the new bank boots.
    t = FW_TXT[lang]

    def fn(txt):
        txt = sub1(r'gToken = null;\n', lambda m: m.group(0) + 'var gReboot = null, gFwNewest = null, gFwLast = null, gFwWait = 0;\n'
                   'var gFwTxt = %s;\n' % json.dumps(t, ensure_ascii=False), txt, 'firmware globals')
        txt = sub1(r"\tlogs = logs.join\('\\n'\);", lambda m: "\tgFwNewest = logs.length ? logs[0] : '';\n" + m.group(0),
                   txt, 'firmware newest line')
        txt = sub1(r"(\te.innerText = logs;\n)", lambda m: m.group(1) + '\tif (gFwWait) fwCheck();\n', txt, 'firmware check hook')
        txt = sub1(r"(\tgToken = pageData.token;\n)", lambda m: m.group(1) +
                   "\tgReboot = util.parseJson('<!--#echo jsonvar=\"token=reboot\"-->');\n"
                   "\tgUpTok = util.parseJson('<!--#echo jsonvar=\"token=Device_FwUpdate\"-->');\n"
                   "\tupShow(upParse(document.getElementById('niUpRaw').innerText));\n", txt, 'firmware online init')
        txt = sub1(r'(\nfunction onFrameLoad\(\)\n)', lambda m: FW_ONLINE_JS + m.group(1), txt, 'firmware online js')
        txt = sub1(r'(\n<div style="display:none" id="divSending">)',
                   lambda m: FW_ONLINE_HTML % dict(t, repo=FW_REPO) + m.group(1), txt, 'firmware online html')
        txt = sub1(r"function onFrameLoad\(\)\n\{\n\tdisplayElement\('divSending', 'none'\);\n\tdisplayElement\('divForm'\);\n\treadLogs\(\);\n\}",
                   '''function fwMsg(s, ok)
{
	var e = document.getElementById('niFwMsg');
	e.className = ok ? 'ni-ok' : 'ni-warn';
	e.innerText = s;
	e.style.display = s ? 'block' : 'none';
}
// newest fwburn line after the upload: a new "operation successful" -> reboot into the new bank
function fwCheck()
{
	var fresh = gFwNewest && gFwNewest != gFwLast;
	if (fresh && / operation successful$/.test(gFwNewest)) {
		gFwWait = 0;
		displayElement('divSending', 'none');
		fwMsg(gFwTxt.ok, true);
		ConfigAccess(gReboot).fct("reboot").commit(function() {}, function() {});
	} else if (gFwWait < 8 && !(fresh && /WARNING|interrupted|can't|Error|error/.test(gFwNewest))) {
		gFwWait++;
		setTimeout(readLogs, 1000);
	} else {
		gFwWait = 0;
		displayElement('divSending', 'none');
		displayElement('divForm');
		fwMsg(fresh ? gFwTxt.fail : gFwTxt.none);
	}
}
function onFrameLoad()
{
	gFwWait = 1;
	readLogs();
}''', txt, 'firmware onFrameLoad')
        txt = sub1(r"(\tdisplayElement\('divForm', 'none'\);\n\tdisplayElement\('divSending'\);\n)",
                   lambda m: "\tgFwLast = gFwNewest;\n\tfwMsg('');\n" + m.group(1), txt, 'firmware send')
        return sub1(r'(<h3 class="text-up">[^<]*</h3>\n)', lambda m: m.group(1) +
                    '\n<p id="niFwMsg" class="ni-warn" style="display:none"></p>\n', txt, 'firmware message')
    return fn


def apps(lang):
    # Games & Applications page: renamed Port Forwarding (it holds preset port forwarding rules)
    title = {'en_US': ('Games & Applications', 'Port Forwarding'), 'pt_BR': ('Jogos ou Aplicativos', 'Redirecionamento de Portas')}[lang]

    def fn(txt):
        return sub1(r'(<h3 class="text-up">)' + re.escape(title[0]) + '<', lambda m: m.group(1) + title[1] + '<', txt, 'config_apps title')
    return fn


def lan_ddns(txt):
    # the DDNS settings have their own page (config_ddns.htm, menu Dynamic DNS): no DDNS tab here.
    # The stock tab content stays, hidden: the stock DynDnsView script binds to its elements.
    txt = sub1(r'\n\s*<li><a href="#" rel="05" class="no-border">DDNS</a></li>', '', txt, 'config_lan DDNS tab')
    return sub1(r'<div id="tab-05" class="tab">', '<div id="tab-05" class="tab" style="display:none !important">', txt,
                'config_lan DDNS tab content')


def lan(txt):
    # "create a reservation" table: 3 columns, but heading and button rows spanned 4 (an empty
    # fourth column made the form rows narrow)
    m = re.search(r'<table class="setupWifiTable">\s*<thead>(?:(?!</table>).)*?id="reservation_Hostname".*?</table>',
                  txt, re.S)
    if not m or m.group(0).count('colspan="4"') != 2:
        sys.exit('config_lan: reservation table not found')
    txt = txt[:m.start()] + m.group(0).replace('colspan="4"', 'colspan="3"') + txt[m.end():]
    # device name / MAC: type, or pick from the connected devices (fills the other fields)
    js = r"""<script type="text/javascript">
(function() {
    var hosts;
    try { hosts = eval('(<!--#echo jsonvar="cli=LANDevice_1_Hosts"-->)'); } catch (e) { return; }
    if (!hosts) return;
    function el(id) { return document.getElementById(id); }
    var list = [], i, h;
    for (i = 1; i <= (+hosts.Count || 0); i++) { h = hosts[i]; if (h && h.MACAddress) list.push(h); }
    function datalist(id, input, key, label) {
        var dl = document.createElement("datalist"), j, o;
        dl.id = id;
        for (j = 0; j < list.length; j++) {
            o = document.createElement("option");
            o.value = list[j][key] || "";
            o.label = list[j][label] || "";
            if (o.value) dl.appendChild(o);
        }
        document.body.appendChild(dl);
        el(input).setAttribute("list", id);
        el(input).setAttribute("autocomplete", "off");
    }
    function pick(key, v) {
        for (var j = 0; j < list.length; j++) {
            if ((list[j][key] || "").toLowerCase() != v.toLowerCase()) continue;
            el("reservation_Hostname").value = list[j].Hostname || "";
            el("reservation_MACAddress").value = list[j].MACAddress;
            var ip = (list[j].IPAddress || "").split(".");
            if (ip.length == 4) for (var k = 0; k < 4; k++) el("reservation_IPAddress" + k).value = ip[k];
            return;
        }
    }
    if (!el("reservation_Hostname") || !el("reservation_MACAddress")) return;
    datalist("niHostNames", "reservation_Hostname", "Hostname", "MACAddress");
    datalist("niHostMacs", "reservation_MACAddress", "MACAddress", "Hostname");
    el("reservation_Hostname").onchange = function() { pick("Hostname", this.value); };
    el("reservation_MACAddress").onchange = function() { pick("MACAddress", this.value); };
})();
</script>
</body>"""
    return sub1(r'</body>', lambda m: js, txt, 'config_lan body')


def about(txt):
    # hardware version: the factory "agilepca" field is empty on these units; tetherd writes
    # model, product code, SoC and loader version to /var/status/hw
    txt = sub1(r'<span id="agilepca"></span>',
               '<span id="agilepca"></span><pre id="ni-hw" style="display:none"><!--#include file="hw.inc" --></pre>',
               txt, 'about agilepca')
    return sub1(r'\$\("#agilepca"\)\.html\(pageData\.agilepca\);',
                lambda m: 'var hw = /hw=(.*)/.exec(document.getElementById("ni-hw").innerHTML);\n'
                          '\t\t\t$("#agilepca").html(hw ? hw[1] : (pageData.agilepca || "-"));', txt, 'about agilepca js')


def dns_js(txt):
    # GVT "captive DNS" check loaded by every page: when the page is not reached through the
    # hostname or the configured static LAN IP (AP mode: DHCP or rescue address 169.254.25.1),
    # it redirects to http://<hostname>/.../wanlink_down.htm, which the PC can't resolve.
    if 'wanlink_down.htm' not in txt:
        sys.exit('dns.js: unexpected content')
    return '// cyberponk: GVT captive DNS redirect disabled\n'


# menu.js is loaded by every admin page: once the page has built its tables, move each setting
# description (small.ni-desc, put under the label by tools/descriptions.py or the ni pages) into a
# last column of its row; other rows of that table get their last cell widened by one column.
DESC_JS = r"""
// cyberponk: setting descriptions in their own column
(function() {
    function move() {
        var tables = document.getElementsByTagName("table"), i, j, k;
        for (i = 0; i < tables.length; i++) {
            var tb = tables[i];
            if (!/(^| )setupWifiTable( |$)/.test(tb.className) || / ni-wide/.test(tb.className)) continue;
            var smalls = tb.getElementsByTagName("small"), has = false;
            for (j = 0; j < smalls.length; j++) if (smalls[j].className == "ni-desc") has = true;
            if (!has) continue;
            tb.className += " ni-wide";
            var rows = tb.rows;
            for (j = 0; j < rows.length; j++) {
                var r = rows[j], found = [], s = r.getElementsByTagName("small");
                for (k = 0; k < s.length; k++) if (s[k].className == "ni-desc") found.push(s[k]);
                if (!r.cells.length) continue;
                if (found.length) {
                    var td = document.createElement("td"), html = [];
                    td.className = "ni-desc-col";
                    for (k = 0; k < found.length; k++) {
                        html.push(found[k].innerHTML);
                        found[k].parentNode.removeChild(found[k]);
                    }
                    td.innerHTML = html.join("<br/><br/>");
                    r.appendChild(td);
                } else {
                    var last = r.cells[r.cells.length - 1];
                    last.colSpan = (last.colSpan || 1) + 1;
                }
            }
        }
    }
    if (window.addEventListener) window.addEventListener("load", move, false);
    else if (window.attachEvent) window.attachEvent("onload", move);
    // logged in with the factory password (auth.htm sets niDefaultPw): Account settings first
    try {
        if (sessionStorage.getItem("niDefaultPw") == "1" && /\/admin\//.test(location.pathname) &&
            !/admin_password\.htm/.test(location.pathname)) location.replace("admin_password.htm");
    } catch (e) {}
})();
"""


def files_txt(txt):
    return sub1(r'config_lan\.htm', 'config_lan.htm ' + ' '.join(NEW_PAGES), txt, 'files.txt', count=1)


ADV_TXT = {'en_US': 'announced on the local network as', 'pt_BR': 'anunciado na rede local como'}


def advanced(lang):
    def fn(txt):
        txt = advanced_rows(txt)
        # mDNS: the name the router is announced under (Device_Hostname.local)
        return sub1(r'(<div class="switchButton" id="Services_MDNSResponder_Enable"[^>]*></div>)', lambda m: m.group(1) +
                    '<span id="niMdnsName" style="margin-left:14px;color:#777;vertical-align:middle;font-size:12px;display:inline"></span>'
                    '<script type="text/javascript">(function() { var h; try { h = eval(\'(<!--#echo jsonvar="cli=Device_Hostname"-->)\'); } catch (e) {}'
                    ' if (h) document.getElementById("niMdnsName").innerHTML = "%s <b>" + String(h).replace(/</g, "&lt;") + ".local</b>"; })();</script>'
                    % ADV_TXT[lang], txt, 'advanced mDNS name')
    return fn


def advanced_rows(txt):
    # rows for removed features: keep the elements (the page binds them), just hide them
    for fid in ('HPNA_Enable', 'Services_TR111_TR111Enable', 'Services_UpnpTracker_Enable',
                'VPNInterface_1_Enable', 'Voice_Enable'):
        txt = sub1(r'<tr>(\s*<td[^>]*>[^<]*</td>\s*<td><div class="switchButton" id="' + fid + '")',
                   r'<tr style="display:none">\1', txt, 'advanced ' + fid)
    return sub1(r'<thead>(\s*<tr><th colspan="2">PTM VLAN</th></tr>\s*</thead>\s*)<tbody>',
                r'<thead style="display:none">\1<tbody style="display:none">', txt, 'advanced PTM')


STATUS_TXT = {
    'en_US': {'title': 'USB tethering', 'settings': 'Settings', 'phone': 'Phone', 'none': 'No phone connected',
              'dhcp': 'Connected, waiting for an address', 'up': 'Connected', 'disabled': 'Connected, failover disabled',
              'usbtitle': 'USB devices', 'nousb': 'No USB device connected', 'tphone': 'phone, USB tethering',
              'tprinter': 'printer', 'tmodem': '3G modem', 'tstorage': 'storage, not supported', 'tother': 'other',
              'ppp': 'PPPoE', 'cdhcp': 'DHCP', 'static': 'Fixed IP', 'connected': 'Connected',
              'disconnected': 'Not connected', 'internet': 'Internet', 'inetok': 'Working', 'inetdown': 'No Internet',
              'via': 'Internet via', 'wan': 'WAN port', 'viaphone': 'USB tethering', 'nonet': 'none',
              'phoneinet': 'Phone Internet', 'clients': 'Clients', 'channel': 'Channel', 'width': 'Bandwidth',
              'power': 'Power', 'half': 'half duplex', 'uplink': 'uplink to the main network', 'gwtag': 'gateway', 'apnote': 'used in router mode only',
              'ddns': 'Dynamic DNS', 'pubip': 'Public IP', 'updating': 'Updating...', 'failed': 'Failed',
              'apconn': 'Access point, address', 'noaddr': 'no address yet', 'gateway': 'gateway',
              'ntp': 'NTP Server', 'now': 'Router time', 'lastsync': 'Last synchronization', 'ok': 'OK',
              'ntpoff': 'synchronization off', 'never': 'not yet',
              'errors': 'There are {n} logged errors that need examination.', 'error1': 'There is 1 logged error that needs examination.',
              'errshow': 'Show', 'errhide': 'Hide', 'errack': 'Mark as examined', 'errdone': 'Marked as examined.'},
    'pt_BR': {'title': 'Ancoragem USB', 'settings': 'Configura&ccedil;&atilde;o', 'phone': 'Celular',
              'none': 'Nenhum celular conectado', 'dhcp': 'Conectado, aguardando endere&ccedil;o', 'up': 'Conectado',
              'disabled': 'Conectado, failover desativado',
              'usbtitle': 'Dispositivos USB', 'nousb': 'Nenhum dispositivo USB conectado',
              'tphone': 'celular, ancoragem USB', 'tprinter': 'impressora', 'tmodem': 'modem 3G',
              'tstorage': 'armazenamento, n&atilde;o suportado', 'tother': 'outro',
              'ppp': 'PPPoE', 'cdhcp': 'DHCP', 'static': 'IP fixo', 'connected': 'Conectado',
              'disconnected': 'Desconectado', 'internet': 'Internet', 'inetok': 'Funcionando',
              'inetdown': 'Sem Internet', 'via': 'Internet via', 'wan': 'porta WAN', 'viaphone': 'Ancoragem USB',
              'nonet': 'nenhuma', 'phoneinet': 'Internet do celular', 'clients': 'Clientes', 'channel': 'Canal',
              'width': 'Largura de banda', 'power': 'Pot&ecirc;ncia', 'half': 'half duplex', 'uplink': 'liga&ccedil;&atilde;o com a rede principal', 'gwtag': 'gateway',
              'apnote': 's&oacute; no modo roteador', 'ddns': 'DNS din&acirc;mico', 'pubip': 'IP p&uacute;blico',
              'updating': 'Atualizando...', 'failed': 'Falhou',
              'apconn': 'Access point, endere&ccedil;o', 'noaddr': 'ainda sem endere&ccedil;o', 'gateway': 'gateway',
              'ntp': 'Servidor NTP', 'now': 'Hora do roteador', 'lastsync': '&Uacute;ltima sincroniza&ccedil;&atilde;o', 'ok': 'OK',
              'ntpoff': 'sincroniza&ccedil;&atilde;o desligada', 'never': 'ainda n&atilde;o',
              'errors': 'H&aacute; {n} erros registrados que precisam ser examinados.', 'error1': 'H&aacute; 1 erro registrado que precisa ser examinado.',
              'errshow': 'Mostrar', 'errhide': 'Ocultar', 'errack': 'Marcar como examinados', 'errdone': 'Marcados como examinados.'},
}

# Status page script: runs on load, after the stock services_status.javascript (DOM-ready) has
# filled its rows. Data: cli= objects and the files tetherd writes (/var/status/*, included).
STATUS_JS = r"""<script type="text/javascript">
(function() {
    function el(id) { return document.getElementById(id); }
    function esc(v) { return String(v).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;"); }
    function trim(v) { return (v || "").replace(/^\s+|\s+$/g, ""); }
    function cli(s) { try { return eval("(" + s + ")"); } catch (e) { return undefined; } }
    // key=value lines of an included status file (a missing file gives the SSI error text)
    function kv(id) {
        var t = {}, l = (el(id) ? el(id).innerHTML : "").split("\n"), i, m;
        for (i = 0; i < l.length; i++) { m = /^([a-z]+)=(.*)$/.exec(trim(l[i])); if (m) t[m[1]] = m[2]; }
        return t;
    }
    function line(id, label, text, ok) {
        var d = el(id);
        d.innerHTML = "<strong>" + label + ":</strong> <span class=\"state\">" + text + "</span>";
        d.className = "status-detail" + (ok === undefined ? "" : ok ? " on" : " off");
        d.style.display = "";
    }
    var mode = cli('<!--#echo jsonvar="cli=Device_OperatingMode"-->') || "AP";
    var wan = cli('<!--#echo jsonvar="cli=WANConnectionDevice_1:shadow"-->') || {};
    var ports = cli('<!--#echo jsonvar="cli=Switch_2_Port"-->') || {};
    var hosts = cli('<!--#echo jsonvar="cli=LANDevice_1_Hosts"-->') || {};
    var arp = cli('<!--#echo jsonvar="cli=LANDevice_1_ARPTable"-->') || {};
    var wl = cli('<!--#echo jsonvar="cli=WLANInterface_1"-->') || {};
    var wlc = cli('<!--#echo jsonvar="cli=WLANConfig"-->') || {};
    var ntpOn = cli('<!--#echo jsonvar="cli=Services_Time_NTPEnable"-->');
    var errTok = cli('<!--#echo jsonvar="token=Device_ErrorsAck"-->');

    function run() {
        var t = kv("ni-tether-raw"), w = kv("ni-wifi-raw"), i, j, m, f;

        // Internet: configured connection, Internet working, active source
        if (el("ni-internet") && mode == "Router") {
            var ppp = wan.WANPPPConnection || {}, ipc = wan.WANIPConnection || {}, st = wan.Status || {};
            var type = ppp.Enable == "1" ? "%(ppp)s" : ipc.AddressingType == "Static" ? "%(static)s" : "%(cdhcp)s";
            var up = st.State == "Up";
            line("ni-wan-conn", type, up ? "%(connected)s" + (st.IPAddress ? " (" + esc(st.IPAddress) + ")" : "") : "%(disconnected)s", up);
            line("ni-inet", "%(internet)s", t.internet == "up" ? "%(inetok)s" : "%(inetdown)s", t.internet == "up");
            var via = t.active == "wan" ? "%(wan)s (" + type + ")" : t.active == "phone" ? "%(viaphone)s" : "%(nonet)s";
            line("ni-inet-via", "%(via)s", via);
        } else if (el("ni-internet")) {
            // access point: management address and Internet through the main router (tetherd)
            line("ni-wan-conn", "%(apconn)s", t.apip ? esc(t.apip) : "%(noaddr)s", !!t.apip);
            line("ni-inet", "%(internet)s", t.internet == "up" ? "%(inetok)s" : "%(inetdown)s", t.internet == "up");
            line("ni-inet-via", "%(via)s", t.apgw ? "%(gateway)s " + esc(t.apgw) + (t.apdns ? ", DNS " + esc(t.apdns) : "") : "%(nonet)s");
            if (el("ni-inet-link")) el("ni-inet-link").href = "config_ap.htm";
        }

        // Local network: devices (name, IP) and negotiated speed of each connected port. A port's
        // MAC list (Status.ARPTable) is joined with the host table (names, DHCP addresses) and the
        // router's ARP table (address of any device it talked to); MACs compared as bare hex
        function hex(v) { return String(v || "").toLowerCase().replace(/[^0-9a-f]/g, ""); }
        var dev = {}, k, hm;
        for (k in arp) if (arp.hasOwnProperty(k) && arp[k] && arp[k].MACAddress) dev[hex(arp[k].MACAddress)] = { ip: arp[k].IPAddress || "", name: "" };
        for (k in hosts) if (hosts.hasOwnProperty(k) && hosts[k] && hosts[k].MACAddress) {
            hm = hex(hosts[k].MACAddress);
            dev[hm] = { ip: hosts[k].IPAddress || (dev[hm] || {}).ip || "", name: hosts[k].Hostname || "" };
        }
        var plist = (ports.List || "").split(",");
        for (i = 0; i < plist.length; i++) {
            var p = ports[plist[i]], span;
            if (!p || !p.Status || p.Status.LinkState != "Up") continue;
            span = el("LAN" + p.PortId + "Hostname");
            if (!span) continue;
            var macs = String(p.Status.ARPTable || "").split(/[,;\s]+/), out = [], more = 0, d, up = false;
            for (m = 0; m < macs.length; m++) {
                d = dev[hex(macs[m])];
                if (!hex(macs[m]) || !d || (!d.ip && !d.name)) continue;
                // the uplink port of an access point carries the whole main network: first 4
                if (out.length >= 4) { more++; continue; }
                // no name known (an access point has no DHCP server, the host table is empty): IP only
                if (t.apgw && d.ip == t.apgw) up = true;
                out.push((d.name ? esc(d.name) + "<br/>" : "") + esc(d.ip || "") + (t.apgw && d.ip == t.apgw ? " <em>(%(gwtag)s)</em>" : ""));
            }
            if (more) out.push("<em>+" + more + "</em>");
            // AP mode: the port the main router is behind lists devices of the whole main network
            if (up) out.unshift("<em>%(uplink)s:</em>");
            var lm = /^(\d+)base[^-]*-(FD|HD)/.exec(p.Status.LinkMode || "");
            var speed = lm ? (+lm[1] >= 1000 ? (+lm[1] / 1000) + " Gbps" : lm[1] + " Mbps") + (lm[2] == "HD" ? " %(half)s" : "") : "";
            span.innerHTML = (out.length ? out.join("<br/>") : "---") + (speed ? "<br/><em>" + speed + "</em>" : "");
        }

        // Wi-Fi: clients, actual channel and width, transmit power
        if (wlc.Enable == "1" && el("ni-wifi-info")) {
            el("ni-wifi-info").innerHTML = "<strong>%(clients)s:</strong> " + esc((wl.Station || {}).Count || "0") +
                " &nbsp; <strong>%(channel)s:</strong> " + esc(w.channel || wlc.CurrentChannel || "-") +
                " &nbsp; <strong>%(width)s:</strong> " + esc(w.bandwidth ? w.bandwidth + " MHz" : "-") +
                " &nbsp; <strong>%(power)s:</strong> " + esc(wlc.TxPower ? wlc.TxPower + "%%" : "-");
            el("ni-wifi-info").style.display = "";
        }

        // USB tethering: phone, address, its Internet
        var s = {unplugged: "%(none)s", dhcp: "%(dhcp)s", up: "%(up)s", disabled: "%(disabled)s"}[t.state] || "-";
        var dev = trim(t.device);
        if (dev) s = esc(dev) + " - " + s;
        if (t.state == "up" && t.ip) s += " (" + esc(t.ip) + ")";
        line("ni-tether-phone", "%(phone)s", s, t.state == "up");
        if (mode != "Router") {
            line("ni-tether-inet", "%(phoneinet)s", "%(apnote)s");
        } else if (t.state == "up") {
            line("ni-tether-inet", "%(phoneinet)s", t.phonenet == "up" ? "%(inetok)s" : "%(inetdown)s", t.phonenet == "up");
        } else {
            el("ni-tether-inet").style.display = "none";
        }

        // Dynamic DNS: public IP and each enabled service's last result (run logs: account sections)
        var dd = cli('<!--#echo jsonvar="cli=Services_DynDNS:shadow"-->') || {}, dl = (dd.List || "").split(",");
        var logs = {}, cur = null, raw = (el("ni-ddns-raw") ? el("ni-ddns-raw").innerHTML : "").split("\n"), pub = "", out2 = [];
        for (i = 0; i < raw.length; i++) {
            var ln = trim(raw[i]);
            if ((m = /^account: (\d+)$/.exec(ln))) { cur = logs[m[1]] = {}; continue; }
            if (!cur) continue;
            if ((m = /^check IP: \S+ -> ([0-9a-fA-F.:]+)$/.exec(ln))) { cur.ip = m[1]; }
            if ((m = /^result: (\S+)/.exec(ln))) { cur.result = m[1]; }
            if (/^status: running/.test(ln)) { cur.running = true; }
        }
        for (i = 0; i < dl.length; i++) {
            var a = dd[dl[i]];
            if (!a || a.Enable != "1" || !(a.Host || a.URL)) continue;
            var lg = logs[dl[i]] || {}, okk = lg.result ? lg.result == "ok" : (a.Status || "").toLowerCase() == "ok";
            if (lg.ip && (!pub || lg.ip.indexOf(":") < 0)) pub = lg.ip;
            if (!pub && a.Cache) pub = a.Cache;
            out2.push('<span class="' + (lg.running ? "" : okk ? "ni-ok" : "ni-bad") + '">' + esc(a.Host || "-") + ": " +
                (lg.running ? "%(updating)s" : okk ? "OK" : "%(failed)s") + "</span>");
        }
        if (out2.length) {
            el("ni-ddns").style.display = "";
            line("ni-ddns-ip", "%(pubip)s", esc(pub || "-"), !!pub);
            el("ni-ddns-list").innerHTML = out2.join("<br/>");
        }

        // USB devices
        var usb = (el("ni-usb-raw") ? el("ni-usb-raw").innerHTML : "").split("\n"), names = [];
        for (i = 0; i < usb.length; i++) {
            m = /^usb=(.*)$/.exec(trim(usb[i])); if (!m) continue;
            f = m[1].split("|");
            var d = f[4] || "", ty = /rndis_host|cdc_ether/.test(d) ? "%(tphone)s" : /usblp/.test(d) ? "%(tprinter)s" :
                /usbserial|option/.test(d) ? "%(tmodem)s" : /usb-storage/.test(d) ? "%(tstorage)s" : "%(tother)s";
            names.push(esc(trim((f[2] || "") + " " + (f[3] || "")) || f[1] || "?") + " (" + ty + ")");
        }
        if (names.length) { el("ni-usb-list").innerHTML = names.join("<br/>"); el("ni-usb-list").className = "status-detail on"; }

        // logged errors (scripts/errscan, /nvram/ni-errors): count, list, mark as examined
        var er = (el("ni-err-raw") ? el("ni-err-raw").innerHTML : "").split("\n"), el2 = [];
        for (i = 0; i < er.length; i++) if (/^\d{4}-\d\d-\d\d \d\d:\d\d \| /.test(trim(er[i]))) el2.push(trim(er[i]));
        if (el2.length && el("ni-errors")) {
            el("ni-err-text").innerHTML = el2.length == 1 ? "%(error1)s" : "%(errors)s".replace("{n}", el2.length);
            el("ni-err-list").innerHTML = esc(el2.join("\n"));
            el("ni-errors").style.display = "";
            el("ni-err-show").onclick = function() {
                var l = el("ni-err-list"), open = l.style.display == "none";
                l.style.display = open ? "" : "none"; this.innerHTML = open ? "%(errhide)s" : "%(errshow)s"; return false;
            };
            el("ni-err-ack").onclick = function() {
                ConfigAccess(errTok).rollback().write("Device_ErrorsAck", String(new Date().getTime())).commit(function(res) {
                    if (res.error) { el("ni-err-text").innerHTML = esc(res.error); return; }
                    el("ni-errors").innerHTML = "%(errdone)s"; el("ni-errors").className = "ni-errors done";
                });
                return false;
            };
        }

        // date and time: clock.inc "now: ...", ntpsync.inc "last=... result=ok|failed"
        if (el("ni-ntp")) {
            var nraw = el("ni-ntp-raw").innerHTML, nn = /now: ([^\n<]+)/.exec(nraw), nt = kv("ni-ntp-raw");
            line("ni-ntp-now", "%(now)s", nn ? esc(trim(nn[1])) : "-");
            if (ntpOn != "1") line("ni-ntp-last", "%(lastsync)s", "%(ntpoff)s", false);
            else if (!nt.last) line("ni-ntp-last", "%(lastsync)s", "%(never)s", false);
            else line("ni-ntp-last", "%(lastsync)s", esc(nt.last) + " (" + (nt.result == "ok" ? "%(ok)s" : "%(failed)s") + ")", nt.result == "ok");
        }
    }
    if (window.addEventListener) window.addEventListener("load", run, false);
    else if (window.attachEvent) window.attachEvent("onload", run);
})();
</script>
</body>"""


def status(lang):
    s = STATUS_TXT[lang]

    def fn(txt):
        for img in ('wifi-locked2.png', 'icon-set-top.png', 'icon-phone.png'):  # hotspot, TV, phone
            txt = sub1(r'<tr>(\s*<th>\s*<img src="\.\./\.\./img/' + re.escape(img) + ')',
                       r'<tr style="display:none">\1', txt, 'status ' + img)
        txt = sub1(r'<tr>(\s*<th>\s*<img src="\.\./\.\./img/icon-internet\.png)', r'<tr id="ni-internet">\1', txt,
                   'status internet')
        # Internet row: the stock xDSL/ETH/PPP indicators and the DSL-oriented details are hidden
        # (kept in the page, the stock script fills them); our lines follow
        for d in ('ethDetails', 'dslDetails', 'pppDetails'):
            txt = sub1(r'(<div id="%s" class="status-detail [a-z]+")' % d, r'\1 style="display:none"', txt, 'status ' + d)
        txt = sub1(r'(<div id="pppDetails"[^>]*>.*?</div>)', lambda m: m.group(1) +
                   '\n\t\t\t\t\t\t\t<div id="ni-wan-conn" class="status-detail" style="display:none"></div>'
                   '<div id="ni-inet" class="status-detail" style="display:none"></div>'
                   '<div id="ni-inet-via" class="status-detail" style="display:none"></div>', txt, 'status internet lines',
                   flags=re.S)
        txt = sub1(r'&gt; <a\s+id="internet-link"\s+class="pointer">[^<]*</a>',
                   lambda m: '&gt; <a id="ni-inet-link" href="config_internet.htm">%s</a>' % s['settings'], txt, 'status internet link')
        # Wi-Fi row: clients, channel, width, power
        txt = sub1(r'(<div id="wirelessDetails"[^>]*>.*?</div>)', lambda m: m.group(1) +
                   '<div id="ni-wifi-info" class="status-detail" style="display:none"></div>'
                   '<pre id="ni-wifi-raw" style="display:none"><!--#include file="wifi.inc" --></pre>', txt,
                   'status wifi info', flags=re.S)
        # USB tethering and USB devices rows, after the others
        row = ('<tr id="ni-tether">\n'
               '\t<th><img src="../../img/icon-tether.png" alt="USB" /><span>%(title)s</span></th>\n'
               '\t<td><pre id="ni-tether-raw" style="display:none"><!--#include file="tether.inc" --></pre>\n'
               '\t\t<div id="ni-tether-phone" class="status-detail off"></div>\n'
               '\t\t<div id="ni-tether-inet" class="status-detail" style="display:none"></div></td>\n'
               '\t<td class="status-link">&gt; <a href="config_usb.htm">%(settings)s</a></td>\n'
               '</tr>\n'
               '<tr id="ni-usb">\n'
               '\t<th><img src="../../img/icon-local.png" alt="USB" /><span>%(usbtitle)s</span></th>\n'
               '\t<td><pre id="ni-usb-raw" style="display:none"><!--#include file="usb.inc" --></pre>\n'
               '\t\t<div id="ni-usb-list" class="status-detail off">%(nousb)s</div></td>\n'
               '\t<td class="status-link">&gt; <a href="config_usb.htm">%(settings)s</a></td>\n'
               '</tr>\n') % s
        # order: Internet, Local Network, Wireless, USB tethering, USB devices
        m = re.search(r'\n[ \t]*<tr>\s*<th>\s*<img src="\.\./\.\./img/icon-local\.png".*?'
                      r'<tr id="lans-link-more".*?</tr>\n', txt, re.S)
        if not m:
            sys.exit('status: Local Network rows not found')
        # Dynamic DNS row (shown when a service is enabled), last
        ddns = ('\n<tr id="ni-ddns" style="display:none">\n'
                '\t<th><img src="../../img/icon-ddns.png" alt="DDNS" /><span>%(ddns)s</span></th>\n'
                '\t<td><pre id="ni-ddns-raw" style="display:none"><!--#include file="ddns.inc" --></pre>\n'
                '\t\t<div id="ni-ddns-ip" class="status-detail"></div>\n'
                '\t\t<div id="ni-ddns-list" class="status-detail"></div></td>\n'
                '\t<td class="status-link">&gt; <a href="config_ddns.htm">%(settings)s</a></td>\n'
                '</tr>\n'
                # NTP: router clock (tetherd) and the last synchronisation (init.d/ntp, scripts/ntp-now)
                '<tr id="ni-ntp">\n'
                '\t<th><img src="../../img/icon-clock.png" alt="NTP" /><span>%(ntp)s</span></th>\n'
                '\t<td><pre id="ni-ntp-raw" style="display:none"><!--#include file="clock.inc" --><!--#include file="ntpsync.inc" --></pre>\n'
                '\t\t<div id="ni-ntp-now" class="status-detail"></div>\n'
                '\t\t<div id="ni-ntp-last" class="status-detail"></div></td>\n'
                '\t<td class="status-link">&gt; <a href="config_ntp.htm">%(settings)s</a></td>\n'
                '</tr>') % s
        lan = m.group(0)
        txt = txt[:m.start()] + '\n' + txt[m.end():]
        txt = sub1(r'(\n)([ \t]*<tr>\s*<th>\s*<img src="\.\./\.\./img/icon-wi-fi\.png)',
                   lambda m: lan + m.group(2), txt, 'status wifi row')
        errs = ('\n<div id="ni-errors" class="ni-errors" style="display:none"><span id="ni-err-text"></span> '
                '<a id="ni-err-show" href="#">%(errshow)s</a> | <a id="ni-err-ack" href="#">%(errack)s</a>'
                '<pre id="ni-err-list" style="display:none"></pre></div>\n'
                '<pre id="ni-err-raw" style="display:none"><!--#include file="errors.inc" --></pre>\n') % s
        txt = sub1(r'(</tr>\n)(\s*</table>)(\s*</div><!--col-722-->)', lambda m: m.group(1) + row + ddns + '\n' + m.group(2) + errs + m.group(3), txt,
                   'status table end')
        # in AP mode the Internet row shows the management address and the Internet via the main router
        js = STATUS_JS % s
        return sub1(r'</body>', lambda m: js, txt, 'status body')
    return fn


def changelog(txt):
    txt = sub1(r'\n<p><b>GitHub:</b>[^\n]*</p>\n', '\n', txt, 'changelog github')
    return sub1(r'(<h3>Changelog</h3>\n+)', lambda m: m.group(1) + CHANGELOG, txt, 'changelog')


if __name__ == '__main__':
    copy_overlay()
    edit(os.path.join(B, 'config.default', 'router.conf'), router_conf)
    edit(os.path.join(B, 'config.default', 'router.xml'), router_xml)
    edit(os.path.join(B, 'rc'), rc)
    edit(os.path.join(B, 'lib', 'dyndns'), dyndns_lib)
    edit(os.path.join(B, 'lib', 'wifi'), wifi_lib)
    edit(os.path.join(B, 'init.d', 'inetd'), inetd)
    edit(os.path.join(B, 'init.d', 'ntp'), ntp_initd)
    edit(os.path.join(B, 'user.d', 'diag'), diag_user)
    edit(os.path.join(B, 'lib', 'dhcpclient'), dhcpclient_lib)
    edit(os.path.join(B, 'init.d', 'lan'), lan_initd)
    edit(os.path.join(B, 'init.d', 'dnsmasq'), dnsmasq_initd)
    write(os.path.join(B, 'release'), VERSION + '\n')
    print('release', VERSION)
    edit(os.path.join(IAD, 'css', 'gateway.css'), lambda t: t + NI_CSS)
    for d, _, files in os.walk(IAD):
        for fn in files:
            if fn.endswith(('.htm', '.html')):
                edit(os.path.join(d, fn), branding)
    for lang in LANGS:
        js = os.path.join(IAD, lang, 'js')
        adm = os.path.join(IAD, lang, 'admin')
        edit(os.path.join(js, 'menu.js'), menu_js(lang))
        edit(os.path.join(js, 'files.txt'), files_txt)
        edit(os.path.join(js, 'dns.js'), dns_js)
        edit(os.path.join(adm, 'config_advanced.htm'), advanced(lang))
        edit(os.path.join(adm, 'config_wireless.htm'), wireless(lang))
        edit(os.path.join(adm, 'admin_password.htm'), account(lang))
        edit(os.path.join(js, 'admin_password.javascript'), account_js(lang))
        edit(os.path.join(adm, 'auth.htm'), auth(lang))
        edit(os.path.join(js, 'config_wireless.javascript'), wifi_js(lang))
        edit(os.path.join(js, 'logread.javascript'), logread_js)
        edit(os.path.join(adm, 'logread.htm'), logread_htm(lang))
        edit(os.path.join(adm, 'firmware.htm'), firmware(lang))
        edit(os.path.join(adm, 'config_lan.htm'), lan)
        edit(os.path.join(adm, 'config_lan.htm'), lan_ddns)
        edit(os.path.join(adm, 'about.htm'), about)
        edit(os.path.join(adm, 'config_apps.htm'), apps(lang))
        edit(os.path.join(adm, 'services_status.htm'), status(lang))
        edit(os.path.join(adm, 'changelog.htm'), changelog)
        for page in descriptions.PAGES:
            edit(os.path.join(adm, page), lambda t, page=page, lang=lang: descriptions.describe(page, lang, t))
        # runtime status written by tetherd, included by the Status and USB pages: the ssi CGI
        # only includes files from the page's own directory (absolute and ../ paths are refused)
        for name in ('tether', 'usb', 'wifi', 'hw', 'ddns', 'sshkey', 'clock', 'ntp', 'ntpsync', 'fwupdate'):
            inc = os.path.join(adm, name + '.inc')
            if os.path.lexists(inc):
                os.remove(inc)
            os.symlink('/var/status/' + {'ddns': 'ddns-all', 'ntp': 'ntp.log'}.get(name, name), inc)
        # logged errors (scripts/errscan), kept in flash across reboots
        inc = os.path.join(adm, 'errors.inc')
        if os.path.lexists(inc):
            os.remove(inc)
        os.symlink('/nvram/ni-errors', inc)
    print('configure done')
