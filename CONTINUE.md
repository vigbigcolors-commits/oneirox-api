# ONEIROX Decode — состояние проекта (продолжить отсюда)

**Последнее обновление:** 2 июля 2026  
**Контрольная точка:** git tag `STABLE_DECODE_07.02.2026` → commit `3acabd5`  
**Предыдущая точка отката:** `STABLE_DECODE_O3`  
**Ветка:** `clean-main` = `origin/main`

---

## Что зафиксировано на `STABLE_DECODE_07.02.2026`

### Decode quality (~9/10 на partner/breakup кейсах)
- Голос **you/your** — не «her brain / her amygdala»
- Термины с пояснением: `REM (deep sleep when vivid dreams run)`
- Partner/breakup сны — CLIENT note в `build_user_message()`
- `[MORNING]` — вопрос про реальность, не сломанная грамматика
- **Один** вызов Claude — стабильно на Railway

### Файлы
| Файл | Роль |
|------|------|
| `main.py` | `/analyze`, rate limit 5/hr/IP, `sanitize_decode_output()` перед return |
| `dream_validation.py` | `build_user_message()`, sanitizer, `_fix_morning_question()` |
| `ONEIROX_PROMPT.txt` | WHO YOU SPEAK TO, PLAIN LANGUAGE BRIDGE, partner rules |
| `test_dream.py` | `py test_dream.py dream.txt` |

### Sanitizer (`sanitize_decode_output`)
- Убирает: `her amygdala`, `her brain`, `his brain`, organ-diagnosis фразы
- **Без** дополнительного API-вызова (multi-call rewrite ломал прод)

---

## Инфраструктура

| | |
|---|---|
| GitHub | https://github.com/vigbigcolors-commits/oneirox-api |
| Railway | `eloquent-enchantment` → `oneirox-api` |
| Production | https://oneirox-api-production.up.railway.app/analyze |
| Version check | `GET /version` → `prompt_sha12` |
| Автодеплой | **ВЫКЛЮЧЕН** → после push **Redeploy вручную** |

---

## Откат к контрольной точке

```powershell
cd "D:\aONEIROX +++++++++\ONEIROX_API +++++++++++++"
git fetch origin
git checkout STABLE_DECODE_07.02.2026 -- main.py dream_validation.py ONEIROX_PROMPT.txt test_dream.py
git push origin HEAD:main
```
→ Railway Dashboard → Deployments → **Redeploy**

**Экстренный откат (старый O3):**
```powershell
git checkout STABLE_DECODE_O3 -- main.py dream_validation.py ONEIROX_PROMPT.txt test_dream.py
git push origin HEAD:main
```

**Без git:** Railway → redeploy предыдущий зелёный deployment.

---

## Лимиты ответа (dream_validation.py)

| Сон | Tier | Лимит ответа | max_tokens |
|---|---|---|---|
| < 40 слов | short | 220 | 350 |
| 40–120 | standard | 300 | 500 |
| 120–300 | long | 400 | 650 |
| 300+ | detailed | 500 | 800 |

---

## Локальный тест

```powershell
cd "D:\aONEIROX +++++++++\ONEIROX_API +++++++++++++"
py test_dream.py dream.txt
```

`.env` → `ANTHROPIC_API_KEY=sk-ant-...`

---

## Деплой

1. Commit → Push (`clean-main` / `origin/main`)
2. Railway → **Redeploy**
3. Проверка: `/version` + тест на oneirox.com

---

## Связь с сайтом

Сайт: `D:\aONEIROX +++++++++\ONEIROX  2 -------------------\Oneirox`  
Контрольная точка сайта: `07.02.2026_Oneirox_stable` → `f6acb06`  
Документация сайта: `CONTINUATION.md` в папке Oneirox

`public/js/oneirox-decode.js` → POST `/analyze` с `{ "text": "..." }`

---

## ⚠️ Не делать снова

- Multi-call Claude rewrite в `main.py` — таймауты, «Something went wrong»
- `system=` отдельный параметр с экспериментальными промптами без теста на Railway

---

## TODO опционально

- [ ] Sanitizer: «the dream was she staging» → «her way of staging»
- [ ] README на GitHub
- [ ] Включить автодеплой Railway (если захочешь)

---

*Открой этот файл в Cursor: «продолжаем с CONTINUE.md» + `@CONTINUATION.md` на сайте*
