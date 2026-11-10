const load = require('./harness.js'), assert = require('assert'), dir = process.argv[2];
const base = {
  'token=Device_OperatingMode,LANDevice,Services_WANAutoConfig,ModemInterface,Layer3Forwarding,WANConnectionDevice,Services_Time': '{"t":1}', 'token=reboot': '{"t":2}',
  'cli=LANDevice_1_IPInterface_1_AddressingType': '"DHCP"', 'cli=LANDevice_1_IPInterface_1_IPAddress': '"192.168.25.1"',
  'cli=LANDevice_1_IPInterface_1_SubnetMask': '"255.255.255.0"', 'cli=LANDevice_1_IPInterface_1_Gateway': '',
  'cli=LANDevice_1_DNSServers': '""', 'cli=LANDevice_1_IPStatus': '{"CurrentIPAddress":"10.0.0.57"}',
};
// --- config_ap in AP mode
let c = load(dir + '/config_ap.htm', Object.assign({ 'cli=Device_OperatingMode': '"AP"' }, base));
assert.equal(c.el('opmode').value, 'AP'); assert.equal(c.el('apSection').style.display, '');
c.handlers['#applyMode'](); assert.equal(c.calls.length, 0); assert(c.msgs[0].startsWith('I:'));     // same mode
c.el('opmode').value = 'Router'; c.handlers['#applyMode']();
assert.equal(c.calls[0].write.Device_OperatingMode, 'Router'); assert.equal(c.calls[0].write.LANDevice_1_HostConfig_DHCPServerEnable, '1');
assert.equal(c.calls[0].write.Services_WANAutoConfig_Enable, '0'); assert.equal(c.calls[0].write.WANConnectionDevice_1_PhysicalInterface_2_Enable, '1');
assert.equal(c.calls[0].write.Services_Time_NTPInterfaceType, 'WANConnectionDevice');
assert.deepEqual(c.calls[1].fct, ['reboot']); assert.deepEqual(c.calls[1].token, { t: 2 });
c.handlers['#save'](); assert.equal(c.calls[2].write.LANDevice_1_IPInterface_1_AddressingType, 'DHCP');
// --- config_ap in Router mode, unset mode -> AP
c = load(dir + '/config_ap.htm', Object.assign({ 'cli=Device_OperatingMode': '"Router"' }, base));
assert.equal(c.el('apSection').style.display, 'none'); c.el('opmode').value = 'AP'; c.handlers['#applyMode']();
assert.equal(c.calls[0].write.LANDevice_1_IPInterface_1_AddressingType, 'DHCP'); assert.equal(c.calls[0].write.ModemInterface_1_Enable, '0');
assert.equal(c.calls[0].write.WANConnectionDevice_1_PhysicalInterface_2_Enable, '0');
assert.equal(c.calls[0].write.Services_Time_NTPInterfaceType, 'LANDevice');
c = load(dir + '/config_ap.htm', Object.assign({ 'cli=Device_OperatingMode': '' }, base));
assert.equal(c.el('opmode').value, 'AP');
// --- config_3g
const g = {
  'token=ModemInterface,WANConnectionDevice,Layer3Forwarding': '{"t":3}', 'cli=Device_OperatingMode': '"Router"',
  'cli=ModemInterface_1': '{"Enable":"0","PhoneNumber":"*99***1#","ModePref":"3Gpref","Status":{"Product":"E173","SIMState":"READY"}}',
  'cli=WANConnectionDevice_6_WANPPPConnection_Username': '"claro"', 'cli=Layer3Forwarding_DefaultConnectionService': '"1"',
};
c = load(dir + '/config_3g.htm', g);
assert.equal(c.el('stProduct').innerHTML, 'E173'); assert.equal(c.el('stManufacturer').innerHTML, '-'); assert.equal(c.msgs.length, 0);
c.el('pin').value = '12'; c.handlers['#save'](); assert.equal(c.calls.length, 0); assert(c.msgs[0].startsWith('E:'));
c.el('pin').value = '1234'; c.el('enable').checked = true; c.el('source').value = '6'; c.el('apn').value = ' claro.com.br '; c.handlers['#save']();
assert.deepEqual(c.calls[0].write, { ModemInterface_1_Enable: '1', ModemInterface_1_APN: 'claro.com.br', ModemInterface_1_PINCode: '1234',
  ModemInterface_1_PhoneNumber: '*99***1#', ModemInterface_1_ModePref: '3Gpref', WANConnectionDevice_6_WANPPPConnection_Username: 'claro',
  Layer3Forwarding_DefaultConnectionService: '6' });
