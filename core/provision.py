"""АВТО-ПРОВИЖИНИНГ: домен (Namecheap) → Cloudflare (zone+DNS проксированно) → деплой.

Цель Алекса: "купили домен → сразу Cloudflare → сразу на сервер → залили сайт" одной кнопкой.
Cloudflare-прокси на каждый домен = решение IP-footprint (реальный IP сервера скрыт, у каждого
домена свой CF-edge). Сервер пока Saturn (на Hetzner); Hetzner Cloud API подключим позже.

Токены (env, создаёт Алекс сам):
  CF_API_TOKEN          — Cloudflare API token (Zone:Edit, DNS:Edit, Zone:Read, Zone:Create)
  NAMECHEAP_API_USER    — Namecheap API user
  NAMECHEAP_API_KEY     — Namecheap API key
  NAMECHEAP_CLIENT_IP   — whitelisted IP (наш сервер) для Namecheap API
Без токена соответствующий шаг возвращает {"skipped": "no token"} — не падает.
"""
import os, json, urllib.request, urllib.parse, xml.etree.ElementTree as ET

CF = "https://api.cloudflare.com/client/v4"

def _cf_req(method, path, body=None):
    tok = os.environ.get("CF_API_TOKEN", "")
    if not tok:
        return {"skipped": "no CF_API_TOKEN"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(CF + path, data=data, method=method,
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=30).read())
    except urllib.error.HTTPError as e:
        return {"success": False, "error": e.read().decode()[:300]}

# ---------- Cloudflare ----------
def cf_account_id():
    # токен может не иметь Account:Read — тогда берём из env (известен из дашборда)
    env = os.environ.get("CF_ACCOUNT_ID", "")
    if env:
        return env
    r = _cf_req("GET", "/accounts")
    if isinstance(r, dict) and r.get("result"):
        return r["result"][0]["id"]
    return None

def cf_add_zone(domain):
    """Создаёт zone. Возвращает {zone_id, name_servers} — NS прописать у регистратора."""
    acc = cf_account_id()
    if not acc:
        return {"ok": False, "step": "account", "raw": acc}
    r = _cf_req("POST", "/zones", {"name": domain, "account": {"id": acc}, "type": "full"})
    if r.get("success"):
        z = r["result"]
        return {"ok": True, "zone_id": z["id"], "name_servers": z.get("name_servers", [])}
    return {"ok": False, "raw": r}

def cf_set_a(zone_id, name, ip, proxied=True):
    """A-запись (проксированная = скрытие IP + footprint-щит)."""
    r = _cf_req("POST", f"/zones/{zone_id}/dns_records",
                {"type": "A", "name": name, "content": ip, "ttl": 1, "proxied": proxied})
    return {"ok": bool(r.get("success")), "raw": r if not r.get("success") else r["result"]["id"]}

def cf_set_ssl_flexible(zone_id):
    """SSL Flexible — чтобы CF отдавал https даже если на сервере http."""
    return _cf_req("PATCH", f"/zones/{zone_id}/settings/ssl", {"value": "flexible"})

# ---------- Namecheap ----------
def _nc_call(command, extra):
    u = os.environ.get("NAMECHEAP_API_USER", ""); k = os.environ.get("NAMECHEAP_API_KEY", "")
    ip = os.environ.get("NAMECHEAP_CLIENT_IP", "")
    if not (u and k and ip):
        return {"skipped": "no Namecheap creds"}
    params = {"ApiUser": u, "ApiKey": k, "UserName": u, "ClientIp": ip, "Command": command}
    params.update(extra)
    url = "https://api.namecheap.com/xml.response?" + urllib.parse.urlencode(params)
    try:
        raw = urllib.request.urlopen(url, timeout=40).read().decode()
        root = ET.fromstring(raw)
        status = root.attrib.get("Status", "")
        return {"ok": status == "OK", "raw": raw[:500]}
    except Exception as e:
        return {"ok": False, "error": str(e)[:200]}

def nc_check(domain):
    return _nc_call("namecheap.domains.check", {"DomainList": domain})

def nc_register(domain, years=1):
    """Покупка домена. Требует баланс + заполненные контакты в аккаунте Namecheap."""
    return _nc_call("namecheap.domains.create", {"DomainName": domain, "Years": years})

