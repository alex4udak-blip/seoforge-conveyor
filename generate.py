import sys,os
from core.structure_planner import plan
from core.assembler import render
def gen(domain,brand,geo,kw):
    pl=plan(domain,brand,geo,kw); h=render(pl)
    out=f"output/{domain.replace('.','_')}.html"; open(out,"w").write(h)
    return pl,out
if __name__=="__main__":
    # тест: 2 разных домена под один бренд -> должны быть РАЗНЫЕ
    for d in [("78win01.host","78Win","in","78win casino"),("33win.wtf","33Win","bd","33win casino")]:
        pl,out=gen(*d)
        print(f"{d[0]:<16} -> {out} | дизайн:{pl['palette']['name']} hero:{pl['hero']} секций:{len(pl['sections'])} cta:'{pl['cta']}' порядок:{pl['sections']}")
