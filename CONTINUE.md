# ONEIROX Decode — состояние проекта (продолжить отсюда)

Последнее обновление: 25 Jun 2026 · коммит `O3` · ветка `clean-main` = `origin/main`

---

## Что уже сделано

### API (Railway) — готово и задеплоено
- **`ONEIROX_PROMPT.txt`** — промпт v3:
  - нейробиологический голос (Walker, Cartwright, LeDoux, Damasio, Revonsuo…)
  - 5 принципов методологии oneirox.com/methodology
  - **APPARENT PRECOGNITION PROTOCOL** — 3 механизма: subthreshold / threat simulation / retrospective sharpening
  - **EPISTEMIC HONESTY** — не выдавать догадки за факты
  - **PLAIN LANGUAGE BRIDGE** — после терминов сразу простые слова
  - **PEACE THROUGH PRECISION** — разделение страха сна и meta-fear
  - выход: `[SIGNAL]` `[BODY]` `[MORNING]`
- **`main.py`** — endpoint `/analyze`, читает промпт из txt, `max_tokens` динамически
- **`dream_validation.py`** — фильтр спама ДО API + лимиты ответа по длине сна
- **`test_dream.py`** — локальный тест без деплоя

### Фронт (WordPress) — готово
- **`oneirox-engine.js` v10.9** — показывает ошибки API (`data.detail`), не generic error
- **`oneirox-core.php`** — версия `10.9` для сброса кэша
- Путь на хостинге: `wp-content/plugins/oneirox-vigen-engine/`

### Инфраструктура
- GitHub: https://github.com/vigbigcolors-commits/oneirox-api
- Railway проект: `eloquent-enchantment` → сервис `oneirox-api`
- Production URL: https://oneirox-api-production.up.railway.app/analyze
- Variable: `ANTHROPIC_API_KEY` (на eloquent-enchantment — есть)
- Rate limit: **5 запросов / час / IP**
- Автодеплой Railway: **выключен** → после push нужен **Redeploy вручную** в Railway Dashboard
- Проверка версии промпта на проде: `GET https://oneirox-api-production.up.railway.app/version` → поле `prompt_sha12` должно совпадать с локальным после Redeploy

---

## Карта файлов

| Задача | Файл |
|---|---|
| Тон, наука, структура, простой язык | `ONEIROX_PROMPT.txt` |
| Модель, rate limit, endpoint | `main.py` |
| Валидация спама, лимиты слов | `dream_validation.py` |
| Локальный тест | `py test_dream.py dream.txt` |
| Прогресс-бар, парсер, ошибки API | `oneirox-engine.js` (WordPress) |
| Сброс кэша JS | `oneirox-core.php` → bump `10.9` → `10.10` |
| Поле Decode, кнопка | HTML Block 1 Kadence (не трогать без нужды) |

**Не коммитить:** `.env`, `dream.txt`, `API KEY/`, `ЗАПАС/`

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
cd "d:\aONEIROX +++++++++\ONEIROX_API +++++++++++++"
py -m pip install -r requirements.txt
py test_dream.py dream.txt
py test_dream.py "test test"   # → Rejected, 0 токенов
```

`.env` → `ANTHROPIC_API_KEY=sk-ant-...`

---

## Деплой API (GitHub Desktop)

1. Правки → Commit → Push (`clean-main`)
2. Railway → Deployments → **Redeploy** (если автодеплой выкл)
3. Проверка: https://oneirox-api-production.up.railway.app/docs

**Только промпт?** Достаточно push `ONEIROX_PROMPT.txt` — `main.py` не трогать.

---

## Деплой фронта (WordPress)

1. Правишь `oneirox-engine.js`
2. Bump версию в `oneirox-core.php` (`10.9` → `10.10`)
3. Залить оба файла на хостинг
4. Очистить кэш Hostinger / Cloudflare
5. Ctrl+Shift+R · в Network проверить `?ver=10.10` и наличие `data.detail` в JS

Локальные копии JS:
- `C:\Users\Vigen\Downloads\oneirox-engine.js`
- `...\wp-content\plugins\oneirox-vigen-engine\` (бэкап сайта)

---

## Эталонный тест-кейс

**`dream.txt`** — кухонный сон / «псевдопророчество» / сажа под обоями.

Хороший ответ должен содержать:
- все 3 механизма (subthreshold, Revonsuo threat simulation, retrospective sharpening)
- «not psychic / not losing your grip»
- meta-fear vs реальная угроза
- простой язык после терминов
- [MORNING] только про дом/сенсорику из текста

---

## Что можно делать дальше

- [ ] Push промпта v3 (PLAIN LANGUAGE) если ещё не на проде — проверить ответ на сайте
- [ ] Подкрутить лимиты слов в `dream_validation.py`
- [ ] Включить автодеплой на Railway (Settings → Deploy on push)
- [ ] Удалить дублирующий Railway-проект `enthusiastic-respect` если не нужен
- [ ] Добавить README на GitHub (сейчас пусто)
- [ ] Sensory Mapper → somatic context уже подмешивается в `oneirox-engine.js`

---

## Частые проблемы

| Симптом | Причина | Решение |
|---|---|---|
| «Something went wrong» на спам | старый JS в кэше | bump ver + purge cache |
| Variables пустые в Railway | другой проект | открыть eloquent-enchantment |
| Push не деплоит | автодеплой выкл | Redeploy вручную |
| `python` не работает | Windows PATH | использовать `py` |

---

## Философия Decode (для правок промпта)

> Помогаем не «расшифровкой символов», а **точностью, которая даёт покой**.
> Человек в 3am: вау от биологии + «я не безумна» + агентность ([MORNING]).
> Методология: https://oneirox.com/methodology/

---

*Открой этот файл в Cursor и скажи: «продолжаем с CONTINUE.md»*