def nc_set_cf_nameservers(domain, name_servers):
    sld, tld = domain.split(".", 1)
    return _nc_call("namecheap.domains.dns.setCustom",
                    {"SLD": sld, "TLD": tld, "Nameservers": ",".join(name_servers)})

# ---------- Hetzner Cloud (1 общий сервер на МНОГО сайтов — экономия) ----------
HC = "https://api.hetzner.cloud/v1"
SHARED_SERVER_NAME = "seoforge-web-1"  # один сервер, на нём все сайты (nginx vhost на домен)

def _hc_req(method, path, body=None):
    tok = os.environ.get("HETZNER_API_TOKEN", "")
    if not tok:
        return {"skipped": "no HETZNER_API_TOKEN"}
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(HC + path, data=data, method=method,
        headers={"Authorization": "Bearer " + tok, "Content-Type": "application/json"})
    try:
        return json.loads(urllib.request.urlopen(req, timeout=40).read())
    except urllib.error.HTTPError as e:
        return {"error": e.read().decode()[:300]}

def ht_server_ip(name=SHARED_SERVER_NAME):
    """IP существующего общего сервера (None если нет — значит надо создать 1 раз)."""
    r = _hc_req("GET", f"/servers?name={name}")
    ss = (r or {}).get("servers", [])
    if ss:
        return ss[0].get("public_net", {}).get("ipv4", {}).get("ip")
    return None

# cloud-init: ставит nginx, готовит /var/www/<domain> и общий vhost-каталог
_CLOUD_INIT = """#cloud-config
packages: [nginx]
runcmd:
  - mkdir -p /var/www/_sites
  - rm -f /etc/nginx/sites-enabled/default
  - bash -c 'cat > /etc/nginx/sites-available/seoforge <<EOF
server {
  listen 80 default_server;
  root /var/www/_sites/\\$http_host;
  index index.html;
  location / { try_files \\$uri \\$uri/ /index.html; }
}
EOF'
  - ln -sf /etc/nginx/sites-available/seoforge /etc/nginx/sites-enabled/seoforge
  - systemctl enable nginx && systemctl restart nginx
"""

def ht_create_shared_server(server_type="cx23", location="nbg1", image="ubuntu-24.04", ssh_keys=None):
    """Создаёт ОДИН общий сервер (если ещё нет). Возвращает {ip, created|exists}."""
    ip = ht_server_ip()
    if ip:
        return {"ip": ip, "status": "exists"}
    body = {"name": SHARED_SERVER_NAME, "server_type": server_type, "location": location,
            "image": image, "user_data": _CLOUD_INIT, "start_after_create": True}
    if ssh_keys:
        body["ssh_keys"] = ssh_keys
    r = _hc_req("POST", "/servers", body)
    if r.get("server"):
        return {"ip": r["server"].get("public_net", {}).get("ipv4", {}).get("ip"), "status": "created",
                "id": r["server"]["id"]}
    return {"status": "error", "raw": r}

# ---------- Оркестратор ----------
def provision(domain, server_ip=None, buy=False):
    """домен (опц. покупка) → CF zone → NS у регистратора → A проксированная → SSL. Возвращает отчёт.
    server_ip=None → берём IP общего Hetzner-сервера (1 сервер на много сайтов)."""
    server_ip = server_ip or ht_server_ip()
    report = {"domain": domain, "server_ip": server_ip, "steps": {}}
    if not server_ip:
        report["steps"]["server"] = "нет общего сервера — создай ht_create_shared_server() или передай IP (напр. Saturn)"
    if buy:
        report["steps"]["buy"] = nc_register(domain)
    zone = cf_add_zone(domain)
    report["steps"]["cf_zone"] = zone
    if zone.get("ok"):
        zid = zone["zone_id"]
        report["steps"]["ns_at_registrar"] = nc_set_cf_nameservers(domain, zone["name_servers"])
        report["steps"]["dns_root"] = cf_set_a(zid, domain, server_ip, proxied=True)
        report["steps"]["dns_www"] = cf_set_a(zid, "www", server_ip, proxied=True)
        report["steps"]["ssl"] = "flexible" if cf_set_ssl_flexible(zid).get("success") else "fail"
    return report
