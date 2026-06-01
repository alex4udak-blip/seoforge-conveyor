"""Своя аналитика (НЕ общий Google Analytics — общий GA-ID = footprint, палит сеть).

Beacon бьёт в FIRST-PARTY путь /px (тот же домен) → nginx проксирует в наш коллектор.
В HTML нет внешнего трекер-хоста → footprint не растёт. Считаем: pageview, источник, клик по /go/ (CTA).
"""

def beacon_js(site_id):
    """JS-сниппет: pageview + клики по CTA (/go/) на first-party /px. site_id уникален на сайт."""
    return (
        "<script>(function(){"
        "var s=" + repr(site_id) + ";"
        "function px(e,x){try{navigator.sendBeacon('/px',new Blob([JSON.stringify("
        "{s:s,e:e,x:x||'',r:document.referrer,p:location.pathname,t:Date.now()})],"
        "{type:'application/json'}));}catch(_){}}"
        "px('view');"
        "document.addEventListener('click',function(ev){var a=ev.target.closest('a');"
        "if(a&&a.getAttribute('href')&&a.getAttribute('href').indexOf('/go/')===0)px('cta',a.textContent.slice(0,40));});"
        "})();</script>"
    )

def inject(html, site_id):
    snip = beacon_js(site_id)
    low = html.lower()
    i = low.rfind("</body>")
    if i == -1:
        return html + snip
    return html[:i] + snip + html[i:]

# nginx location, проксирующий /px в наш коллектор (добавляется в vhost сервера)
def nginx_px_proxy(collector_url):
    return (f"location = /px {{ proxy_pass {collector_url}/track; "
            f"proxy_set_header X-Real-IP $remote_addr; proxy_set_header Host $host; }}")
