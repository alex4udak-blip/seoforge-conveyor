# SEOForge — конвейер гембл-SEO 24/7

Генератор SEO-сайтов v2 + vision-оценщик + разведка. Деплой на Saturn, работает постоянно.

## Модули
- `core/` — генератор: structure_planner, keyword_taxonomy, content_agent (Claude), image_agent (Runware), asset_fetcher, site_planner, assembler3 (современный дизайн), quality_gate
- `site_builder.py` — сборка мультистраничного сайта (9 стр + sitemap/robots/llms)
- `build_assets.py` — пул картинок (hero+игры) на диск
- `vision_checker2.py` — vision-оценка против реальных топов выдачи
- `visual_checker.py` — DOM-QA
- `app.py` — FastAPI: POST /generate, GET /sites, /health

## Запуск
```
pip install -r requirements.txt
ANTHROPIC_API_KEY=... uvicorn app:app --host 0.0.0.0 --port 8000
```

## Деплой Saturn
Dockerfile → Saturn app (project cricket360-india) → 24/7.
</content>
