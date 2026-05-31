#!/usr/bin/env python3
"""Пул картинок: генерит hero+игры ОДИН РАЗ с упорными ретраями, сохраняет на диск.
Сборка сайта потом берёт готовые файлы — не зависит от живости Runware в момент.
Usage: python3 build_assets.py <geo>"""
import sys, os, time, urllib.request
from core.image_agent import gen_image
from core.keyword_taxonomy import GEO_FLAVOR

def fetch(url, path):
    for _ in range(3):
        try:
            urllib.request.urlretrieve(url, path); return True
        except Exception: time.sleep(2)
    return False

def gen_persistent(prompt, w, h, out, tries=6):
    if os.path.exists(out): return out
    for t in range(tries):
        try:
            url,_=gen_image(prompt, w, h)
            if fetch(url, out): print(f"  ✓ {os.path.basename(out)}"); return out
        except Exception as e:
            print(f"  retry {t+1}: {str(e)[:30]}"); time.sleep(3)
    print(f"  ✗ FAILED {os.path.basename(out)}"); return None

def build(geo):
    d=f"output/assets/{geo}"; os.makedirs(d, exist_ok=True)
    fl=GEO_FLAVOR.get(geo,{})
    print(f"=== assets для {geo} ===")
    gen_persistent(f"online casino banner {geo} theme, premium neon cinematic, dark, no text",1024,512,f"{d}/hero.jpg")
    for g in fl.get("hot",[])[:6]:
        slug=g.lower().replace(" ","_")
        gen_persistent(f"{g} casino game preview, vibrant colorful exciting, no text",512,384,f"{d}/game_{slug}.jpg")
    print("готово:", os.listdir(d))

if __name__=="__main__":
    build(sys.argv[1] if len(sys.argv)>1 else "in")