assert.deepEqual(c.calls[0].encrypt, {});                       // empty password keeps the stored one
c.el('pass').value = 'secret'; c.handlers['#save'](); assert.deepEqual(c.calls[1].encrypt, { WANConnectionDevice_6_WANPPPConnection_Password: 'secret' });
c = load(dir + '/config_3g.htm', Object.assign({}, g, { 'cli=Device_OperatingMode': '"AP"', 'cli=ModemInterface_1': '' }));
assert(c.msgs[0].startsWith('I:')); assert.equal(c.el('number').value, '*99#');
// --- config_internet
const wanObj = (o) => JSON.stringify(Object.assign({
  MACAddressOverride: '0', MACAddress: '', DNSServers: '',
  PhysicalInterface: { List: '1,2,3', '1': { Enable: '1', VlanNumber: '' }, '2': { Enable: '1', VlanNumber: '1' }, '3': { Enable: '1', VlanNumber: '1' } },
  WANIPConnection: { Enable: '0', IPAddress: '10.0.0.3', SubnetMask: '', DefaultGateway: '10.0.0.1', AddressingType: 'Static' },
  WANPPPConnection: { Enable: '1', Username: 'turbonet@turbonet', Password: '********', PPPoEServiceName: '' },
  Status: { State: 'Up', IPAddress: '177.1.2.3', Gateways: '177.1.2.1', DNSServers: '8.8.8.8' } }, o));
