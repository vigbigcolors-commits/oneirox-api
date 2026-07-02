# ONEIROX Decode — состояние проекта (продолжить отсюда)

**Последнее обновление:** 3 июля 2026  
**Контрольная точка:** git tag `STABLE_DECODE_07.02.2026` → commit `3acabd5`  
**Сайт (пара):** tag `03.07.2026_Oneirox_stable` → `a985df4`  
**Ветка:** `clean-main` = `origin/main`

---

## Что зафиксировано

### Decode quality (~9/10 partner/breakup)
- Голос **you/your** — не «her brain / her amygdala»
- Термины: `name (plain words in parentheses)`
- Partner/breakup — CLIENT note в `build_user_message()`
- `[MORNING]` — «Did she tell you» / вопрос про реальность
- **Один** вызов Claude — стабильно на Railway

**Последний эталонный ответ (проверен):**
- «Your grief is structural», «dream to destiny» — её интерпретация
- MORNING: marriage, timelines, pressure ✅
- Мелочи: «scan her dreams sleep», «her dreams and amygdala» — sanitizer TODO

### Файлы
| Файл | Роль |
|------|------|
| `main.py` | `/analyze`, rate limit 5/hr/IP, `sanitize_decode_output()` |
| `dream_validation.py` | `build_user_message()`, sanitizer, `_fix_morning_question()` |
| `ONEIROX_PROMPT.txt` | WHO YOU SPEAK TO, PLAIN LANGUAGE BRIDGE, partner rules |
| `test_dream.py` | `py test_dream.py dream.txt` |

---

## Инфраструктура

| | |
|---|---|
| GitHub | https://github.com/vigbigcolors-commits/oneirox-api |
| Railway | `eloquent-enchantment` → `oneirox-api` |
| Production | https://oneirox-api-production.up.railway.app/analyze |
| Автодеплой | **ВЫКЛЮЧЕН** → push + **Redeploy вручную** |

---

## Откат

```powershell
cd "D:\aONEIROX +++++++++\ONEIROX_API +++++++++++++"
git fetch origin
git checkout STABLE_DECODE_07.02.2026 -- main.py dream_validation.py ONEIROX_PROMPT.txt test_dream.py
git push origin HEAD:main
```
→ Railway → Redeploy

**Экстренный:** `git checkout STABLE_DECODE_O3 -- ...` или redeploy зелёный в Railway.

---

## ⚠️ Не делать снова

- Multi-call Claude rewrite — таймауты
- Диагностировать чужой мозг: her amygdala, her brain
- Возвращать neural-bg в perf-defer на сайте (ломает видимость анимации)

---

## TODO опционально

- [ ] Sanitizer: grammar fixes (см. CONTINUATION.md на сайте)
- [ ] README на GitHub
- [ ] Автодеплой Railway

---

## Связь с сайтом

`CONTINUATION.md` в `D:\aONEIROX +++++++++\ONEIROX  2 -------------------\Oneirox`  
`public/js/oneirox-decode.js` → POST `/analyze`

*«продолжаем с CONTINUE.md» + `@CONTINUATION.md`*
