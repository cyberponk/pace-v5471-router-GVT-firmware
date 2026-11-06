"""Setting descriptions for the stock web pages (en_US and pt_BR pages are separate files).

Each entry: (kind, en_anchor, pt_anchor, en_text, pt_text). The anchor is the start of the
label as it appears in the page source; it must match exactly once, so a changed page fails
the build instead of silently losing a description.
  td      <td ...>[<strong>]anchor ... </td>      text added before the cell's </td>
  th      <th ...>anchor ... </th>                text in a new full-width row under the heading row
  label   <label>anchor</label>                   text added after </label>
  strong  <strong>anchor</strong>                  text added after </strong>
  replace <td>anchor[^<]*</td>                     the cell text is replaced by the text
The cyberponk pages (tools/overlay) carry their descriptions in the HTML itself.
"""
import re
import sys

PAGES = {
    'config_lan.htm': [
        ('td', 'DHCP Server:', 'Servidor DHCP:',
         'Hands out IP addresses to the devices on the local network. Turn it off only if another device on the network does this.',
         'Distribui endereços IP para os dispositivos da rede local. Desligue só se outro aparelho da rede fizer isso.'),
        ('td', 'Router IP Address:', 'Endereço IP do Roteador:',
         'Address of this router on the local network, also used to open this web interface. After a change, reconnect at the new address.',
         'Endereço deste roteador na rede local, também usado para abrir esta interface. Depois de alterar, conecte no novo endereço.'),
        ('td', 'Net Mask:', 'Máscara de Rede:',
         'Size of the local network. 255.255.255.0 allows up to 254 devices.',
         'Tamanho da rede local. 255.255.255.0 permite até 254 dispositivos.'),
        ('td', 'Address Range:', 'Faixa de Endereçamento:',
         'First and last address the DHCP server hands out. Give devices with a fixed address an address outside this range.',
         'Primeiro e último endereço distribuído pelo servidor DHCP. Dispositivos com endereço fixo devem usar um endereço fora desta faixa.'),
        ('td', 'Specific DNS Server:', 'Servidor DNS Específico:',
         'Off: devices use the router as DNS server (it asks the DNS of the Internet connection). On: devices get the servers below instead.',
         'Desligado: os dispositivos usam o roteador como DNS (ele consulta o DNS da conexão de Internet). Ligado: os dispositivos recebem os servidores abaixo.'),
        ('td', 'Primary DNS Server:', 'Servidor DNS Primário:',
         'DNS server handed to the devices when Specific DNS Server is on.',
         'Servidor DNS entregue aos dispositivos quando Servidor DNS Específico está ligado.'),
        ('td', 'Secondary DNS Server:', 'Servidor DNS Secundário:',
         'Optional second DNS server, used when the primary one does not answer.',
         'Segundo servidor DNS opcional, usado quando o primário não responde.'),
        ('td', 'Lease Time:', 'Período de Concessão do DHCP:',
         'How long, in seconds, a device keeps its address before renewing it (86400 = 1 day).',
         'Por quanto tempo, em segundos, um dispositivo mantém o endereço antes de renová-lo (86400 = 1 dia).'),
        ('th', 'CREATE AN IP RESERVATION', 'CRIAR RESERVA NO DHCP',
         'Always give the same IP address to a device, identified by its MAC address.',
         'Entrega sempre o mesmo endereço IP a um dispositivo, identificado pelo endereço MAC.'),
        ('th', 'LEASE TABLE', 'TABELA DE CONCESSÃO DHCP',
         'Devices that currently have an address from the DHCP server.',
         'Dispositivos que receberam endereço do servidor DHCP.'),
        ('td', 'Rule Name:', 'Nome da Regra:',
         'A name for this rule, for your reference.',
         'Um nome para esta regra, para sua referência.'),
        ('td', 'Protocol:', 'Protocolo:',
         'Type of traffic to forward: TCP, UDP or both.',
         'Tipo de tráfego a redirecionar: TCP, UDP ou ambos.'),
        ('td', 'Source Port:', 'Porta(s) de Origem:',
         'Port or range on the Internet side (this router\'s public address) that is forwarded.',
         'Porta ou faixa no lado da Internet (endereço público deste roteador) que é redirecionada.'),
        ('td', 'Destination Port:', 'Porta(s) de Destino:',
         'Port on the local device that receives the connections. Empty = same as the source port.',
         'Porta no dispositivo local que recebe as conexões. Vazio = a mesma da origem.'),
        ('td', 'Source IP:', 'IP de Origem:',
         'Accept connections only from this Internet address. Empty = from anywhere.',
         'Aceita conexões só deste endereço da Internet. Vazio = de qualquer lugar.'),
        ('td', 'Destination IP:', 'IP de Destino:',
         'Local device that receives the forwarded connections. Give it a fixed address (IP reservation).',
         'Dispositivo local que recebe as conexões redirecionadas. Dê a ele um endereço fixo (reserva de IP).'),
        ('td', 'DMZ State:', 'Estado do DMZ:',
         'Sends every incoming connection that no other rule handles to one local device. That device is fully exposed to the Internet: use with care.',
         'Envia toda conexão de entrada que nenhuma outra regra trata para um dispositivo local. Esse dispositivo fica totalmente exposto à Internet: use com cuidado.'),
        ('td', 'IP Address:', 'Endereço de IP:',
         'Local device that receives the DMZ traffic.',
         'Dispositivo local que recebe o tráfego do DMZ.'),
        ('td', 'UPNP State:', 'Estado do UPNP:',
         'Lets devices and apps (games, consoles, video calls) open ports on the router by themselves.',
         'Permite que dispositivos e aplicativos (jogos, consoles, chamadas de vídeo) abram portas no roteador sozinhos.'),
    ],
    'config_wireless.htm': [
        ('td', 'Private Wi-Fi Network:', 'Rede Wi-Fi Privada:',
         'Turns the Wi-Fi network on or off.',
         'Liga ou desliga a rede Wi-Fi.'),
        ('td', 'SSID Broadcast:', 'Anúncio de SSID:',
         'On: the network name shows up in Wi-Fi lists. Off: hidden, devices have to type the name to join.',
         'Ligado: o nome da rede aparece nas listas de Wi-Fi. Desligado: oculto, é preciso digitar o nome para conectar.'),
        ('td', 'SSID:', 'SSID:',
         'Network name shown to devices (up to 32 characters).',
         'Nome da rede mostrado aos dispositivos (até 32 caracteres).'),
        ('td', 'Password:', 'Senha:',
         'Wi-Fi password (WPA/WPA2: 8 to 63 characters).',
         'Senha do Wi-Fi (WPA/WPA2: 8 a 63 caracteres).'),
        ('td', 'Security Mode:', 'Modo de Segurança:',
         'Encryption of the network. WPA2 (AES) is recommended; WEP and open networks are not safe.',
         'Criptografia da rede. WPA2 (AES) é o recomendado; WEP e rede aberta não são seguros.'),
        ('td', 'WPS:', 'WPS:',
         'Connect devices with a button or a PIN instead of the password. Less safe; off by default.',
         'Conecta dispositivos com um botão ou PIN em vez da senha. Menos seguro; desligado por padrão.'),
        ('td', 'Register Mode - WPS:', 'Modo de Registro - WPS:',
         'Button: press Push Button here and the WPS button on the device within 2 minutes. PIN: enter the device\'s WPS PIN below.',
         'Botão: clique em Push Button aqui e no botão WPS do dispositivo em até 2 minutos. PIN: digite abaixo o PIN WPS do dispositivo.'),
        ('td', 'Pin Number:', 'Código Numérico:',
         'WPS PIN shown by the device you want to connect.',
         'PIN WPS mostrado pelo dispositivo que você quer conectar.'),
        ('td', 'Operation Mode:', 'Modo de Operação:',
         'Wi-Fi standards accepted (802.11b/g/n). Mixed modes keep old devices working; n only is faster but leaves them out.',
         'Padrões de Wi-Fi aceitos (802.11b/g/n). Os modos mistos mantêm aparelhos antigos funcionando; somente n é mais rápido mas os exclui.'),
        ('td', 'Channel:', 'Canal:',
         'Radio channel (2.4 GHz). Auto picks the least busy one; 1, 6 and 11 do not overlap each other.',
         'Canal de rádio (2,4 GHz). Automático escolhe o menos ocupado; 1, 6 e 11 não se sobrepõem.'),
        ('td', 'Channel Bandwidth:', 'Largura de Banda do Canal:',
         '20 MHz is more reliable where there are many networks; 40 MHz is faster with a good signal.',
         '20 MHz é mais estável onde há muitas redes; 40 MHz é mais rápido com bom sinal.'),
        ('td', 'Transmit Power:', 'Potência Transmitida [%]:',
         'Radio power in percent. Lower it to reduce the range or the interference with neighbours.',
         'Potência do rádio em porcentagem. Diminua para reduzir o alcance ou a interferência com vizinhos.'),
        ('td', 'WMM:', 'WMM:',
         'Wi-Fi multimedia: gives priority to voice and video. Needed for 802.11n speeds, keep it on.',
         'Multimídia Wi-Fi: dá prioridade a voz e vídeo. Necessário para as velocidades 802.11n, mantenha ligado.'),
        ('td', 'Power Saving - WMM:', 'Economia de Energia - WMM',
         'Lets battery devices sleep between transmissions to save power.',
         'Permite que aparelhos a bateria economizem energia entre as transmissões.'),
        ('td', 'MAC Address:', 'Endereço MAC:',
         'Hardware address of the Wi-Fi radio.',
         'Endereço físico do rádio Wi-Fi.'),
        ('td', 'Frequency Band:', 'Banda de Frequência:',
         'Radio band. This device has a 2.4 GHz radio only.',
         'Banda de rádio. Este aparelho tem só rádio de 2,4 GHz.'),
        ('td', 'MAC Filter:', 'Filtro de MAC',
         'Off: any device with the password can connect. On: the device list below is applied, as set in MAC filter mode (allow only them, or block them).',
         'Desligado: qualquer aparelho com a senha conecta. Ligado: a lista de aparelhos abaixo é aplicada, conforme o Modo do filtro de MAC (permitir só eles, ou bloqueá-los).'),
    ],
    'config_firewall.htm': [
        ('th', 'Set default policy', 'Politica Padrão',
         'What happens to traffic that matches no rule in the list: Accept lets it through, Reject blocks it.',
         'O que acontece com o tráfego que não corresponde a nenhuma regra da lista: Aceitar deixa passar, Rejeitar bloqueia.'),
        ('td', 'Rule Name:', 'Nome da Regra:',
         'A name for this rule, for your reference.',
         'Um nome para esta regra, para sua referência.'),
        ('td', 'Protocol:', 'Protocolo:',
         'Type of traffic the rule applies to.',
         'Tipo de tráfego ao qual a regra se aplica.'),
        ('td', 'Local Port:', 'Porta Local',
         'Port on the local network side.',
         'Porta no lado da rede local.'),
        ('td', 'Remote Port:', 'Porta Remota',
         'Port on the Internet side.',
         'Porta no lado da Internet.'),
        ('td', 'Local IP:', 'IP Local',
         'Address on the local network side.',
         'Endereço no lado da rede local.'),
        ('td', 'Remote IP:', 'IP Remoto',
         'Address on the Internet side.',
         'Endereço no lado da Internet.'),
        ('td', 'Policy:', 'Politica',
         'Accept or block the traffic that matches this rule.',
         'Aceitar ou bloquear o tráfego que corresponde a esta regra.'),
    ],
    'config_apps.htm': [
        ('strong', 'Device name or IP Address', 'Endereço IP de Destino',
         'Opens the ports a game or application needs and sends them to this device. Give the device a fixed address (IP reservation on the Local Network page).',
         'Abre as portas que um jogo ou aplicativo precisa e as envia para este dispositivo. Dê a ele um endereço fixo (reserva de IP na página Rede Local).'),
    ],
    'config_advanced.htm': [
        ('td', 'IPv6 Enable:', 'IPv6 Ativo:',
         'Turns IPv6 on for the router and the local network. Needs IPv6 from the Internet provider.',
         'Liga o IPv6 no roteador e na rede local. Precisa de IPv6 do provedor de Internet.'),
        ('td', 'Lan DHCPv6:', 'Lan DHCPv6:',
         'Also hands out IPv6 addresses by DHCPv6 on the local network, besides automatic configuration (SLAAC).',
         'Também distribui endereços IPv6 por DHCPv6 na rede local, além da configuração automática (SLAAC).'),
        ('td', 'Allow Remote Ping:', 'Permitir Ping Remoto:',
         'Answer pings sent from the Internet to the router\'s public address.',
         'Responde a pings enviados da Internet para o endereço público do roteador.'),
        ('td', 'Log Dropped:', 'Log Dropped:',
         'Write the blocked incoming packets to the system log (System Logs page).',
         'Registra os pacotes de entrada bloqueados no histórico do sistema (página Histórico).'),
        ('td', 'Attack Detection WAN 1:', 'Attack Detection WAN 1:',
         'Extra protection against common attacks from the Internet (port scans, floods), for IPv4 and IPv6.',
         'Proteção extra contra ataques comuns vindos da Internet (varreduras de porta, inundações), para IPv4 e IPv6.'),
        ('td', 'MDNSResponder:', 'MDNSResponder:',
         'Announces the router on the local network (Bonjour/mDNS), so devices can find it by name.',
         'Anuncia o roteador na rede local (Bonjour/mDNS), para os dispositivos o acharem pelo nome.'),
        ('td', 'Conntrack:', 'Conntrack:',
         'Connection tracking (the table of open connections used by NAT and the firewall). Filter: limits suspicious new connections. Status: keeps the table visible to the system.',
         'Rastreamento de conexões (a tabela de conexões abertas usada pelo NAT e pelo firewall). Filter: limita novas conexões suspeitas. Status: mantém a tabela visível para o sistema.'),
        ('td', 'Accelerator:', 'Accelerator:',
         'Hardware packet accelerator. On gives full speed between the WAN and the local network; turn it off only to troubleshoot.',
         'Acelerador de pacotes por hardware. Ligado dá a velocidade máxima entre a WAN e a rede local; desligue só para diagnóstico.'),
        ('td', 'QueueManagement:', 'QueueManagement:',
         'Traffic queues with priorities (QoS) on the Internet connection.',
         'Filas de tráfego com prioridades (QoS) na conexão de Internet.'),
    ],
    'languages.htm': [
        ('td', 'Choose the language of the Power Box user interface:',
         'Escolha o idioma que deseja utilizar na interface de configuração do Power Box:',
         'Language of this web interface. It does not change anything else on the device.',
         'Idioma desta interface web. Não altera mais nada no aparelho.'),
    ],
    'admin_password.htm': [
        ('label', 'Current Password:', 'Senha Atual:',
         'Password you use now to log in to this web interface (default after a reset: admin).',
         'Senha usada hoje para entrar nesta interface (padrão após reset: admin).'),
        ('label', 'New Password:', 'Nova Senha:',
         'New password for this web interface.',
         'Nova senha para esta interface.'),
        ('label', 'New Password (confirm):', 'Nova Senha (confirme):',
         'Type the new password again.',
         'Digite a nova senha de novo.'),
    ],
    'resets.htm': [
        ('replace', 'This button will reboot', 'Este botão reinicia',
         'Restarts the device. Internet and Wi-Fi stop for about 2 minutes; all settings are kept.',
         'Reinicia o aparelho. A Internet e o Wi-Fi param por cerca de 2 minutos; todas as configurações são mantidas.'),
        ('replace', 'This button will reconfigure', 'Este botão reconfigurá',
         'Restores the factory settings and restarts: access point mode, Wi-Fi settings and web password (admin) back to the defaults. Afterwards the device is at 169.254.25.1 or gets an address from your main router.',
         'Restaura as configurações de fábrica e reinicia: modo access point, Wi-Fi e senha da interface (admin) voltam ao padrão. Depois o aparelho fica em 169.254.25.1 ou recebe endereço do roteador principal.'),
    ],
    'logread.htm': [
        ('label', 'Event:', 'Último evento',
         'Show the messages of one module or severity only.',
         'Mostra só as mensagens de um módulo ou gravidade.'),
    ],
    'net_utils.htm': [
        ('td', 'Utility:', 'Ferramentas',
         'Ping: checks if an address answers and how fast. Traceroute: shows the path to it.',
         'Ping: verifica se um endereço responde e em quanto tempo. Traceroute: mostra o caminho até ele.'),
        ('td', 'Destination:', 'IP de Destino:',
         'Name or IP address to test, for example 8.8.8.8 or google.com.',
         'Nome ou endereço IP a testar, por exemplo 8.8.8.8 ou google.com.'),
        ('td', 'Number of pings:', 'Número de tentativas:',
         'How many test packets to send.',
         'Quantos pacotes de teste enviar.'),
        ('td', 'Packet Size:', 'Tamanho do Pacote:',
         'Size of each test packet in bytes.',
         'Tamanho de cada pacote de teste, em bytes.'),
    ],
    'firmware.htm': [
        ('td', 'Current firmware:', 'Firmware atual:',
         'Version running now.',
         'Versão em uso.'),
        ('td', 'New firmware:', 'Nova firmware:',
         'Image file (.bin) to install. It is written to the other flash bank; the current version stays as a fallback. The device restarts when done.',
         'Arquivo da imagem (.bin) a instalar. Ela é gravada no outro banco da flash; a versão atual fica como reserva. O aparelho reinicia ao terminar.'),
    ],
}

