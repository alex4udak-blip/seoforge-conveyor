"""Мониторинг сайтов: жив/упал, в индексе/выпал, забанен. Сигналы для алертов (#76)."""
import urllib.request, ssl, re

_ctx = ssl.create_default_context(); _ctx.check_hostname = False; _ctx.verify_mode = ssl.CERT_NONE

def http_status(url, timeout=12):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        r = urllib.request.urlopen(req, timeout=timeout, context=_ctx)
        return r.getcode()
    except urllib.error.HTTPError as e:
        return e.code
    except Exception:
        return 0

def indexed_count(domain):
    """Сколько страниц в индексе Google (site:domain). 0 = не проиндексирован/выпал."""
    try:
        from core.recon import _fetch
        html = _fetch(f"https://www.google.com/search?q=site:{domain}&num=20")
        m = re.search(r"[Аа]bout ([\d,]+) result|Результатов: примерно ([\d\s]+)", html or "")
        if m:
            return int(re.sub(r"[^\d]", "", m.group(1) or m.group(2)))
        return html.count(domain) if html else 0
    except Exception:
        return None

def check_site(host, domain=None):
    """Сводка здоровья сайта: код, в индексе. domain — корневой для site:."""
    code = http_status(f"https://{host}/")
    idx = indexed_count(domain or host)
    alert = None
    if code == 0 or code >= 500:
        alert = f"DOWN ({code})"
    elif idx == 0:
        alert = "НЕ в индексе / выпал"
    return {"host": host, "http": code, "indexed": idx, "alert": alert,
            "ok": alert is None}
