"""Structure-planner: домен -> УНИКАЛЬНАЯ структура+дизайн. Отдельный хеш на параметр."""
import hashlib
from core import design_tokens as T
def _h(domain,key): return int(hashlib.sha256(f"{domain}:{key}".encode()).hexdigest(),16)
def plan(domain, brand, geo, keyword):
    pick=lambda lst,key: lst[_h(domain,key)%len(lst)]
    palette=pick(T.PALETTES,"pal"); fonts=pick(T.FONTS,"font")
    hero=pick(T.HERO_LAYOUTS,"hero"); cta=pick(T.CTA_TEXTS,"cta"); radius=pick(T.RADIUS,"rad")
    n=4+_h(domain,"n")%4
    pool=T.SECTION_POOL[:]; order=[]
    for i in range(n):
        if not pool: break
        order.append(pool.pop(_h(domain,f"sec{i}")%len(pool)))
    if "toplist" not in order: order.insert(0,"toplist")
    if "faq" in order: order.remove("faq")
    order.append("faq")
    return {"domain":domain,"brand":brand,"geo":geo,"keyword":keyword,
            "palette":palette,"fonts":fonts,"hero":hero,"cta":cta,"radius":radius,"sections":order}