# stock text errors fixed first: (page, lang) -> [(wrong, right)]
FIXES = {
    # "Reservation List" heading was two other headings pasted together
    ('config_lan.htm', 'pt_BR'): [('CRIAR RESERVA NO DHCPTABELA DE CONCESSÃO DHCP', 'LISTA DE RESERVAS')],
}

CLOSE = {'td': '</td>', 'th': '</th>'}


def describe(page, lang, txt):
    for wrong, right in FIXES.get((page, lang), []):
        if txt.count(wrong) != 1:
            sys.exit(f'descriptions: {page} {lang} fix "{wrong}" not found once')
        txt = txt.replace(wrong, right)
    for kind, en, pt, en_text, pt_text in PAGES.get(page, []):
        anchor, text = (en, en_text) if lang == 'en_US' else (pt, pt_text)
        a = re.escape(anchor)
        if kind == 'replace':
            pat = r'(<td>)' + a + r'[^<]*(</td>)'
        elif kind in CLOSE:
            pat = r'<' + kind + r'[^>]*>\s*(?:<strong>\s*)?' + a
        elif kind == 'label':
            pat = r'<label[^>]*>\s*' + a + r'\s*</label>'
        else:  # strong
            pat = r'<strong>\s*' + a + r'\s*</strong>'
        found = list(re.finditer(pat, txt))
        if len(found) != 1:
            sys.exit(f'descriptions: {page} {lang} "{anchor}": {len(found)} matches')
        m = found[0]
        small = f'<small class="ni-desc">{text}</small>'
        if kind == 'replace':
            txt = txt[:m.start()] + m.group(1) + text + m.group(2) + txt[m.end():]
        elif kind == 'th':
            # own row under the heading: after the heading's </tr>, or after </thead> when the
            # heading has no <tr> (the browser makes one); spans what the heading spans
            span = re.search(r'colspan="?(\d+)', txt[m.start():m.end()])
            span = span.group(1) if span else '1'
            close = txt.find('</th>', m.end())
            nxt = re.compile(r'\s*(</tr>|</thead>)').match(txt, close + 5)
            if not nxt:
                sys.exit(f'descriptions: {page} {lang} "{anchor}": no </tr> or </thead> after the heading')
            row = f'<tr><td class="ni-desc-row" colspan="{span}">{text}</td></tr>'
            if nxt.group(1) == '</thead>':
                row = '<tbody>' + row + '</tbody>'
            txt = txt[:nxt.end()] + row + txt[nxt.end():]
        elif kind in CLOSE:
            end = txt.find(CLOSE[kind], m.end())
            txt = txt[:end] + small + txt[end:]
        else:
            txt = txt[:m.end()] + small + txt[m.end():]
    return txt