const inet = (o) => ({
  'token=WANConnectionDevice,WANEthernetInterface,Services_WANAutoConfig,Device_InternetProbes,Device_WANIsolate,Services_DnsForwarder': '{"t":4}', 'cli=Device_OperatingMode': '"Router"',
  'cli=Services_DnsForwarder': '{"Enable":"1","DoT":"off","RebindProtect":"1"}',
  'cli=Device_InternetProbes': '"1.1.1.1,8.8.8.8"', 'cli=Device_WANIsolate': '"0"',
  'cli=WANConnectionDevice_1:shadow': wanObj(o || {}), 'cli=WANEthernetInterface_1_VLANInterface_1': '{"Enable":"1","VID":"600"}',
});
c = load(dir + '/config_internet.htm', inet());
assert.equal(c.el('ctype').value, 'PPPoE'); assert.equal(c.el('user').value, 'turbonet@turbonet'); assert.equal(c.el('vlan').checked, true);
assert.equal(c.el('probes').value, '1.1.1.1, 8.8.8.8'); assert.equal(c.el('isolate').checked, false);
assert.equal(c.el('vid').value, '600'); assert.equal(c.el('stIp').innerHTML, '177.1.2.3'); assert.equal(c.el('secStatic').style.display, 'none');
assert.equal(c.msgs.length, 0);
c.handlers['#save'](); let w = c.calls[0].write;                                 // PPPoE, VLAN 600, keep password
assert.equal(w.WANConnectionDevice_1_WANPPPConnection_Enable, '1'); assert.equal(w.WANConnectionDevice_1_WANIPConnection_Enable, '0');
assert.equal(w.WANConnectionDevice_1_PhysicalInterface_1_Enable, '0'); assert.equal(w.WANConnectionDevice_1_PhysicalInterface_2_Enable, '1');
assert.equal(w.WANConnectionDevice_1_PhysicalInterface_3_Enable, '0'); assert.equal(w.Services_WANAutoConfig_Enable, '0');
assert.equal(w.WANConnectionDevice_1_PhysicalInterface_2_VlanNumber, '1'); assert.equal(w.WANEthernetInterface_1_VLANInterface_1_VID, '600');
assert.equal(w.WANConnectionDevice_1_MACAddressOverride, '0'); assert(!('WANConnectionDevice_1_WANPPPConnection_Password' in w));
assert.equal(w.Device_InternetProbes, '1.1.1.1,8.8.8.8'); assert.equal(w.Device_WANIsolate, '0');
assert(!('Services_DnsForwarder_DoT' in w) && !('Services_DnsForwarder_RebindProtect' in w));   // DNS unchanged: not written
assert.equal(c.el('dot').value, 'off'); assert.equal(c.el('rebind').checked, true);
assert.deepEqual(c.calls[0].encrypt, {});
c.el('pass').value = 'pw'; c.el('svc').value = ' isp '; c.el('vlan').checked = false; c.el('macclone').checked = true; c.el('mac').value = 'aa-bb-cc-dd-ee-ff';
c.handlers['#save'](); w = c.calls[1].write;
assert.deepEqual(c.calls[1].encrypt, { WANConnectionDevice_1_WANPPPConnection_Password: 'pw' });
assert.equal(w.WANConnectionDevice_1_PhysicalInterface_2_VlanNumber, '1'); assert.equal(w.WANEthernetInterface_1_VLANInterface_1_VID, '0');
assert.equal(w.WANConnectionDevice_1_WANPPPConnection_PPPoEServiceName, 'isp');
assert.equal(w.WANConnectionDevice_1_MACAddressOverride, '1'); assert.equal(w.WANConnectionDevice_1_MACAddress, 'AA:BB:CC:DD:EE:FF');
c.el('nopass').checked = true; c.handlers['#save']();                            // no password
assert.equal(c.calls[2].write.WANConnectionDevice_1_WANPPPConnection_Password, ''); assert.deepEqual(c.calls[2].encrypt, {});
c.el('mac').value = 'zz'; c.handlers['#save'](); assert.equal(c.calls.length, 3); assert(c.msgs[0].startsWith('E:'));
c.el('macclone').checked = false; c.el('vlan').checked = true; c.el('vid').value = '5000'; c.handlers['#save'](); assert.equal(c.calls.length, 3);
c.el('vid').value = '600'; c.el('user').value = ' '; c.handlers['#save'](); assert.equal(c.calls.length, 3);   // account required
c.el('user').value = 'u'; c.el('ctype').value = 'DHCP'; c.handlers['#save'](); w = c.calls[3].write;
assert.equal(w.WANConnectionDevice_1_WANIPConnection_Enable, '1'); assert.equal(w.WANConnectionDevice_1_WANIPConnection_AddressingType, 'DHCP');
assert.equal(w.WANConnectionDevice_1_WANPPPConnection_Enable, '0'); assert.equal(w.WANConnectionDevice_1_DNSServers, '');
c.el('ctype').value = 'Static'; c.el('ip').value = '200.1.2.10'; c.el('mask').value = '255.255.255.0'; c.el('gw').value = '200.1.2.1';
c.el('dns').value = '1.1.1.1, 8.8.8.8'; c.handlers['#save'](); w = c.calls[4].write;
assert.equal(w.WANConnectionDevice_1_WANIPConnection_AddressingType, 'Static'); assert.equal(w.WANConnectionDevice_1_WANIPConnection_IPAddress, '200.1.2.10');
assert.equal(w.WANConnectionDevice_1_DNSServers, '1.1.1.1,8.8.8.8');
c.el('mask').value = '255.0.255.0'; c.handlers['#save'](); assert.equal(c.calls.length, 5);                     // bad mask
c.el('mask').value = '255.255.255.0'; c.el('dns').value = '1.1.1'; c.handlers['#save'](); assert.equal(c.calls.length, 5);
c = load(dir + '/config_internet.htm', inet({ WANPPPConnection: { Enable: '0' }, WANIPConnection: { Enable: '1', AddressingType: 'Static', IPAddress: '1.2.3.4' },
  PhysicalInterface: { List: '2', '2': { Enable: '1', VlanNumber: '' } }, MACAddressOverride: '1', MACAddress: '00:11:22:33:44:55', Status: { State: 'Down' } }));
