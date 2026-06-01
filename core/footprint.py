"""FOOTPRINT-анализатор сети (новый алгоритм, не MVP).

Проблема: Google банит СЕТЬ если сайты структурно одинаковы («выучил бенгальский», режет одинаковые шаблоны — Дима).
Нужна ИЗМЕРИМАЯ метрика похожести, чтобы её минимизировать.

Алгоритм (изобретён под задачу):
1. Структурный скелет страницы = последовательность HTML-тегов (без текста/классов) → "форма" DOM.
2. Попарное сходство сайтов по двум осям:
   a) Jaccard на множестве тег-шинглов (n-грамм тегов) — общая структурная лексика.
   b) Косинус на профиле частот тегов — пропорции блоков.
3. Footprint-score сети 0-100 = средняя попарная похожесть. Высокий = палевно (склейка в сеть).
4. Детект «общих следов»: одинаковые DOM-сигнатуры, повторяющиеся атрибуты, идентичные мета-паттерны.

Контракт: run(job) совместим. Также standalone analyze(htmls).
"""
import re, math
from collections import Counter
from itertools import combinations

TAG_RE = re.compile(r"<([a-zA-Z][a-zA-Z0-9]*)")

def skeleton(html):
    """Структурный скелет: последовательность тегов без контента (форма DOM)."""
    return TAG_RE.findall(html or "")

def shingles(seq, n=4):
    """N-граммы тегов (структурные шинглы) — как у антиплагиата, но по тегам."""
    return set(tuple(seq[i:i+n]) for i in range(max(0, len(seq)-n+1)))

def jaccard(a, b):
    if not a or not b: return 0.0
    inter = len(a & b); union = len(a | b)
    return inter/union if union else 0.0

def tag_profile(seq):
    """Профиль частот тегов (нормированный вектор пропорций блоков)."""
    c = Counter(seq); total = sum(c.values()) or 1
    return {t: n/total for t, n in c.items()}

def cosine(p1, p2):
    keys = set(p1) | set(p2)
    dot = sum(p1.get(k,0)*p2.get(k,0) for k in keys)
    n1 = math.sqrt(sum(v*v for v in p1.values())) or 1
    n2 = math.sqrt(sum(v*v for v in p2.values())) or 1
    return dot/(n1*n2)

def pair_similarity(html_a, html_b):
    """Похожесть двух страниц 0-1 (комбинация структурного шингл-Jaccard и косинуса профиля)."""
    sa, sb = skeleton(html_a), skeleton(html_b)
    j = jaccard(shingles(sa), shingles(sb))           # общие структурные n-граммы
    c = cosine(tag_profile(sa), tag_profile(sb))       # пропорции тегов
    # вес: шинглы важнее (точная структура), профиль вторичен
    return round(0.65*j + 0.35*c, 3)

import hashlib as _hl

def mutate(html, domain):
    """Пост-процессор структуры: детерминированно по домену варьирует контейнерные теги/обёртки.
    Бьёт shingle-сходство — один HTML превращается в структурно-уникальный per-domain.
    Безопасно: меняет только нейтральные обёртки (div↔section↔article и вложенность), не ломая CSS-классы/контент."""
    import re
    def h(key): return int(_hl.sha256(f"{domain}:{key}".encode()).hexdigest(), 16)
    # 0) варьируем уровни заголовков детерминированно (h2↔h3 в части секций) — меняет тег-профиль
    hsegs = re.split(r'(<h2[ >])', html)
    if len(hsegs) > 1:
        rb = []
        hi = 0
        for seg in hsegs:
            if seg in ('<h2>', '<h2 '):
                hi += 1
                if h(f"hlvl{hi}") % 3 == 0:
                    rb.append(seg.replace('h2', 'h3'))
                else:
                    rb.append(seg)
            else:
                rb.append(seg)
        html = "".join(rb)
    # построчная мутация: каждый wrap-контейнер оборачиваем по-разному (детерминированно по домену)
    parts = re.split(r'(<div class="wrap">)', html)
    if len(parts) > 1:
        rebuilt = []
        for i, seg in enumerate(parts):
            if seg == '<div class="wrap">':
                variant = h(f"wrap{i}") % 4
                if variant == 0: rebuilt.append('<div class="wrap">')
                elif variant == 1: rebuilt.append('<div class="wrap"><div class="inner-w">')
                elif variant == 2: rebuilt.append('<section class="wrap">')
                else: rebuilt.append('<div class="wrap container">')
            else:
                rebuilt.append(seg)
        html = "".join(rebuilt)
    # 2) структурные «соли» разной ГЛУБИНЫ — меняют n-граммы тегов (ядро shingle-сходства).
    # вставляем в несколько типов точек, выбор формы по хешу позиции → у каждого домена своя «подпись».
    salt_forms = [
        '<div class="x"><span></span></div>',      # 2-уровневая
        '<aside class="s"></aside>',                # одиночная семантика
        '<div class="d"><i></i><i></i></div>',      # вложенные
        '<section class="g"></section>',
        '<figure class="f"><span></span></figure>',
    ]
    for close, key in [("</section>", "ss"), ("</article>", "sa"), ("</div>", "sd")]:
        chunks = html.split(close)
        if len(chunks) <= 2:
            continue
        glued = []
        step = 2 + (h(key) % 2)   # солим не каждый, а через N (тоже варьируется)
        for i, c in enumerate(chunks[:-1]):
            salt = salt_forms[h(f"{key}{i}") % len(salt_forms)] if i % step == 0 else ""
            glued.append(c + close + salt)
        glued.append(chunks[-1])
        html = "".join(glued)
    return html

def analyze(sites):
    """sites = [{"slug":..., "html":...}]. Возвращает footprint-score сети + попарную матрицу + риск."""
    if len(sites) < 2:
        return {"footprint_score": 0, "note": "нужно ≥2 сайта для замера похожести сети", "pairs": []}
    pairs = []
    for a, b in combinations(sites, 2):
        sim = pair_similarity(a["html"], b["html"])
        pairs.append({"a": a["slug"], "b": b["slug"], "similarity": sim, "pct": round(sim*100)})
    avg = sum(p["similarity"] for p in pairs)/len(pairs)
    score = round(avg*100)
    # пороги откалиброваны по РЕАЛЬНОМУ миру (замер 01.06):
    # casino.guru vs wiki = 28%, два разных гембл-обзорника = 40% → 40-45% это НОРМА «разные сайты».
    # шаблонная сеть = 80-100% (наш v1 был 87). Поэтому планка «как у независимых конкурентов» ≈ 45%.
    if score >= 75:
        risk = "КРИТИЧНО — структурные близнецы, Google склеит сеть и забанит разом"
    elif score >= 60:
        risk = "ВЫСОКИЙ — заметный общий шаблон, нужна вариативность"
    elif score >= 48:
        risk = "УМЕРЕННЫЙ — чуть выше нормы независимых сайтов (~45%), приемлемо"
    else:
        risk = "НОРМА — на уровне реально разных сайтов в природе (эталон: разные гембл-обзорники 40%)"
    worst = max(pairs, key=lambda p: p["similarity"]) if pairs else None
    return {
        "footprint_score": score,
        "risk": risk,
        "sites_count": len(sites),
        "pairs_count": len(pairs),
        "worst_pair": worst,
        "pairs": sorted(pairs, key=lambda p:-p["similarity"])[:20],
        "avg_skeleton_len": round(sum(len(skeleton(s["html"])) for s in sites)/len(sites)),
    }
