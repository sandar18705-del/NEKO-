#!/data/data/com.termux/files/usr/bin/bash

echo -e "\033[92m[*] S7-WIFI-PRO အား ထည့်သွင်းနေပါသည်...\033[0m"

# ၁။ လိုအပ်တဲ့ Python နဲ့ Library တွေ သွင်းမယ်
pkg update && pkg upgrade -y
pkg install python -y
pip install requests

# ၂။ Folder အဟောင်းရှိရင် ဖျက်ပြီး အသစ်ဆောက်မယ်
rm -rf ~/NEKO-
mkdir -p ~/NEKO-
cd ~/NEKO-




# ၄။ Starter ဖိုင်ကို ဒေါင်းမယ်
curl -LO https://raw.githubusercontent.com/sandar18705-del/NEKO-/main/internet.py