assert.equal(c.el('ctype').value, 'Static'); assert.equal(c.el('vlan').checked, false); assert.equal(c.el('rowVid').style.display, 'none');
assert.equal(c.el('macclone').checked, true); assert.equal(c.el('secPpp').style.display, 'none'); assert.equal(c.el('stIp').innerHTML, '-');
c = load(dir + '/config_internet.htm', inet({ WANPPPConnection: { Enable: '0' }, WANIPConnection: { Enable: '1', AddressingType: 'DHCP' } }));
assert.equal(c.el('ctype').value, 'DHCP');
c = load(dir + '/config_internet.htm', Object.assign(inet(), { 'cli=WANEthernetInterface_1_VLANInterface_1': '{"Enable":"1","VID":"0"}' }));
assert.equal(c.el('vlan').checked, false); assert.equal(c.el('vid').value, '');  // VID 0 = untagged
c = load(dir + '/config_internet.htm', Object.assign(inet(), { 'cli=Device_OperatingMode': '"AP"' })); assert(c.msgs[0].startsWith('I:'));
c = load(dir + '/config_internet.htm', inet());                                   // monitoring + isolation
c.el('probes').value = ' 9.9.9.9 , 1.0.0.1'; c.el('isolate').checked = true; c.handlers['#save']();
assert.equal(c.calls[0].write.Device_InternetProbes, '9.9.9.9,1.0.0.1'); assert.equal(c.calls[0].write.Device_WANIsolate, '1');
c.el('probes').value = 'example.com'; c.handlers['#save'](); assert.equal(c.calls.length, 1); assert(c.msgs[0].startsWith('E:'));
c.el('probes').value = '1.1.1.1,2.2.2.2,3.3.3.3,4.4.4.4,5.5.5.5'; c.handlers['#save'](); assert.equal(c.calls.length, 1);
c = load(dir + '/config_internet.htm', Object.assign(inet(), { 'cli=Device_InternetProbes': 'undefined', 'cli=Device_WANIsolate': '"1"' }));
assert.equal(c.el('probes').value, '1.1.1.1, 8.8.8.8'); assert.equal(c.el('isolate').checked, true);
c = load(dir + '/config_internet.htm', inet());                                   // DNS over TLS, rebinding protection
c.el('dot').value = 'quad9'; c.el('rebind').checked = false; c.handlers['#save']();
assert.equal(c.calls[0].write.Services_DnsForwarder_DoT, 'quad9'); assert.equal(c.calls[0].write.Services_DnsForwarder_RebindProtect, '0');
c.handlers['#save'](); assert(!('Services_DnsForwarder_DoT' in c.calls[1].write));  // saved: unchanged now
c = load(dir + '/config_internet.htm', Object.assign(inet(), { 'cli=Services_DnsForwarder': '{"DoT":"cloudflare"}' }));
assert.equal(c.el('dot').value, 'cloudflare'); assert.equal(c.el('rebind').checked, true);
// --- config_usb
const usb = (o) => Object.assign({
  'token=Device_TetherFailover,Services_Ippos_Enable': '{"t":5}', 'cli=Device_OperatingMode': '"Router"',
  'cli=Device_TetherFailover': '"1"', 'cli=Services_Ippos_Enable': '"0"',
  'include=tether.inc': 'mode=Router\nfailover=1\nstate=up\ndevice=SAMSUNG SAMSUNG_Android\nip=10.34.99.61\ngateway=10.34.99.57\ndns=10.34.99.57\nwan=up\nactive=wan\n',
  'include=usb.inc': 'usb=1-1|04e8:6863|SAMSUNG|SAMSUNG_Android|rndis_host\nusb=1-2|03f0:0517|HP|<b>LaserJet</b>|usblp\n',
}, o);
c = load(dir + '/config_usb.htm', usb());
assert.equal(c.el('failover').checked, true); assert.equal(c.el('printer').checked, false); assert.equal(c.msgs.length, 0);
assert(c.el('tState').innerHTML.indexOf('SAMSUNG SAMSUNG_Android') == 0); assert(c.el('tState').innerHTML.indexOf('(10.34.99.61)') > 0);
const list = c.el('usbList').innerHTML;
assert(list.indexOf('SAMSUNG SAMSUNG_Android') > 0 && list.indexOf('04e8:6863') > 0); assert(list.indexOf('&lt;b&gt;LaserJet') > 0);
assert.equal((list.match(/<tr>/g) || []).length, 2);
c.el('failover').checked = false; c.el('printer').checked = true; c.handlers['#save']();
assert.deepEqual(c.calls[0].write, { Device_TetherFailover: '0', Services_Ippos_Enable: '1' }); assert.deepEqual(c.calls[0].token, { t: 5 });
c = load(dir + '/config_usb.htm', usb({ 'cli=Device_OperatingMode': '"AP"', 'cli=Device_TetherFailover': '"0"',
  'include=tether.inc': '<HR><H2>Not Found</H2>\n<HR>', 'include=usb.inc': '' }));
