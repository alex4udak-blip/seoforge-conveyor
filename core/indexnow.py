"""IndexNow — мгновенный пинг поисковикам (Bing, Yandex, Seznam) о новых/обновлённых URL. Бесплатно.

Требует файл-ключ в корне сайта: https://<domain>/<key>.txt с содержимым = сам ключ.
Google IndexNow не поддерживает (для Google — GSC/Indexing API отдельно), но Bing+Yandex берут моментально.
"""
import hashlib, json, urllib.request

def key_for(domain):
    """Детерминированный 32-симв. ключ на домен (чтобы не хранить отдельно)."""
    return hashlib.sha256(("seoforge-indexnow:" + domain).encode()).hexdigest()[:32]

def keyfile(domain):
    """Возвращает (filename, content) для размещения в корне сайта."""
    k = key_for(domain)
    return (f"{k}.txt", k)

def submit(domain, urls):
    """Пинг IndexNow. urls — список полных https URL."""
    k = key_for(domain)
    payload = {"host": domain, "key": k, "keyLocation": f"https://{domain}/{k}.txt",
               "urlList": urls}
    body = json.dumps(payload).encode()
    req = urllib.request.Request("https://api.indexnow.org/indexnow", data=body,
        headers={"Content-Type": "application/json; charset=utf-8"})
    try:
        r = urllib.request.urlopen(req, timeout=20)
        return {"ok": r.getcode() in (200, 202), "code": r.getcode(), "submitted": len(urls)}
    except urllib.error.HTTPError as e:
        return {"ok": False, "code": e.code, "err": e.read().decode()[:200]}
    except Exception as e:
        return {"ok": False, "err": str(e)[:200]}
