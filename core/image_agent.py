import urllib.request,json,uuid,time
import os
KEY=os.environ.get("RUNWARE_API_KEY","")
def gen_image(prompt,w=1024,h=512,model="runware:101@1"):
    task={"taskType":"imageInference","taskUUID":str(uuid.uuid4()),"positivePrompt":prompt,
          "model":model,"width":w,"height":h,"numberResults":1}
    if model.startswith("runware:"):   # Flux Dev/Schnell поддерживают steps/CFG
        task["steps"]=30; task["CFGScale"]=3.5
    # Flux Pro Ultra (bfl:2@2) — фикс.размеры, без steps/CFG
    body=json.dumps([{"taskType":"authentication","apiKey":KEY}, task]).encode()
    for _a in range(3):
        try:
            req=urllib.request.Request("https://api.runware.ai/v1",data=body,headers={"Content-Type":"application/json"})
            r=json.loads(urllib.request.urlopen(req,timeout=90).read())
            return r["data"][0]["imageURL"], r["data"][0].get("cost",0.0006)
        except Exception:
            time.sleep(2)
    raise RuntimeError("runware failed 3x")