assert.equal(c.el('failover').checked, false); assert.equal(c.el('tState').innerHTML, '-'); assert(c.msgs[0].startsWith('I:'));
assert.equal((c.el('usbList').innerHTML.match(/<tr>/g) || []).length, 1);
c = load(dir + '/config_usb.htm', usb({ 'cli=Device_TetherFailover': 'undefined', 'include=tether.inc': 'state=disabled\ndevice= \n' }));
assert.equal(c.el('failover').checked, true); assert(c.el('tState').innerHTML.length > 1);  // unset = default on
// --- config_ddns
const acct = (o) => Object.assign({ Enable: '0', Server: '', ServerName: '', Username: '', Password: '', Host: '', URL: '', Status: '',
  EnableHTTPS: '0', Cache: '' }, o || {});
const lw = () => { for (let i = c.calls.length - 1; i >= 0; i--) if (Object.keys(c.calls[i].write).length || c.calls[i].remove.length) return c.calls[i]; };
const dd = (list, log) => {
  const obj = { List: Object.keys(list).join(',') };
  for (const k in list) obj[k] = acct(list[k]);
  return { 'token=Services_DynDNS': '{"t":6}', 'cli=Services_DynDNS:shadow': JSON.stringify(obj), 'include=ddns.inc': log === undefined ? '' : log };
};
c = load(dir + '/config_ddns.htm', dd({ 1: {} }));                                     // stock default: empty account 1
assert(/No dynamic DNS service|Nenhum serviço/.test(c.el('list').innerHTML)); assert.equal(c.el('server').value, 'dynv6');
assert.equal(c.el('enable').checked, true); assert.equal(c.el('editButtons').style.display, 'none'); assert.equal(c.el('addButtons').style.display, '');
c.el('host').value = 'myhome.dns.army'; c.el('pass').value = 'tok'; c.handlers['#add']();
let dw = c.calls[0].write;                                                              // reuses the empty account 1
assert.equal(dw.Services_DynDNS_1_Server, 'dynv6'); assert.equal(dw.Services_DynDNS_1_Username, 'none'); assert.equal(dw.Services_DynDNS_1_Host, 'myhome.dns.army');
assert.equal(dw.Services_DynDNS_1_Enable, '1'); assert.equal(dw.Services_DynDNS_1_EnableHTTPS, '1');
assert.deepEqual(c.calls[0].encrypt, { Services_DynDNS_1_Password: 'tok' }); assert.deepEqual(c.calls[0].token, { t: 6 });
assert.deepEqual(c.calls[0].create, []);                                                   // account 1 exists already
const log2 = 'account: 1\ntime: 2026-11-05 14:59:28\nprovider: dynv6\ncheck IP: https://api.ipify.org -> 203.0.113.7\nlast successful update: 2026-11-05 14:59:29\nresult: ok\n' +
  'account: 2\ntime: 2026-11-05 15:00:00\nprovider: customget\nresult: failed\n';
c = load(dir + '/config_ddns.htm', dd({ 1: { Enable: '1', Server: 'dynv6', Host: 'a.dns.army' },
  2: { Enable: '1', Server: 'customget', Host: 'home.example.com', URL: 'https://example.com/cpanelwebcall/k' }, 3: { Enable: '0', Server: 'nsupdate4', Host: 'u.nsupdate.info' } }, log2));
