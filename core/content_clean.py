"""Чистка сгенерированного контента — анти-AI-детект + актуальность.

1. Zero-width / невидимые юникод-символы — LLM их вставляет, это ПАЛЕВО на AI-детекторах (GPTZero и
   ко ловят по ним). Вырезаем.
2. Год: LLM по дефолту пишет 2024/2025 — у нас 2026. Заменяем.
3. AI-маркеры-фразы (in conclusion / moreover / it's worth noting) — флагуем (для лога), не режем грубо.
"""
import re

# невидимые: zero-width space/non-joiner/joiner, word-joiner, BOM, soft-hyphen, LTR/RTL marks
_INVISIBLE = dict.fromkeys([0x200b, 0x200c, 0x200d, 0x2060, 0xfeff, 0x00ad, 0x200e, 0x200f,
                            0x2061, 0x2062, 0x2063, 0x2064], None)
_AI_PHRASES = ["in conclusion", "it's worth noting", "it is worth noting", "moreover,",
               "furthermore,", "in today's digital", "when it comes to", "dive into",
               "navigating the", "in the world of", "elevate your", "unlock the"]
CUR_YEAR = "2026"

def strip_invisible(s):
    return s.translate(_INVISIBLE)

def fix_year(s):
    # заменяем устаревшие годы на текущий (в гембле «2024 best casino» = протухло)
    return re.sub(r"\b20(2[0-5])\b", CUR_YEAR, s)

def clean(html):
    """Чистит HTML: невидимые символы + год. Возвращает (clean_html, report)."""
    inv = sum(html.count(chr(cp)) for cp in _INVISIBLE)
    out = strip_invisible(html)
    yrs = len(re.findall(r"\b20(2[0-5])\b", out))
    out = fix_year(out)
    low = out.lower()
    ai_hits = [p for p in _AI_PHRASES if p in low]
    return out, {"invisible_removed": inv, "stale_years_fixed": yrs, "ai_phrase_flags": ai_hits}

def text_word_count(html):
    """Видимый текст без тегов/скриптов → число слов (метрика глубины контента)."""
    h = re.sub(r"<(script|style)[^>]*>.*?</\1>", " ", html, flags=re.S)
    txt = re.sub(r"<[^>]+>", " ", h)
    return len(txt.split())
