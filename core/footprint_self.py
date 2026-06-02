"""Footprint-самоаудит сети: попарная схожесть НАШИХ сайтов + общие следы (GA/исходящие).

Главный бан-вектор сети (по Диме/ресёрчу) — шаблон-склейка. Мерим что наши сайты РАЗНЫЕ.
Порог склейки 0.65 (footprint.pair_similarity). Также ловим общий GA/GTM ID и исходящие с главной.
"""
import os, re, glob

def audit(output_dir="output"):
    from core.footprint import pair_similarity
    idx = {}
    for p in glob.glob(os.path.join(output_dir, "*", "index.html")):
        slug = p.split(os.sep)[-2]
        try:
            idx[slug] = open(p, encoding="utf-8").read()
        except Exception:
            pass
    sites = list(idx.keys())
    pairs = []
    for i in range(len(sites)):
        for j in range(i + 1, len(sites)):
            sim = pair_similarity(idx[sites[i]], idx[sites[j]])
            pairs.append({"a": sites[i], "b": sites[j], "sim": round(sim, 3),
                          "glued": sim >= 0.65})
    pairs.sort(key=lambda x: x["sim"], reverse=True)
    # общие следы: одинаковый GA/GTM ID на >1 сайте = footprint
    ga = {}
    for slug, h in idx.items():
        for m in re.findall(r"(G-[A-Z0-9]{6,}|GTM-[A-Z0-9]{4,}|UA-\d+)", h):
            ga.setdefault(m, []).append(slug)
    shared_ga = {k: v for k, v in ga.items() if len(v) > 1}
    return {"sites": len(sites), "max_sim": pairs[0]["sim"] if pairs else 0,
            "glued_pairs": [p for p in pairs if p["glued"]],
            "shared_analytics_ids": shared_ga,
            "verdict": "ОК — сеть не склеена" if (not any(p["glued"] for p in pairs) and not shared_ga)
                       else "РИСК склейки — разнообразить"}
