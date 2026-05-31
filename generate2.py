import sys,os
from core.structure_planner import plan
from core.keyword_taxonomy import detect_type,KW_TYPES,GEO_FLAVOR
from core.content_agent import generate as gt
from core.image_agent import gen_image
from core.assembler2 import render
def build(dom,brand,geo,kw):
    ktype=detect_type(kw); secs=KW_TYPES[ktype]["sections"]
    pl=plan(dom,brand,geo,kw); pl["sections"]=secs   # ФИКС: секции под тип ключа
    content,u=gt(brand,geo,kw,secs)
    hero,_=gen_image(f"online casino hero banner, {geo} theme, premium cinematic neon, no text",1024,400)
    html=render(pl,content,hero,"")  # лого пустое -> CSS-текст в assembler
    out=f"output/{dom.replace('.','_')}.html"; open(out,"w").write(html)
    print(f"OK {dom} | type:{ktype} secs:{secs} | in={u['input_tokens']} out={u['output_tokens']}")
    return out
if __name__=="__main__":
    pass  # ANTHROPIC_API_KEY из env
    build("78win01.host","78Win","in","78win casino")
