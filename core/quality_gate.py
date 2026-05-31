"""Quality-gate: проверка AI-текста перед публикацией. AI-маркеры + длина + плейсхолдеры.
Возвращает (ok, score, issues). Сырой AI = бан (March 2026)."""
import re
AI_MARKERS=re.compile(r"\b(in conclusion|moreover|furthermore|it's worth noting|in today's world|navigating the|delve into|tapestry|in the realm of|when it comes to|a testament to|elevate your|unlock the|seamless|bustling|ever-evolving)\b",re.I)
def check(content):
    issues=[]; secs=content.get("sections",{})
    if not secs: return False,0,["нет секций"]
    bad_markers=0; short=0; placeholder=0
    for k,v in secs.items():
        v=v or ""
        m=len(AI_MARKERS.findall(v)); bad_markers+=m
        if len(v)<60: short+=1; issues.append(f"{k}: коротко ({len(v)})")
        if "..." in v or "<" in v or "placeholder" in v.lower(): placeholder+=1; issues.append(f"{k}: плейсхолдер")
    if bad_markers: issues.append(f"AI-маркеров: {bad_markers}")
    # score 0-100: штраф за маркеры/короткие/плейсхолдеры
    score=max(0,100 - bad_markers*8 - short*15 - placeholder*30)
    ok = score>=70 and placeholder==0
    return ok, score, issues
