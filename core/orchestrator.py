"""ОРКЕСТРАТОР КОНВЕЙЕРА — гонит домен через ВСЕ стадии единой цепью, с логом и состоянием.

Стадии: RECON → PLAN(architect) → CONTENT(copywriter) → IMAGES → GENERATE(multisite)
        → SEO-files(robots/sitemap/llms) + ANALYTICS(beacon) → DEPLOY(CF DNS + scp) → INDEX(IndexNow)
        → RANK(baseline позиция/AI-видимость).
Каждая стадия логируется в job['stages']; падение стадии не роняет всю цепь (best-effort с пометкой).
Контракт: run_pipeline(brand, keyword, geo, host, do_deploy=False) -> job dict.
"""
import os, json, time, hashlib

def _log(job, stage, status, **extra):
    rec = {"stage": stage, "status": status, **extra}
    job["stages"].append(rec)
    print(f"[{stage}] {status} " + " ".join(f"{k}={v}" for k, v in extra.items()), flush=True)

def run_pipeline(brand, keyword, geo, host, do_deploy=False, server_ip=None, mode="generic"):
    job = {"brand": brand, "keyword": keyword, "geo": geo, "host": host, "mode": mode, "stages": []}
    site_id = hashlib.sha256(host.encode()).hexdigest()[:12]
    job["site_id"] = site_id

    # 1. RECON
    recon = None
    try:
        from core.recon import serp
        recon = serp(keyword, geo, n=6, classify_deep=False)
        _log(job, "RECON", "ok", top=len(recon.get("top", []) or recon.get("results", [])),
             related=len(recon.get("related", [])))
    except Exception as e:
        _log(job, "RECON", "skip", err=str(e)[:80])

    # 2. PLAN
    from core.agent_architect import plan_structure
    plan = plan_structure(keyword, geo, recon=recon, seed=host)
    _log(job, "PLAN", "ok", layout=plan.get("layout"), blocks=len(plan.get("blocks", [])), src=plan.get("source"))

    # 3. CONTENT
    from core.agent_copywriter import write_content
    content = write_content(brand, keyword, geo, plan)
    _log(job, "CONTENT", "ok", blocks=len(content))

    # 4. IMAGES
    from core.keyword_taxonomy import GEO_FLAVOR
    from core.image_bank import hero_img, game_img
    from core.asset_fetcher import payment_logo_url, casino_logo
    fl = GEO_FLAVOR.get(geo, {}); hot = fl.get("hot", ["Slots", "Roulette"])[:4]
    cas = [{"name": (t.get("brand") or t.get("domain", "")),
            "logo": casino_logo(t.get("domain", ""), t.get("brand") or t.get("domain", "")),
            "bonus": fl.get("bonus", "")} for t in (recon.get("top") or [])[:5] if t.get("domain")] if recon else []
    images = {"hero": hero_img(host, 1000, 440, brand=brand, vibe=f"{brand} {keyword}"),
              "games": {g: game_img(g, host, brand=brand) for g in hot},
              "pays": {p: payment_logo_url(p) for p in fl.get("pay", ["Visa"])[:4]},
              "casinos": cas}
    _log(job, "IMAGES", "ok", hero=bool(images["hero"]), games=len(images["games"]))

    # 5. GENERATE (multipage)
    from core.site_multi import build_multisite
    pages = build_multisite(brand, keyword, geo, host, plan, content, images, mode=mode)
    if (not pages or "index" not in pages or len(pages) < 5):  # авто-ретрай при недоборе (#115)
        _log(job, "GENERATE", "retry", got=len(pages or {}))
        pages = build_multisite(brand, keyword, geo, host, plan, content, images, mode=mode)
    if not pages or "index" not in pages or len(pages) < 5:
        _log(job, "GENERATE", "fail", got=len(pages or {}), have_index=bool(pages and "index" in pages),
             note="не деплою битый набор (нет index или <5 стр)")
        job["pages_partial"] = list((pages or {}).keys())
        return job
    _log(job, "GENERATE", "ok", pages=len(pages))

    # 6. SEO-files + ANALYTICS (инъекция beacon в каждую страницу)
    from core.seo_files import robots_txt, sitemap_xml, llms_txt
    from core.indexnow import keyfile
    from core.analytics import inject
    pages = {sl: inject(h, site_id) for sl, h in pages.items()}
    files = {f"{sl}.html": h for sl, h in pages.items()}
    files["robots.txt"] = robots_txt(host)
    files["sitemap.xml"] = sitemap_xml(host, list(pages.keys()))
    files["llms.txt"] = llms_txt(brand, host, geo, pages=list(pages.keys()))
    kf_name, kf_content = keyfile(host); files[kf_name] = kf_content
    _log(job, "SEO+ANALYTICS", "ok", files=len(files), beacon=site_id, indexnow_key=kf_name)

    if not do_deploy:
        job["files"] = list(files.keys())
        _log(job, "DEPLOY", "skipped", note="do_deploy=False")
        return job

    # 7. DEPLOY — записать файлы и залить на сервер + CF DNS
    import tempfile
    d = tempfile.mkdtemp(prefix="site_")
    for fn, content_ in files.items():
        open(os.path.join(d, fn), "w", encoding="utf-8").write(content_)
    import core.provision as p
    server_ip = server_ip or p.ht_server_ip()
    dep = p.deploy_files(host, d, server_ip=server_ip)
    _log(job, "DEPLOY:files", "ok" if dep.get("ok") else "fail", **dep)
    # CF DNS: добавить поддомен в существующую зону
    cf = _cf_subdomain(host, server_ip)
    _log(job, "DEPLOY:dns", "ok" if cf.get("ok") else "fail", **{k: v for k, v in cf.items() if k != "raw"})

    # 8. INDEX — IndexNow пинг
    from core.indexnow import submit
    urls = [f"https://{host}/" if sl == "index" else f"https://{host}/{sl}.html" for sl in pages]
    idx = submit(host, urls)
    _log(job, "INDEX:indexnow", "ok" if idx.get("ok") else "fail", **idx)

    # 9. RANK — базовая проверка AI-видимости/позиции
    try:
        from core.recon import ai_visibility
        av = ai_visibility(brand, geo) if "ai_visibility" in dir(__import__("core.recon", fromlist=["x"])) else None
        _log(job, "RANK:baseline", "ok", ai=str(av)[:80] if av else "n/a")
    except Exception as e:
        _log(job, "RANK:baseline", "skip", err=str(e)[:60])

    job["live_url"] = f"https://{host}/"
    return job