let lst = c.el('list').innerHTML;
assert.equal((lst.match(/<tr /g) || []).length, 3); assert(lst.indexOf('203.0.113.7') > 0 && lst.indexOf('2026-11-05 14:59:29') > 0);
assert(lst.indexOf('home.example.com') > 0); assert(lst.indexOf("Page.update('2')") > 0 && lst.indexOf("Page.remove('3')") > 0);
assert(c.el('log').innerHTML.indexOf('result: failed') > 0);                              // last account with a log
c.el('host').value = 'b.nsupdate.info'; c.el('server').value = 'nsupdate4'; c.el('server').onchange(); c.handlers['#add']();
assert.equal(c.calls[0].write.Services_DynDNS_4_Username, 'b.nsupdate.info');             // next free index
assert.deepEqual(c.calls[0].create, ['Services_DynDNS_4']);                                // new list entry created
c.Page.edit('2');                                                                          // edit: form filled, Save mode
assert.equal(c.el('server').value, 'customget'); assert.equal(c.el('host').value, 'home.example.com');
assert.equal(c.el('addButtons').style.display, 'none'); assert.notEqual(c.el('rowHost').style.display, 'none'); assert.equal(c.el('rowPass').style.display, 'none');
c.el('url').value = 'http://example.com/cpanelwebcall/k2'; c.handlers['#save']();
dw = lw().write; assert.equal(dw.Services_DynDNS_2_Host, 'home.example.com'); assert.equal(dw.Services_DynDNS_2_URL, 'http://example.com/cpanelwebcall/k2');
assert.equal(dw.Services_DynDNS_2_Username, 'none'); assert.deepEqual(lw().encrypt, { Services_DynDNS_2_Password: 'none' });
c.Page.edit('2'); c.el('host').value = ''; c.handlers['#save']();                        // cPanel without hostname: the URL's server
assert.equal(lw().write.Services_DynDNS_2_Host, 'example.com');
c.Page.edit('2'); c.el('url').value = 'nope'; const nc = c.calls.length; c.handlers['#save'](); assert.equal(c.calls.length, nc); assert(c.msgs[0].startsWith('E:'));
c.Page.edit('1'); c.el('server').value = 'dyndns'; c.el('server').onchange(); c.el('user').value = ''; c.handlers['#save']();
assert.equal(c.calls.length, nc);                                                        // legacy: username required
let timers = 0; global.setInterval = () => { timers++; return 1; }; global.clearInterval = () => {};
c.Page.update('2'); let last = lw().write;
assert.deepEqual(Object.keys(last), ['Services_DynDNS_2_UpdateNow']); assert(/^\d+$/.test(last.Services_DynDNS_2_UpdateNow)); assert.equal(timers, 1);
c.Page.remove('3');                                                                      // disabled first, then removed
const wr = c.calls.filter(x => Object.keys(x.write).length || x.remove.length);
assert.deepEqual(wr[wr.length - 2].write, { Services_DynDNS_3_Enable: '0' }); assert.deepEqual(wr[wr.length - 1].remove, ['Services_DynDNS_3']);
c = load(dir + '/config_ddns.htm', dd({ 1: { Server: 'athos', Host: 'x.y' } }, 'The filename requested in a include file directive, /x/ddns.inc,\ndoes not seem to exist.'));
assert(!/filename/.test(c.el('log').innerHTML)); assert(c.el('list').innerHTML.indexOf('athos') > 0);
console.log('pages ok:', dir);
// --- config_ntp
const ntp = (o) => Object.assign({
  'token=Services_Time': '{"t":9}',
  'cli=Services_Time': JSON.stringify(Object.assign({ NTPEnable: '1', NTPServers: '0.pool.ntp.org,a.ntp.br', LocalTimeZone: 'BRT3',
    NTPInterfaceType: 'LANDevice', NTPSynchronized: '1' }, o || {})),
  'include=clock.inc': 'now: 2026-11-06 12:20:00 BRT\n',
  'include=ntp.inc': 'time before: 2026-11-06 12:16:01 BRT\nntpd: reply from 200.160.7.197: offset 0.000647\nresult: synchronized\n',
});
c = load(dir + '/config_ntp.htm', ntp());
assert.equal(c.el('enable').checked, true); assert.equal(c.el('servers').value, '0.pool.ntp.org, a.ntp.br');
assert.equal(c.el('tz').value, 'BRT3'); assert.equal(c.el('rowTzCustom').style.display, 'none');
assert.equal(c.el('stClock').innerHTML, '2026-11-06 12:20:00 BRT'); assert(/result: synchronized/.test(c.el('log').innerHTML));
c.el('servers').value = ' a.ntp.br , 200.160.7.186 '; c.el('tz').value = 'CET-1CEST,M3.5.0,M10.5.0/3'; c.handlers['#save']();
assert.deepEqual(c.calls[0].write, { Services_Time_NTPEnable: '1', Services_Time_NTPServers: 'a.ntp.br,200.160.7.186',
  Services_Time_LocalTimeZone: 'CET-1CEST,M3.5.0,M10.5.0/3', Services_Time_LocalTimeZoneArea: 'CET' });
