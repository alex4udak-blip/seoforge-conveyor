"""КОНТРАКТ модулей SEOForge — чтобы вкладки работали И в оркестраторе/цепочке/параллели.

ПРИНЦИП: каждый модуль = чистая функция вход(dict) → выход(dict). Без побочки в глобалы.
UI дёргает функцию ради показа; оркестратор дёргает ту же функцию в цепочке. Один код — два потока.

ЕДИНЫЙ ФОРМАТ ДАННЫХ между звеньями (что течёт по конвейеру):

  Job = {
    "geo": "in", "niche": "crash", "keyword": "aviator predictor india",
    # заполняется по мере прохождения звеньев:
    "recon":   {...},   # RECON.run() — топ, конкуренты, семантика, динамика, footprint
    "ai_vis":  {...},   # AI-visibility — есть в AI-выдаче, кто вместо нас
    "domain":  {...},   # ДОМЕНЩИК — выбранный домен, цена, DR, тип
    "site":    {...},   # ГЕНЕРАТОР — slug, страницы, schema
    "audit":   {...},   # VISION/копирайт — баллы, фиксы
    "deploy":  {...},   # ДЕПЛОЙ — url, статус
    "keitaro": {...},   # ТРЕКИНГ — депы/EPC (замыкание)
  }

КАЖДЫЙ модуль реализует:
  def run(job: dict) -> dict:   # принимает Job, возвращает Job с заполненной своей секцией
      ...
      job["<секция>"] = результат
      return job

Тогда оркестратор = просто:
  job = {"geo":"in","niche":"crash"}
  for step in [recon.run, ai_vis.run, domains.run, generator.run, audit.run, deploy.run]:
      job = step(job)
  # а параллельные (ai_vis ∥ recon) — через threads, мёржат свои секции

СОСТОЯНИЕ: общая SQLite output/seoforge.db (не разрозненные CSV/JSON).
  таблицы: serp_snapshots (есть), domains, sites, jobs, ai_visibility.

UI-эндпоинты остаются тонкими обёртками над module.run() — показывают job-секцию.
"""

def merge(job: dict, section: str, data: dict) -> dict:
    """Хелпер: записать секцию в Job не мутируя вход (безопасно для параллели)."""
    out = dict(job or {})
    out[section] = data
    return out

def new_job(geo="in", niche=None, keyword=None, **extra) -> dict:
    return {"geo": geo, "niche": niche, "keyword": keyword, **extra}
