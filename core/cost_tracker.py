"""Экономика конвейера: себестоимость сайта + ROI. Unit-экономика к цели $20k/июнь."""
# замеренные/оценённые ставки
COST = {
    "claude_page": 0.06,    # Sonnet ~32k токенов/стр (multisite, 7 стр)
    "claude_plan": 0.01,    # architect+copywriter
    "runware_hero": 0.06,   # Flux Pro Ultra 4MP
    "runware_game": 0.0038, # Flux Dev /игра
    "domain_year": 12.0,    # средний дроп/рег
    "server_month": 3.99,   # cx23 (делится на ~N сайтов)
}
DEP_VALUE = 200.0  # $ за депозит по рефу

def site_cost(pages=7, games=4, sites_per_server=50):
    c = (pages * COST["claude_page"] + COST["claude_plan"] + COST["runware_hero"]
         + games * COST["runware_game"] + COST["domain_year"]
         + COST["server_month"] / sites_per_server)
    return round(c, 2)

def roi(deps, pages=7, games=4):
    cost = site_cost(pages, games)
    rev = deps * DEP_VALUE
    return {"site_cost": cost, "deps": deps, "revenue": rev,
            "roi_x": round(rev / cost, 1) if cost else None,
            "breakeven_deps": round(cost / DEP_VALUE, 3)}

def june_target(target=20000, deps_per_site_month=1.0):
    """Сколько сайтов нужно под цель $/месяц при среднем депов/сайт."""
    deps_needed = target / DEP_VALUE
    sites = deps_needed / max(deps_per_site_month, 0.01)
    return {"target_usd": target, "deps_needed": round(deps_needed),
            "sites_needed": round(sites), "total_cost": round(sites * site_cost(), 2)}
