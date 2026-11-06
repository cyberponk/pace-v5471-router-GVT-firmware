"""pt_BR strings for the overlay web pages (generated from the en_US sources by configure.py).

Each key must occur in the page it is listed for; translate() fails otherwise,
so a changed English string cannot silently stay untranslated.
"""

COMMON = {
    '<title>Pace v5471</title>': '<title>Pace v5471</title>',
    '>Cancel<': '>Cancelar<',
    '>Save<': '>Salvar<',
    "'Settings saved.'": "'Configuração salva.'",
    '>Settings<': '>Configuração<',
}

PAGES = {
    'config_ap.htm': {
        '<small class="ni-desc"><b>Access point:</b><br/>Wi-Fi and LAN ports are handed over to the main router, connected to a LAN port.<br/><br/><b>Router:</b><br/>Router mode with Internet on the WAN port, DHCP server, firewall, NAT, Wi-Fi, USB tethering failover.</small>':
            '<small class="ni-desc"><b>Access point:</b><br/>Wi-Fi e portas LAN são transferidos ao roteador principal, conectado a uma porta LAN.<br/><br/><b>Roteador:</b><br/>Modo roteador com internet pela porta WAN, servidor DHCP, firewall, NAT, Wi-Fi, failover pela ancoragem USB.</small>',
        '<small class="ni-desc">How this access point gets its management address: by DHCP from the main router, or a fixed address.</small>':
            '<small class="ni-desc">Como este access point recebe o endereço de gerência: por DHCP do roteador principal, ou um endereço fixo.</small>',
        '<small class="ni-desc">Fixed address of this access point on your network, outside the DHCP range of the main router.</small>':
            '<small class="ni-desc">Endereço fixo deste access point na sua rede, fora da faixa DHCP do roteador principal.</small>',
        '<small class="ni-desc">Same mask as your main network, usually 255.255.255.0.</small>':
            '<small class="ni-desc">A mesma máscara da rede principal, normalmente 255.255.255.0.</small>',
        '<small class="ni-desc">Address of your main router; used for the device\'s own Internet access (time, updates).</small>':
            '<small class="ni-desc">Endereço do roteador principal; usado para o próprio acesso do aparelho à Internet (hora, atualizações).</small>',
        '<small class="ni-desc">DNS servers for the device itself. Empty = use the gateway.</small>':
            '<small class="ni-desc">Servidores DNS do próprio aparelho. Vazio = usar o gateway.</small>',
        "'Please provide a valid IP address.'": "'Informe um endereço IP válido.'",
        "'Please provide a valid subnet mask.'": "'Informe uma máscara de sub-rede válida.'",
        "'Please provide a valid gateway address.'": "'Informe um gateway válido.'",
        "'DNS servers must be IP addresses separated by commas.'":
            "'Os servidores DNS devem ser endereços IP separados por vírgula.'",
        """'Settings saved. If the address changed, reconnect to the new address (in DHCP mode, look for "PaceAP" in your main router client list, or use 169.254.25.1 with a direct cable).'""":
            """'Configuração salva. Se o endereço mudou, conecte no novo endereço (no modo DHCP, procure "PaceAP" na lista de clientes do roteador principal, ou use 169.254.25.1 com cabo direto).'""",
        "'Saving... the page may stop responding if the address changes.'":
            "'Salvando... a página pode parar de responder se o endereço mudar.'",
        "'The device is already in this mode.'": "'O aparelho já está neste modo.'",
        "'Mode saved. The device is rebooting, this takes about 2 minutes.'":
            "'Modo salvo. O aparelho está reiniciando, isso leva cerca de 2 minutos.'",
        "'After the reboot the device is a router: LAN 192.168.25.1, DHCP server on. Connect your PC to it and open http://192.168.25.1'":
            "'Após reiniciar o aparelho será um roteador: LAN 192.168.25.1, servidor DHCP ligado. Conecte o PC nele e abra http://192.168.25.1'",
        """'After the reboot the device is an access point: it gets its address by DHCP from your main router (look for "PaceAP"), or use 169.254.25.1 with a direct cable.'""":
            """'Após reiniciar o aparelho será um access point: recebe endereço por DHCP do roteador principal (procure "PaceAP"), ou use 169.254.25.1 com cabo direto.'""",
        '>Operating Mode<': '>Modo de Operação<',
        '>Mode<': '>Modo<',
        '>Current mode:<': '>Modo atual:<',
        '>Operating mode:<': '>Modo de operação:<',
        '>Access point (behind your main router)<': '>Access point (atrás do roteador principal)<',
        '>Router (WAN port or 3G modem)<': '>Roteador (porta WAN ou modem 3G)<',
        '<small>Changing the mode reboots the device. Router mode uses LAN 192.168.25.1 with DHCP server on; change it later under Local Network.</small>':
            '<small>Trocar o modo reinicia o aparelho. O modo roteador usa LAN 192.168.25.1 com servidor DHCP ligado; altere depois em Rede Local.</small>',
        '>Apply and reboot<': '>Aplicar e reiniciar<',
        "<p>Management address of this access point on your main router's network. Wi-Fi and LAN clients get their addresses from the main router.</p>":
            '<p>Endereço de gerenciamento deste access point na rede do roteador principal. Os clientes Wi-Fi e LAN recebem endereço do roteador principal.</p>',
        '>Current status<': '>Status atual<',
        '>IP address:<': '>Endereço IP:<',
        '>Subnet mask:<': '>Máscara de sub-rede:<',
        '>DNS servers:<': '>Servidores DNS:<',
        '>Rescue address:<': '>Endereço de resgate:<',
        '169.254.25.1 (direct cable)': '169.254.25.1 (cabo direto)',
        '>Address mode:<': '>Modo de endereço:<',
        '>Automatic (DHCP from main router)<': '>Automático (DHCP do roteador principal)<',
        '>Static<': '>Estático<',
        '>Gateway (main router):<': '>Gateway (roteador principal):<',
        '>DNS servers (optional):<': '>Servidores DNS (opcional):<',
        '<small>Comma separated. Empty = use the gateway.</small>':
            '<small>Separados por vírgula. Vazio = usar o gateway.</small>',
    },
    'config_3g.htm': {
        '<small class="ni-desc">Use a supported USB 3G modem when it is plugged in (router mode).</small>':
            '<small class="ni-desc">Usa um modem 3G USB suportado quando ele estiver ligado (modo roteador).</small>',
        '<small class="ni-desc">Which connection is the Internet: the WAN port or the 3G modem. USB tethering failover is set on the USB Devices page.</small>':
            '<small class="ni-desc">Qual conexão é a Internet: a porta WAN ou o modem 3G. O failover por ancoragem USB fica na página Dispositivos USB.</small>',
        '<small class="ni-desc">Access point name of your mobile operator (for example zap.vivo.com.br).</small>':
            '<small class="ni-desc">Nome do ponto de acesso da operadora (por exemplo zap.vivo.com.br).</small>',
        '<small class="ni-desc">Login of the mobile operator, if it requires one.</small>':
            '<small class="ni-desc">Usuário da operadora, se ela exigir.</small>',
        '<small class="ni-desc">Password of the mobile operator, if it requires one.</small>':
            '<small class="ni-desc">Senha da operadora, se ela exigir.</small>',
        '<small class="ni-desc">PIN of the SIM card, if it is locked. A wrong PIN can block the SIM.</small>':
            '<small class="ni-desc">PIN do chip, se ele estiver bloqueado. Um PIN errado pode bloquear o chip.</small>',
        '<small class="ni-desc">Number the modem dials to connect; usually *99#.</small>':
            '<small class="ni-desc">Número que o modem disca para conectar; normalmente *99#.</small>',
        '<small class="ni-desc">Which mobile networks the modem may use.</small>':
            '<small class="ni-desc">Quais redes móveis o modem pode usar.</small>',
        "'The PIN must be 4 to 8 digits (or empty).'": "'O PIN deve ter de 4 a 8 dígitos (ou ficar vazio).'",
        "'The device is in access point mode. Switch to router mode under Operating Mode to use the 3G modem.'":
            "'O aparelho está no modo access point. Mude para o modo roteador em Modo de Operação para usar o modem 3G.'",
        '>3G Modem<': '>Modem 3G<',
        '<p>USB 3G modem used as Internet connection in router mode. Supported:':
            '<p>Modem 3G USB usado como conexão de Internet no modo roteador. Suportados:',
        '>Modem status<': '>Status do modem<',
        '>Manufacturer:<': '>Fabricante:<',
        '>Product:<': '>Produto:<',
        '>SIM state:<': '>Estado do SIM:<',
        '>Signal strength:<': '>Intensidade do sinal:<',
        '>Registration:<': '>Registro:<',
        '>Access technology:<': '>Tecnologia de acesso:<',
        '>3G modem:<': '>Modem 3G:<',
        '>Internet source:<': '>Origem da Internet:<',
        '>WAN port<': '>Porta WAN<',
        '>3G modem<': '>Modem 3G<',
        '>Username:<': '>Usuário:<',
        '>Password:<': '>Senha:<',
        '<small>Leave empty to keep the current password.</small>':
            '<small>Deixe vazio para manter a senha atual.</small>',
        '>SIM PIN:<': '>PIN do SIM:<',
        '>Dial number:<': '>Número de discagem:<',
        '>Network preference:<': '>Preferência de rede:<',
        '>3G preferred<': '>3G preferencial<',
        '>3G only<': '>Somente 3G<',
        '>2G preferred<': '>2G preferencial<',
        '>2G only<': '>Somente 2G<',
    },
    'config_internet.htm': {
        '<small class="ni-desc">PPPoE: fiber/DSL modem in bridge mode, with an account from the provider. DHCP: the modem or another router gives the address. Fixed IP: address given by the provider.</small>':
            '<small class="ni-desc">PPPoE: modem de fibra/DSL em modo bridge, com conta do provedor. DHCP: o modem ou outro roteador entrega o endereço. IP fixo: endereço informado pelo provedor.</small>',
        '<small class="ni-desc">PPPoE user name given by the provider (often user@provider).</small>':
            '<small class="ni-desc">Usuário PPPoE informado pelo provedor (muitas vezes usuario@provedor).</small>',
        '<small class="ni-desc">PPPoE password given by the provider.</small>':
            '<small class="ni-desc">Senha PPPoE informada pelo provedor.</small>',
        '<small class="ni-desc">PPPoE service name; only some providers use it.</small>':
            '<small class="ni-desc">Nome do serviço PPPoE; só alguns provedores usam.</small>',
        '<small class="ni-desc">Fixed public or WAN address given by the provider.</small>':
            '<small class="ni-desc">Endereço público ou WAN fixo informado pelo provedor.</small>',
        '<small class="ni-desc">Mask given by the provider.</small>':
            '<small class="ni-desc">Máscara informada pelo provedor.</small>',
        '<small class="ni-desc">Provider router the Internet traffic is sent to.</small>':
            '<small class="ni-desc">Roteador do provedor para onde o tráfego de Internet é enviado.</small>',
        '<small class="ni-desc">Name servers used by the router and handed to the devices.</small>':
            '<small class="ni-desc">Servidores de nomes usados pelo roteador e entregues aos dispositivos.</small>',
        '<small class="ni-desc">Some fiber providers require the Internet traffic to carry a VLAN number. Off = normal Ethernet (DHCP from another router, most modems).</small>':
            '<small class="ni-desc">Alguns provedores de fibra exigem que o tráfego de Internet leve um número de VLAN. Desligado = Ethernet normal (DHCP de outro roteador, a maioria dos modems).</small>',
        '<small class="ni-desc">VLAN number required by the provider.</small>':
            '<small class="ni-desc">Número da VLAN exigido pelo provedor.</small>',
        '<small class="ni-desc">Use another MAC address on the WAN port, for providers or modems that only accept the device registered before.</small>':
            '<small class="ni-desc">Usa outro endereço MAC na porta WAN, para provedores ou modems que só aceitam o aparelho cadastrado antes.</small>',
        '<small class="ni-desc">MAC address to use on the WAN port.</small>':
            '<small class="ni-desc">Endereço MAC a usar na porta WAN.</small>',
        "'Please enter the PPPoE account.'": "'Informe a conta PPPoE.'",
        "'The VLAN ID must be a number from 1 to 4094.'": "'O ID da VLAN deve ser um número de 1 a 4094.'",
        "'Please enter the MAC address as six hex pairs, like 00:11:22:33:44:55.'":
            "'Informe o endereço MAC como seis pares hexadecimais, por exemplo 00:11:22:33:44:55.'",
        "'Please provide a valid IP address.'": "'Informe um endereço IP válido.'",
        "'Please provide a valid subnet mask.'": "'Informe uma máscara de sub-rede válida.'",
        "'Please provide a valid gateway address.'": "'Informe um gateway válido.'",
        "'DNS servers must be IP addresses separated by commas.'":
            "'Os servidores DNS devem ser endereços IP separados por vírgula.'",
        "'Settings saved. The Internet connection restarts.'": "'Configuração salva. A conexão de Internet será reiniciada.'",
        "'Monitoring addresses must be 1 to 4 IP addresses separated by commas.'":
            "'Os endereços de monitoramento devem ser de 1 a 4 endereços IP separados por vírgula.'",
        '>Internet check<': '>Verificação de Internet<',
        '<td width="250">Monitoring addresses:<small class="ni-desc">Pinged every 5 seconds through the WAN and through the USB phone to check that the Internet works: the WAN counts as down when none of them answers. Up to 4 IP addresses separated by commas (default 1.1.1.1, 8.8.8.8).</small>':
            '<td width="250">Endereços de monitoramento:<small class="ni-desc">Recebem ping a cada 5 segundos pela WAN e pelo celular USB para verificar se a Internet funciona: a WAN é considerada fora quando nenhum responde. Até 4 endereços IP separados por vírgula (padrão 1.1.1.1, 8.8.8.8).</small>',
        '<td width="250">Isolate from the WAN-side network:<small class="ni-desc">On: computers on this router\'s network can\'t reach the devices of the network the WAN port is connected to (for example the other router\'s network); the Internet keeps working. Off: they can, like any other address.</small>':
            '<td width="250">Isolar da rede do lado WAN:<small class="ni-desc">Ligado: os computadores da rede deste roteador não acessam os aparelhos da rede ligada à porta WAN (por exemplo a rede do outro roteador); a Internet continua funcionando. Desligado: acessam, como qualquer outro endereço.</small>',
        "'The device is in access point mode: the WAN port is not used. Switch to router mode under Operating Mode.'":
            "'O aparelho está no modo access point: a porta WAN não é usada. Mude para o modo roteador em Modo de Operação.'",
        "'Connected'": "'Conectado'",
        "'Not connected'": "'Não conectado'",
        '<td width="250">DNS over TLS:<small class="ni-desc">The router sends the name lookups of all devices encrypted (TLS, port 853) to the chosen provider, so the Internet provider and the network on the WAN side can neither read nor change them. Off: the DNS servers of the connection are used, unencrypted.</small>':
            '<td width="250">DNS sobre TLS:<small class="ni-desc">O roteador envia as consultas de nomes de todos os aparelhos criptografadas (TLS, porta 853) ao provedor escolhido, assim o provedor de Internet e a rede do lado WAN não conseguem ler nem alterar. Desligado: são usados os servidores DNS da conexão, sem criptografia.</small>',
        '>Off<': '>Desligado<',
        '>Quad9 (9.9.9.9, blocks malicious sites)<': '>Quad9 (9.9.9.9, bloqueia sites maliciosos)<',
        '<td width="250">DNS rebinding protection:<small class="ni-desc">Answers that point an Internet name to a private address (192.168.x.x, 10.x.x.x...) are dropped, so a web page can\'t use your browser to reach the router or other local devices. Local names (.local, .lan, .home, .home.arpa, .internal) are allowed.</small>':
            '<td width="250">Proteção contra DNS rebinding:<small class="ni-desc">Respostas que apontam um nome da Internet para um endereço privado (192.168.x.x, 10.x.x.x...) são descartadas, assim uma página web não consegue usar o seu navegador para acessar o roteador ou outros aparelhos locais. Nomes locais (.local, .lan, .home, .home.arpa, .internal) são permitidos.</small>',
        '<p>Internet connection on the WAN port (router mode). With USB tethering failover on (USB Devices page), a phone plugged into the USB port takes over while this connection is down.</p>':
            '<p>Conexão de Internet na porta WAN (modo roteador). Com o failover por ancoragem USB ativado (página Dispositivos USB), um celular ligado na porta USB assume enquanto esta conexão estiver fora.</p>',
        '>Connection status<': '>Status da conexão<',
        '>Status:<': '>Status:<',
        '>IP address:<': '>Endereço IP:<',
        '>Gateway:<': '>Gateway:<',
        '>DNS:<': '>DNS:<',
        '>Connection<': '>Conexão<',
        '>Connection type:<': '>Tipo de conexão:<',
        '>DHCP (automatic IP)<': '>DHCP (IP automático)<',
        '>Fixed IP<': '>IP fixo<',
        '>Account:<': '>Conta:<',
        '>Password:<': '>Senha:<',
        '<small>Leave empty to keep the current password.</small>': '<small>Deixe vazio para manter a senha atual.</small>',
        '<small>No password</small>': '<small>Sem senha</small>',
        '>Service name:<': '>Nome do serviço:<',
        '<small>Optional. Leave empty unless your provider requires one.</small>':
            '<small>Opcional. Deixe vazio, a menos que o provedor exija.</small>',
        '>Subnet mask:<': '>Máscara de sub-rede:<',
        '>DNS servers:<': '>Servidores DNS:<',
        '<small>Separated by commas.</small>': '<small>Separados por vírgula.</small>',
        '>WAN port<': '>Porta WAN<',
        '>VLAN tag:<': '>Tag de VLAN:<',
        '>VLAN ID:<': '>ID da VLAN:<',
        '<small>Only if your provider requires it (for example 600 for Vivo/GVT).</small>':
            '<small>Somente se o provedor exigir (por exemplo 600 para Vivo/GVT).</small>',
        '>MAC address clone:<': '>Clonar endereço MAC:<',
        '>MAC address:<': '>Endereço MAC:<',
        '<small>For example the address of your previous router.</small>':
            '<small>Por exemplo o endereço do seu roteador anterior.</small>',
    },
    'ddns_log.htm': {},
    'ntp_log.htm': {},
    'config_ntp.htm': {
        "'NTP servers must be 1 to 4 host names or IP addresses separated by commas.'":
            "'Os servidores NTP devem ser de 1 a 4 nomes ou endereços IP separados por vírgula.'",
        "'Please enter a time zone in POSIX format, for example BRT3 or CET-1CEST,M3.5.0,M10.5.0/3.'":
            "'Informe um fuso horário no formato POSIX, por exemplo BRT3 ou CET-1CEST,M3.5.0,M10.5.0/3.'",
        "'Synchronizing...'": "'Sincronizando...'",
        "'Synchronization finished, see the log below.'": "'Sincronização concluída, veja o registro abaixo.'",
        "'No answer from the router after 60 seconds.'": "'Sem resposta do roteador após 60 segundos.'",
        "'Yes'": "'Sim'",
        "'Not yet'": "'Ainda não'",
        "'Local network (the main router), access point mode'": "'Rede local (o roteador principal), modo access point'",
        "'Internet connection (WAN), router mode'": "'Conexão de Internet (WAN), modo roteador'",
        "'No synchronization run from this page yet.'": "'Nenhuma sincronização feita por esta página ainda.'",
        '<h3 class="text-up">NTP Server</h3>': '<h3 class="text-up">Servidor NTP</h3>',
        "<p>Sets the router's clock from Internet time servers (NTP) at every connection and once a day, and the time zone used for the logs and the schedules. HTTPS (dynamic DNS, DNS over TLS) needs the right date to check certificates.</p>":
            '<p>Acerta o relógio do roteador pelos servidores de hora da Internet (NTP) a cada conexão e uma vez por dia, e define o fuso horário usado nos registros e agendamentos. O HTTPS (DNS dinâmico, DNS sobre TLS) precisa da data certa para verificar certificados.</p>',
        '<tr><th colspan="2">Status</th></tr>': '<tr><th colspan="2">Status</th></tr>',
        '>Router time:<': '>Hora do roteador:<',
        '>Synchronized:<': '>Sincronizado:<',
        '>Synchronized through:<': '>Sincronizado por:<',
        '<td width="250">Time synchronization:<small class="ni-desc">On: the clock is set from the servers below. Off: the clock starts at a fixed date at every boot.</small>':
            '<td width="250">Sincronização de hora:<small class="ni-desc">Ligado: o relógio é acertado pelos servidores abaixo. Desligado: o relógio começa numa data fixa a cada reinício.</small>',
        '<td width="250">NTP servers:<small class="ni-desc">Up to 4 time servers, by name or IP address, separated by commas (default 0.pool.ntp.org, 1.pool.ntp.org, 2.pool.ntp.org; a.ntp.br is the Brazilian one). The interface follows the operating mode: the local network in access point mode, the Internet connection in router mode.</small>':
            '<td width="250">Servidores NTP:<small class="ni-desc">Até 4 servidores de hora, por nome ou endereço IP, separados por vírgula (padrão 0.pool.ntp.org, 1.pool.ntp.org, 2.pool.ntp.org; a.ntp.br é o brasileiro). A interface segue o modo de operação: a rede local no modo access point, a conexão de Internet no modo roteador.</small>',
        '<td width="250">Time zone:<small class="ni-desc">Local time shown by the router. Brazil has no daylight saving time since 2019.</small>':
            '<td width="250">Fuso horário:<small class="ni-desc">Hora local mostrada pelo roteador. O Brasil não tem horário de verão desde 2019.</small>',
        '>Brasília (UTC-3): South, Southeast, Northeast, Goiás, Pará<': '>Brasília (UTC-3): Sul, Sudeste, Nordeste, Goiás, Pará<',
        '>Amazon (UTC-4): Amazonas, Mato Grosso, Rondônia, Roraima<': '>Amazonas (UTC-4): Amazonas, Mato Grosso, Rondônia, Roraima<',
        '>Lisbon (UTC+0, summer time)<': '>Lisboa (UTC+0, horário de verão)<',
        '>London (UTC+0, summer time)<': '>Londres (UTC+0, horário de verão)<',
        '>Central Europe (UTC+1, summer time)<': '>Europa Central (UTC+1, horário de verão)<',
        '>US Eastern (UTC-5, summer time)<': '>EUA Leste (UTC-5, horário de verão)<',
        '>US Central (UTC-6, summer time)<': '>EUA Central (UTC-6, horário de verão)<',
        '>US Mountain (UTC-7, summer time)<': '>EUA Montanha (UTC-7, horário de verão)<',
        '>US Pacific (UTC-8, summer time)<': '>EUA Pacífico (UTC-8, horário de verão)<',
        '>Other (POSIX TZ string)<': '>Outro (texto TZ POSIX)<',
        '<td width="250">Time zone (POSIX):<small class="ni-desc">Name and offset west of UTC, optionally the summer time name and rules, for example BRT3 or CET-1CEST,M3.5.0,M10.5.0/3.</small>':
            '<td width="250">Fuso horário (POSIX):<small class="ni-desc">Nome e diferença a oeste do UTC, opcionalmente o nome e as regras do horário de verão, por exemplo BRT3 ou CET-1CEST,M3.5.0,M10.5.0/3.</small>',
        '>Update now<': '>Atualizar agora<',
        '<tr><th>Synchronization log</th></tr>': '<tr><th>Registro de sincronização</th></tr>',
        '<td class="ni-desc-row">Steps of the last synchronization started with Update now: interface and DNS used, the servers\' answers (offset and delay in seconds), the time before and after.</td>':
            '<td class="ni-desc-row">Passos da última sincronização feita com Atualizar agora: interface e DNS usados, as respostas dos servidores (diferença e atraso em segundos), a hora antes e depois.</td>',
    },
    'config_ddns.htm': {
        "token_d: 'HTTP token of the dynv6 account (Keys page). Leave empty to keep the stored one.'":
            "token_d: 'Token HTTP da conta dynv6 (página Keys). Deixe vazio para manter o salvo.'",
        "secret: 'Secret:'": "secret: 'Segredo:'",
        "secret_d: 'Secret of this host at nsupdate.info (shown when the host is created). Leave empty to keep the stored one.'":
            "secret_d: 'Segredo deste host no nsupdate.info (mostrado quando o host é criado). Deixe vazio para manter o salvo.'",
        "pass: 'Password:'": "pass: 'Senha:'",
        "pass_d: 'Password of that account. Leave empty to keep the stored one.'":
            "pass_d: 'Senha dessa conta. Deixe vazio para manter a salva.'",
        "host_d: 'Full name to update, for example myhome.dns.army or myhome.nsupdate.info.'":
            "host_d: 'Nome completo a atualizar, por exemplo minhacasa.dns.army ou minhacasa.nsupdate.info.'",
        "hostCp_d: 'Name this URL updates, for example myhome.example.com (shown in the list and the log). Empty = the server of the URL.'":
            "hostCp_d: 'Nome que esta URL atualiza, por exemplo minhacasa.exemplo.com.br (mostrado na lista e no registro). Vazio = o servidor da URL.'",
        "failed: 'Failed'": "failed: 'Falhou'",
        "running: 'Updating...'": "running: 'Atualizando...'",
        "never: 'Not done yet'": "never: 'Ainda não feita'",
        "disabled: 'Disabled'": "disabled: 'Desativado'",
        "'Please enter a valid hostname.'": "'Informe um hostname válido.'",
        "'Please enter the update URL (https://...).'": "'Informe a URL de atualização (https://...).'",
        "'Please enter the server name.'": "'Informe o nome do servidor.'",
        "'Please enter the username.'": "'Informe o usuário.'",
        "'Service added.'": "'Serviço adicionado.'",
        "'Service saved.'": "'Serviço salvo.'",
        "'Service removed.'": "'Serviço removido.'",
        "'Update finished, see the log below.'": "'Atualização concluída, veja o registro abaixo.'",
        "'No result after 90 seconds, see the System Logs page.'": "'Sem resultado após 90 segundos, veja a página Histórico.'",
        "'No update done yet.'": "'Nenhuma atualização feita ainda.'",
        "'No dynamic DNS service configured.'": "'Nenhum serviço de DNS dinâmico configurado.'",
        "edit: 'Edit'": "edit: 'Editar'",
        "update: 'Update now'": "update: 'Atualizar agora'",
        "remove: 'Remove'": "remove: 'Remover'",
        "pCustom: 'cPanel / custom URL'": "pCustom: 'cPanel / URL personalizada'",
        '>Dynamic DNS<': '>DNS Dinâmico<',
        "<p>Keeps names pointing to this router's public IP address, with one or more services. The new providers update over HTTPS with certificate checks (10 s timeout); the public address is read from a check-IP service, so it also works behind another router. All services are checked at every WAN connection and every 5 minutes.</p>":
            '<p>Mantém nomes apontando para o IP público deste roteador, com um ou mais serviços. Os novos provedores atualizam por HTTPS com verificação de certificado (tempo limite 10 s); o endereço público é obtido de um serviço de verificação de IP, então funciona também atrás de outro roteador. Todos os serviços são verificados a cada conexão WAN e a cada 5 minutos.</p>',
        '>Service<': '>Serviço<',
        '>Enabled:<small class="ni-desc">Updates this service. Off keeps it in the list without updating.</small>':
            '>Ativado:<small class="ni-desc">Atualiza este serviço. Desligado mantém na lista sem atualizar.</small>',
        '>Provider:<small class="ni-desc">Service where the name is registered.</small>':
            '>Provedor:<small class="ni-desc">Serviço onde o nome está registrado.</small>',
        '>cPanel / custom URL (GET)<': '>cPanel / URL personalizada (GET)<',
        '>Server:<small class="ni-desc">DynDNS 2 update server (dynv6.com for dns.army, dynv6.net and the other dynv6 domains).</small>':
            '>Servidor:<small class="ni-desc">Servidor de atualização DynDNS 2 (dynv6.com para dns.army, dynv6.net e os outros domínios dynv6).</small>',
        '>Update URL:<small class="ni-desc">Full update URL from the provider, for example the cPanel dynamic DNS URL. Called with HTTPS (http:// is changed to https://); the server takes the address the call comes from.</small>':
            '>URL de atualização:<small class="ni-desc">URL completa de atualização do provedor, por exemplo a URL de DNS dinâmico do cPanel. Chamada por HTTPS (http:// vira https://); o servidor usa o endereço de onde vem a chamada.</small>',
        '>Username:<small class="ni-desc">Your account at the provider.</small>':
            '>Usuário:<small class="ni-desc">Sua conta no provedor.</small>',
        '>Password:</span><small class="ni-desc" id="passDesc">Password of that account. Leave empty to keep the stored one.</small>':
            '>Senha:</span><small class="ni-desc" id="passDesc">Senha dessa conta. Deixe vazio para manter a salva.</small>',
        '>Hostname:<small class="ni-desc" id="hostDesc">Full name to update, for example myhome.dns.army or myhome.nsupdate.info.</small>':
            '>Hostname:<small class="ni-desc" id="hostDesc">Nome completo a atualizar, por exemplo minhacasa.dns.army ou minhacasa.nsupdate.info.</small>',
        '>Clear<': '>Limpar<',
        '>Add<': '>Adicionar<',
        '>Configured services<': '>Serviços configurados<',
        '>Current IP<': '>IP atual<',
        '>Last update<': '>Última atualização<',
        '>Actions<': '>Ações<',
        '>Update log<': '>Registro da atualização<',
        ">Steps of the last update: public address found, request sent (no passwords), provider's answer. The update button of a service updates it even if the address did not change.<":
            '>Etapas da última atualização: endereço público encontrado, pedido enviado (sem senhas), resposta do provedor. O botão de atualizar de um serviço atualiza mesmo se o endereço não mudou.<',
    },
    'config_usb.htm': {
        '<small class="ni-desc">Enabled: in router mode the phone takes over automatically while the WAN connection is down. Disabled: the phone is not used.</small>':
            '<small class="ni-desc">Ativado: no modo roteador o celular assume automaticamente enquanto a conexão WAN estiver fora. Desativado: o celular não é usado.</small>',
        '<small class="ni-desc">A printer plugged into the USB port can be used by the computers of the local network (IPP printing).</small>':
            '<small class="ni-desc">Uma impressora ligada na porta USB pode ser usada pelos computadores da rede local (impressão IPP).</small>',
        "'No phone connected'": "'Nenhum celular conectado'",
        "'Connected, waiting for an address'": "'Conectado, aguardando endereço'",
        "'Connected'": "'Conectado'",
        "'Connected, failover disabled'": "'Conectado, failover desativado'",
        "'The device is in access point mode: failover is used in router mode only.'":
            "'O aparelho está no modo access point: o failover só é usado no modo roteador.'",
        "'No USB device connected'": "'Nenhum dispositivo USB conectado'",
        "'Phone (USB tethering)'": "'Celular (ancoragem USB)'",
        "'Printer'": "'Impressora'",
        "'3G modem'": "'Modem 3G'",
        "'Storage (not supported)'": "'Armazenamento (não suportado)'",
        "'Other'": "'Outro'",
        '>USB Devices<': '>Dispositivos USB<',
        '>USB Tethering<': '>Ancoragem USB<',
        '<td colspan="2">In router mode, an Android phone plugged into the USB port with USB tethering on is kept ready as a backup Internet connection. While the WAN connection is down (no connection, or no answer from the Internet), all traffic goes through the phone; when the WAN answers again the router switches back. Switching takes about 15 seconds and open connections are restarted.</td>':
            '<td colspan="2">No modo roteador, um celular Android ligado na porta USB com a ancoragem USB ativada fica de reserva como conexão de Internet. Enquanto a conexão WAN estiver fora (sem conexão, ou sem resposta da Internet), todo o tráfego passa pelo celular; quando a WAN voltar a responder o roteador volta para ela. A troca leva cerca de 15 segundos e as conexões abertas são reiniciadas.</td>',
        '>USB tethering failover:<': '>Failover por ancoragem USB:<',
        '>Phone:<': '>Celular:<',
        '>Printers<': '>Impressoras<',
        '>Share USB printers on the network:<': '>Compartilhar impressoras USB na rede:<',
        '>Connected USB devices<': '>Dispositivos USB conectados<',
    },
}


def translate(name, src):
    table = dict(COMMON)
    table.update(PAGES[name])
    for en, pt in table.items():
        if en not in src:
            if en in COMMON:
                continue
            raise SystemExit(f'i18n: "{en[:60]}" not found in {name}')
        src = src.replace(en, pt)
    return src
