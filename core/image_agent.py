import urllib.request,json,uuid,time
import os
KEY=os.environ.get("RUNWARE_API_KEY","")
def gen_image(prompt,w=1024,h=512):
    body=json.dumps([{"taskType":"authentication","apiKey":KEY},
     {"taskType":"imageInference","taskUUID":str(uuid.uuid4()),"positivePrompt":prompt,
      "model":"runware:101@1","width":w,"height":h,"numberResults":1}]).encode()
    for _a in range(3):
        try:
            req=urllib.request.Request("https://api.runware.ai/v1",data=body,headers={"Content-Type":"application/json"})
            r=json.loads(urllib.request.urlopen(req,timeout=90).read())
            return r["data"][0]["imageURL"], r["data"][0].get("cost",0.0006)
        except Exception:
            time.sleep(2)
    raise RuntimeError("runware failed 3x")
