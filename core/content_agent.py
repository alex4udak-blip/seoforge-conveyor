"""Content-агент: генерит реальный контент секций через Claude (Haiku). 1 запрос/сайт."""
import urllib.request,json,os
from core.keyword_taxonomy import KW_TYPES, GEO_FLAVOR, detect_type
MODEL="claude-haiku-4-5"
def generate(brand,geo,keyword,sections):
    key=os.environ["ANTHROPIC_API_KEY"]
    ktype=detect_type(keyword); fl=GEO_FLAVOR.get(geo,{})
    prompt=f"""You are an iGaming SEO copywriter. Generate UNIQUE, human-sounding content (80%+ human tone, no AI fluff) for a {ktype}-type page about "{brand}" targeting geo {geo.upper()} (keyword: {keyword}).
Geo context: sport={fl.get('sport','')}, payments={fl.get('pay',[])}, hot games={fl.get('hot',[])}.
Write REAL content (NOT placeholders, NOT "...", NOT "<...>"). Each section = 2-4 full human sentences with specifics.\nReturn STRICT JSON only: {{"meta_description":"<real 1 sentence>", "sections":{{ {", ".join(f'"{s}":"<real 2-4 sentences>"' for s in sections)} }}}}.
Localize naturally, mention payment methods and local sport where relevant. No markdown."""
    body=json.dumps({"model":MODEL,"max_tokens":2000,
        "messages":[{"role":"user","content":prompt}]}).encode()
    req=urllib.request.Request("https://api.anthropic.com/v1/messages",data=body,
        headers={"x-api-key":key,"anthropic-version":"2023-06-01","content-type":"application/json"})
    import time as _t
    r=None
    for _attempt in range(3):
        try:
            r=json.loads(urllib.request.urlopen(req,timeout=60).read()); break
        except Exception as _e:
            _t.sleep(1.5)
    if r is None: raise RuntimeError("content api failed 3x")
    txt=r["content"][0]["text"]; usage=r["usage"]
    # извлечь JSON
    s=txt.find("{"); e=txt.rfind("}")+1
    data=json.loads(txt[s:e])
    return data, usage