def auto_brandjack(geo="in", n=3, zone="playerstatspro.net", do_deploy=True, patterns=None):
    """АВТО-КОНВЕЙЕР: свежие бренды (brand-radar) → брендоджек-сайты автоматом. Машина денег."""
    from core.brand_radar import fresh_brands
    brands = fresh_brands(patterns=patterns, limit=n * 3)
    log(f"brand-radar: {len(brands)} свежих кандидатов")
    done = []
    for b in brands[:n]:
        slug = re.sub(r"[^a-z0-9]+", "-", b["brand"].lower()).strip("-")[:30] or "brand"
        host = f"{slug}-review.{zone}"
        try:
            job = run_pipeline(b["brand"], f"{b['brand']} review {geo}", geo, host,
                               do_deploy=do_deploy, mode="brandjack")
            done.append({"brand": b["brand"], "src_domain": b["domain"],
                         "host": host, "live": job.get("live_url"),
                         "ok": sum(1 for s in job["stages"] if s["status"] == "ok")})
        except Exception as e:
            done.append({"brand": b["brand"], "err": str(e)[:80]})
    return done

def log(m):
    print(f"[auto] {m}", flush=True)

def _cf_subdomain(host, ip):
    """Добавляет A-запись поддомена в существующую CF-зону (zone = последние 2 лейбла)."""
    import core.provision as p
    parts = host.split(".")
    zone = ".".join(parts[-2:]); sub = ".".join(parts[:-2]) or "@"
    r = p._cf_req("GET", f"/zones?name={zone}")
    res = (r or {}).get("result") if isinstance(r, dict) else None
    if not res:
        return {"ok": False, "err": f"zone {zone} not in CF"}
    zid = res[0]["id"]
    rec = p.cf_set_a(zid, sub if sub != "@" else zone, ip, proxied=True)
    return {"ok": rec.get("ok", False), "zone": zone, "sub": sub}
