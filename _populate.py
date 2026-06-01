#!/usr/bin/env python3
"""Наполнить сеть 6 гео: generate(async) -> wait -> local vision audit -> /score."""
import json, time, subprocess, urllib.request, os, sys

B = "https://cricket360-india-j49veu.saturn.ac"
UA = "Mozilla/5.0 (Macintosh) Chrome/120"

SITES = [
    ("crashbet-bd", "CrashBet", "bd", "crash gambling bangladesh"),
    ("royalspin-uk", "RoyalSpin", "uk", "online casino uk"),
    ("fortunetiger-br", "FortuneTiger", "br", "cassino online brasil"),
    ("megaslots-ng", "MegaSlots", "ng", "online casino nigeria"),
    ("aviatorwin-in", "AviatorWin", "in", "aviator game india"),
    ("luckyjet-in", "LuckyJet", "in", "lucky jet india"),
]

def req(path, method="GET", body=None):
    data = json.dumps(body).encode() if body else None
    r = urllib.request.Request(B + path, data=data, method=method,
                               headers={"User-Agent": UA, "Content-Type": "application/json"})
    try:
        return urllib.request.urlopen(r, timeout=30).read().decode()
    except Exception as e:
        return f"ERR:{e}"

# 1) trigger all generates
for dom, brand, geo, kw in SITES:
    res = req("/generate", "POST", {"domain": dom, "brand": brand, "geo": geo})
    print(f"GEN {brand}/{geo}: {res[:80]}")

print("waiting 120s for async builds...")
time.sleep(120)

# 2) verify each site is up
for dom, brand, geo, kw in SITES:
    for attempt in range(6):
        c = req(f"/site/{dom}/index.html")
        if not c.startswith("ERR") and "<" in c[:200]:
            print(f"  {dom}: UP")
            break
        time.sleep(15)
    else:
        print(f"  {dom}: NOT UP after retries")

print("DONE generate phase")