c.el('servers').value = 'bad_name'; c.handlers['#save'](); assert.equal(c.calls.length, 1); assert(c.msgs[0].startsWith('E:'));
c.el('servers').value = 'a.ntp.br'; c.el('tz').value = 'custom'; c.el('tzCustom').value = 'bad tz'; c.handlers['#save'](); assert.equal(c.calls.length, 1);
c.el('tzCustom').value = 'AMT4'; c.handlers['#save'](); assert.equal(c.calls[1].write.Services_Time_LocalTimeZone, 'AMT4');
c = load(dir + '/config_ntp.htm', ntp({ LocalTimeZone: 'XYZ5', NTPInterfaceType: 'WANConnectionDevice', NTPSynchronized: '0' }));
assert.equal(c.el('tz').value, 'custom'); assert.equal(c.el('tzCustom').value, 'XYZ5'); assert.equal(c.el('rowTzCustom').style.display, '');
assert(/WAN/.test(c.el('stVia').innerHTML) || /WAN/.test(c.el('stVia').innerHTML));
global.setInterval = () => 1; global.XMLHttpRequest = function() { this.open = () => {}; this.send = () => {}; };
c.handlers['#update'](); assert(/^\d+$/.test(c.calls[0].write.Services_Time_UpdateNow));
// --- firmware: after the upload, reboot only on a new "operation successful" from fwburn
const vm = require('vm');
function fw(logsAfter, upRaw) {
  const html = require('fs').readFileSync(dir + '/firmware.htm', 'utf8');
  let src = html.match(/<script type="text\/javascript">\n(gToken[\s\S]*?)<\/script>/)[1]
    .replace(/<!--#echo jsonvar="token=logread"-->/, '{"t":"log"}').replace(/<!--#echo jsonvar="token=reboot"-->/, '{"t":"rb"}')
    .replace(/<!--#echo jsonvar="token=Device_FwUpdate"-->/, '{"t":"up"}')
    .replace(/<!--#echo jsonvar="cli=Device_FirmwareVersion"-->/, '"cyberponk-v1.2.31"');
  const els = {}, el = id => els[id] || (els[id] = { style: {}, innerText: id == 'niUpRaw' ? (upRaw || '') : '', innerHTML: '', value: 'x.bin', submit() {} });
  let logs = 'Nov 10 10:00:00 PaceAP user.info fwburn[1]: operation successful', ready, timers = [];
  const r = { calls: [], el, timers };
  const ctx = {
    document: { getElementById: el }, setTimeout: f => timers.push(f),
    $: { util: { parseJson: JSON.parse }, event: { ready: f => { ready = f; } } }, html: () => {},
    ConfigAccess: tok => ({ fct(n) { this.n = n; return this; },
      write(k, v) { this.n = k + '=' + v; return this; },
      commit(ok) { r.calls.push(tok.t + ':' + this.n); ok(this.n == 'logread' ? { logread: logs } : {}); } }),
    confirm: () => true, XMLHttpRequest: function() { this.open = (m, u) => { r.xhr = u; }; this.send = () => {}; r.x = this; },
    setInterval: f => { r.tick = f; return 1; }, clearInterval: () => { r.tick = null; },
  };
  ctx.$ = Object.assign(() => ({ html() {} }), ctx.$);
  vm.createContext(ctx); vm.runInContext(src, ctx); ready();
  r.ctx = ctx; if (upRaw !== undefined) return r;
  vm.runInContext('sendFirmware()', ctx); logs += '|' + logsAfter; el('frameFirmware').onload();
  for (let i = 0; i < 10 && timers.length; i++) timers.shift()();
  return r;
}
let f = fw('Nov 10 10:05:00 PaceAP user.info fwburn[2]: DUAL BANK|Nov 10 10:05:09 PaceAP user.info fwburn[2]: operation successful');
assert(f.calls.includes('rb:reboot')); assert.equal(f.el('niFwMsg').className, 'ni-ok');
f = fw('Nov 10 10:05:00 PaceAP user.info fwburn[2]: WARNING: Invalid MD5SUM');
assert(!f.calls.includes('rb:reboot')); assert.equal(f.el('niFwMsg').className, 'ni-warn'); assert.equal(f.el('divForm').style.display, 'block');
f = fw('');                                                                     // only the old success line: no reboot
assert(!f.calls.includes('rb:reboot')); assert.equal(f.el('niFwMsg').style.display, 'block'); assert(f.calls.filter(x => x == 'log:logread').length > 5);
// online update: state from the last run, check -> poll -> Install -> confirm -> install
f = fw('', 'The filename requested in a include file directive does not seem to exist.');
assert(/./.test(f.el('niUpState').innerHTML)); assert.equal(f.el('niUpInstall').style.display, 'none');
f = fw('', 'id: check.1\ncurrent: 1.2.33\nlatest: 1.2.34\nurl: https://x/cyberponk-v1.2.34.bin\ndate: 2026-11-10\nnotes: Fixes <b>\nnotes: more\nstate: available\n');
assert(f.el('niUpState').innerHTML.indexOf('1.2.34') >= 0); assert.equal(f.el('niUpInstall').style.display, '');
assert.equal(f.el('niUpNotes').innerHTML, 'Fixes &lt;b&gt;\nmore');
vm.runInContext("fwOnline('install')", f.ctx);
const uw = f.calls[f.calls.length - 1]; assert(/^up:Device_FwUpdate=install\.\d+$/.test(uw), uw);
assert.equal(f.el('niUpCheck').style.display, 'none');
const id = uw.split('=')[1];
f.tick(); f.x.readyState = 4; f.x.status = 200; f.x.responseText = 'id: ' + id + '\ncurrent: 1.2.33\nstep: downloading\n'; f.x.onreadystatechange();
assert(f.tick); assert(/\.\.\./.test(f.el('niUpState').innerHTML));
f.tick(); f.x.readyState = 4; f.x.status = 200; f.x.responseText = 'id: ' + id + '\nerror: download failed (x)\nstate: error\n'; f.x.onreadystatechange();
assert(!f.tick); assert(/download failed/.test(f.el('niUpState').innerHTML)); assert.equal(f.el('niUpCheck').style.display, '');
console.log('firmware ok:', dir);
// --- config_backup: every CGI call writes a fresh one-time ticket first
{
  const xs = [];
  global.XMLHttpRequest = function() { this.open = (m, u) => { this.m = m; this.u = u; }; this.send = b => { this.b = b; xs.push(this); };
    this.getResponseHeader = () => 'text/plain'; };
  const reply = (x, t) => { x.readyState = 4; x.status = 200; x.responseText = t; x.onreadystatechange(); };
  global.confirm = () => true; global.location = { host: "192.0.2.10" }; global.window = {};
  c = load(dir + '/config_backup.htm', { 'token=Device_SettingsTicket': '{"t":"bk"}' });
  assert.equal(xs.length, 1); assert(/^http:\/\/192\.0\.2\.10:8090\/settings\?t=[0-9a-f]{32}&a=list$/.test(xs[0].u), xs[0].u);
  assert.equal(c.calls[0].write.Device_SettingsTicket, xs[0].u.match(/t=([0-9a-f]+)/)[1]);
  reply(xs[0], 'ok\n1794322230|2026-11-10 14:50 BRT|cyberponk-v1.2.35|<b>x</b>\n\n');
  assert(/&lt;b&gt;x/.test(c.el('list').innerHTML)); assert(/data-id="1794322230"/.test(c.el('list').innerHTML));
  c.el('desc').value = '  '; c.handlers['#save'](); assert.equal(xs.length, 1); assert(c.msgs[0].startsWith('E:'));
  c.el('desc').value = 'before Wi-Fi'; c.handlers['#save'](); assert.equal(xs[1].m, 'POST'); assert.equal(xs[1].b, 'before Wi-Fi');   // no Blob in node
  assert.notEqual(xs[1].u.match(/t=([0-9a-f]+)/)[1], xs[0].u.match(/t=([0-9a-f]+)/)[1]);
  reply(xs[1], 'error: already 20 saved settings, delete one first\n'); assert(/already 20/.test(c.msgs[c.msgs.length - 1]));
  c.el('file').files = [{ name: 'x.tar' }]; c.handlers['#upload'](); assert(/a=upload$/.test(xs[2].u));
  reply(xs[2], 'ok\ndate=2026-11-10\nfirmware=cyberponk-v1.2.35\ndescription=\n'); assert(/a=apply$/.test(xs[3].u));
  reply(xs[3], 'ok\n'); assert.equal(c.el('main').style.display, 'none');
  const e = { target: { getAttribute: k => ({ 'data-id': '1794322230', 'data-act': 'delete' })[k] }, preventDefault() {} };
  c.el('list').onclick(e); assert(/a=delete&id=1794322230$/.test(xs[4].u));
  console.log('backup ok:', dir);
}
