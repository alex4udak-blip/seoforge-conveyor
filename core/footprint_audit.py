"""FOOTPRINT-АУДИТОР СВОЕЙ СЕТИ (правильная модель, не tag-метрика).

Google склеивает сеть НЕ по похожести div'ов, а по 6 векторам инфраструктуры+связей
(из наших кейсов вскрытия чужих сетей). Проверяем что НАШУ сеть нельзя вскрыть тем же.
Каждый вектор = реальный риск-сигнал с числовым весом.

run(network) -> {risk_score, vectors:[...], fixes:[...]}
network = [{slug, html, ip?, ns?, registrar?, deployed_date?}]
"""
import re
from collections import Counter

def _extract(html):
    """Тащим из HTML палевные следы: tracking-ID, исходящие ссылки на свои."""
    ga = set(re.findall(r'(G-[A-Z0-9]{6,}|UA-\d{4,}-\d+|GTM-[A-Z0-9]{4,})', html or ""))
    adsense = set(re.findall(r'(ca-pub-\d{10,})', html or ""))
    # текстовый отпечаток: набор «фирменных» фраз (повторяющийся текст = шаблон)
    phrases = set(re.findall(r'200% up to|Welcome Bonus|players won today|paid out this week|Licensed', html or ""))
    return {"ga": ga, "adsense": adsense, "phrases": phrases}

def audit(network):
    """6 векторов футпринта. Возвращает risk 0-100 + по каждому вектору + фиксы."""
    n = len(network)
    if n < 2:
        return {"risk_score": 0, "note": "нужно ≥2 сайта", "vectors": []}
    ex = [{"slug": s["slug"], **_extract(s.get("html", "")), **s} for s in network]
    vectors = []; fixes = []

    # 1. ОБЩИЙ IP/СЕРВЕР (главный сигнал) — если хостинг не задан, считаем все на одном (риск)
    ips = [s.get("ip") for s in network if s.get("ip")]
    if not ips:
        vectors.append({"vector": "IP/сервер", "risk": 90,
                        "detail": "хостинг не разнесён — вероятно ВСЕ на одном сервере/IP = очевидная сеть"})
        fixes.append("Разнести сайты по разным серверам/IP (главный антифутпринт). Сейчас все на одном Saturn.")
    else:
        uniq = len(set(ips))
        r = round(100 * (1 - uniq / n))
        vectors.append({"vector": "IP/сервер", "risk": r, "detail": f"{uniq} уникальных IP на {n} сайтов"})
        if r > 40: fixes.append("Больше разных IP/подсетей — сайты группируются на общих серверах")

    # 2. ОБЩИЕ TRACKING-ID — reverse-lookup мгновенно палит
    all_ga = Counter();
    for e in ex:
        for g in e["ga"] | e["adsense"]: all_ga[g] += 1
    shared = {g: c for g, c in all_ga.items() if c > 1}
    if shared:
        vectors.append({"vector": "tracking-ID", "risk": 95,
                        "detail": f"ОБЩИЕ ID на нескольких сайтах: {list(shared)[:3]} — reverse-lookup вскроет сеть"})
        fixes.append("Убрать общие GA/GTM/AdSense ID — у каждого сайта свой или никакого")
    else:
        vectors.append({"vector": "tracking-ID", "risk": 5, "detail": "общих tracking-ID нет — чисто"})

    # 3. ПЕРЕЛИНКОВКА МЕЖДУ СВОИМИ — граф сети
    slugs = {s["slug"] for s in network}
    cross = 0
    for s in network:
        for other in slugs:
            if other != s["slug"] and other in (s.get("html") or ""):
                cross += 1
    if cross:
        vectors.append({"vector": "перелинковка", "risk": 70,
                        "detail": f"{cross} ссылок между своими сайтами — образует граф сети"})
        fixes.append("Убрать прямые ссылки между сайтами сети (или только через нейтральные хабы)")
    else:
        vectors.append({"vector": "перелинковка", "risk": 5, "detail": "сайты не ссылаются друг на друга — чисто"})

    # 4. ТЕКСТОВЫЙ ШАБЛОН — повторяющиеся фирменные фразы («выучил бенгальский»)
    phrase_counts = Counter()
    for e in ex:
        for p in e["phrases"]: phrase_counts[p] += 1
    repeated = {p: c for p, c in phrase_counts.items() if c >= max(2, n * 0.6)}
    if repeated:
        r = round(100 * len(repeated) / max(1, len(phrase_counts) or 1))
        vectors.append({"vector": "текст-шаблон", "risk": min(r, 80),
                        "detail": f"повторяющиеся фразы на {len(repeated)} паттернах: {list(repeated)[:2]}"})
        fixes.append("Уникализировать фирменные фразы (бонус/winners/trust) — сейчас одинаковый текст")
    else:
        vectors.append({"vector": "текст-шаблон", "risk": 10, "detail": "повторяющихся фраз мало"})

    # 5. NS/регистратор
    ns = [s.get("ns") for s in network if s.get("ns")]
    if ns and len(set(ns)) < len(ns):
        vectors.append({"vector": "NS/whois", "risk": 50, "detail": "общие NS-серверы"})
        fixes.append("Разные NS/регистраторы")
    else:
        vectors.append({"vector": "NS/whois", "risk": 15 if not ns else 5,
                        "detail": "NS не проверены" if not ns else "NS разные"})

    # 6. ДАТА деплоя пачкой
    dates = [s.get("deployed_date") for s in network if s.get("deployed_date")]
    if dates and len(set(dates)) == 1 and len(dates) > 2:
        vectors.append({"vector": "даты", "risk": 40, "detail": "все задеплоены в один день"})
        fixes.append("Разнести запуски во времени")
    else:
        vectors.append({"vector": "даты", "risk": 10, "detail": "даты не проверены/разнесены"})

    # итоговый риск = взвешенная макс-ориентированная (один критичный вектор уже палит)
    weights = {"IP/сервер": 0.30, "tracking-ID": 0.25, "перелинковка": 0.20,
               "текст-шаблон": 0.15, "NS/whois": 0.06, "даты": 0.04}
    score = round(sum(v["risk"] * weights.get(v["vector"], 0.1) for v in vectors))
    verdict = ("КРИТИЧНО — сеть легко вскрывается" if score >= 60 else
               "ВЫСОКИЙ риск футпринта" if score >= 40 else
               "СРЕДНИЙ — есть слабые места" if score >= 25 else
               "НИЗКИЙ — сеть хорошо замаскирована")
    return {"risk_score": score, "verdict": verdict, "sites": n,
            "vectors": sorted(vectors, key=lambda v: -v["risk"]), "fixes": fixes}
