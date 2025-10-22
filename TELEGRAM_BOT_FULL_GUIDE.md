# 🤖 Полная инструкция: Telegram бот с автопарсингом и модерацией

## 🎯 Возможности бота

✅ **Автоматическая проверка сайтов** — бот сам проверяет источники новостей по расписанию  
✅ **Парсинг с картинками** — извлекает текст и изображения из статей  
✅ **Перевод на марийский** — GPT-4 переводит каждую новость  
✅ **Модерация через личку** — новости приходят вам в Telegram с кнопками "Опубликовать"/"Отклонить"  
✅ **Публикация в канал** — одобренные новости автоматически публикуются с картинками  
✅ **База данных** — отслеживает уже опубликованные новости (без дублей)  

---

## 🚀 Быстрая настройка (5 шагов)

### Шаг 1: Добавить API ключи

Вам нужно добавить 4 секрета (формы для добавления появились выше ⬆️):

#### 1️⃣ OPENAI_API_KEY
**Где взять:**
1. https://platform.openai.com/api-keys
2. Создайте ключ
3. Скопируйте (начинается с `sk-proj-...`)

**Пример:** `sk-proj-aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789`

---

#### 2️⃣ TELEGRAM_BOT_TOKEN
**Где взять:**
1. Напишите [@BotFather](https://t.me/BotFather) в Telegram
2. Отправьте `/newbot`
3. Придумайте имя и username бота
4. Скопируйте токен

**Пример:** `7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`

---

#### 3️⃣ MODERATOR_CHAT_ID
**Где взять:**
1. Напишите [@userinfobot](https://t.me/userinfobot) в Telegram
2. Отправьте любое сообщение
3. Бот покажет ваш ID (число, например `123456789`)
4. Скопируйте это число

**Пример:** `123456789`

---

#### 4️⃣ CHANNEL_ID
**Где взять:**
1. Создайте канал в Telegram
2. Добавьте вашего бота в администраторы канала
3. Включите право "Публикация сообщений"
4. Перешлите любое сообщение из канала боту [@userinfobot](https://t.me/userinfobot)
5. Он покажет `Forwarded from chat: -1001234567890`
6. Скопируйте ID с минусом

**Пример:** `-1001234567890`

---

### Шаг 2: Настроить webhook для бота

После добавления всех ключей выполните:

```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d"
```

Замените `<ВАШ_ТОКЕН>` на ваш TELEGRAM_BOT_TOKEN.

**Проверка:**
```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/getWebhookInfo"
```

Должно быть: `"url": "https://functions.poehali.dev/..."`

---

### Шаг 3: Добавить источник новостей

**Через API:**

```bash
curl -X POST https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d \
  -H "Content-Type: application/json" \
  -d '{
    "action": "add_source",
    "name": "Марий Эл новости",
    "url": "https://mari-el.gov.ru/news/",
    "interval": 60
  }'
```

**Параметры:**
- `name` — название источника (для вас)
- `url` — ссылка на страницу со списком новостей
- `interval` — интервал проверки в минутах (60 = каждый час)

---

### Шаг 4: Запустить проверку новостей

**Ручной запуск:**

```bash
curl -X POST https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d \
  -H "Content-Type: application/json" \
  -d '{"action": "check_sources"}'
```

Бот найдет новые статьи, переведет их и отправит вам в Telegram для модерации!

---

### Шаг 5: Автоматизация (опционально)

Для автоматической проверки каждые N минут используйте cron или GitHub Actions.

**GitHub Actions** (бесплатно):

Создайте файл `.github/workflows/news-checker.yml`:

```yaml
name: Check News Sources

on:
  schedule:
    - cron: '0 * * * *'  # Каждый час
  workflow_dispatch:  # Ручной запуск

jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - name: Check news sources
        run: |
          curl -X POST https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d \
            -H "Content-Type: application/json" \
            -d '{"action": "check_sources"}'
```

Теперь бот будет проверять новости каждый час автоматически!

---

## 📱 Как работает модерация

### 1. Бот находит новую новость

Бот проверяет источники по расписанию и находит новую статью.

### 2. Вам приходит сообщение в Telegram

**Пример сообщения:**

```
📰 Новая новость для модерации

Оригинал:
В Марий Эл открылся новый парк

Перевод:
Марий Элыште у парк почылтеш

[Полный переведенный текст...]

Источник: https://example.com/news/123

[✅ Опубликовать] [❌ Отклонить]
```

Если у новости есть картинка — она тоже будет в сообщении!

### 3. Вы нажимаете кнопку

**✅ Опубликовать** → новость сразу публикуется в канал с картинкой  
**❌ Отклонить** → новость отмечается как отклоненная

### 4. Подтверждение

Бот отправит вам:
- `✅ Новость опубликована!` — при успехе
- `❌ Новость отклонена` — при отказе

---

## 🖼️ Работа с картинками

Бот автоматически:
1. Находит первое изображение в статье
2. Сохраняет URL картинки в базу
3. Отправляет вам в модерации через `sendPhoto`
4. Публикует в канал с картинкой через `sendPhoto`

**Если картинка не загрузится** — отправится текстовое сообщение.

---

## 🗄️ База данных

Бот хранит в PostgreSQL:

### Таблица `news_items`
- `url` — ссылка на новость (уникальная)
- `title` — оригинальный заголовок
- `original_text` — оригинальный текст
- `translated_title` — переведенный заголовок
- `translated_text` — переведенный текст
- `image_url` — ссылка на картинку
- `status` — статус (`new`, `pending_moderation`, `published`, `rejected`)
- `published_at` — дата публикации

### Таблица `news_sources`
- `name` — название источника
- `url` — URL страницы со списком новостей
- `check_interval_minutes` — интервал проверки
- `last_checked_at` — когда последний раз проверяли
- `is_active` — активен ли источник

**Защита от дублей:** Бот проверяет URL новости — если она уже есть в базе, пропускает.

---

## 📝 API методы

### 1. Проверить источники новостей

```bash
POST /
{
  "action": "check_sources"
}
```

**Ответ:**
```json
{
  "success": true,
  "sources_checked": 1,
  "new_articles": 3,
  "articles": [...]
}
```

---

### 2. Добавить источник

```bash
POST /
{
  "action": "add_source",
  "name": "Название",
  "url": "https://example.com/news",
  "interval": 60
}
```

---

### 3. Парсинг конкретной новости

```bash
POST /
{
  "action": "parse",
  "url": "https://example.com/article/123"
}
```

**Ответ:**
```json
{
  "success": true,
  "original": {
    "title": "...",
    "text": "...",
    "image": "https://...",
    "url": "..."
  },
  "translated": {
    "title": "...",
    "text": "..."
  }
}
```

---

### 4. Webhook для Telegram

```bash
POST /
{
  "action": "webhook",
  "callback_query": {
    "data": "approve_123",
    "message": {...}
  }
}
```

Автоматически обрабатывается при нажатии кнопок.

---

## 🎯 Примеры использования

### Пример 1: Добавить источник и проверить

```javascript
// 1. Добавить источник
await fetch('https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'add_source',
    name: 'Mari News',
    url: 'https://mari-el.gov.ru/news/',
    interval: 30
  })
});

// 2. Проверить новости
await fetch('https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ action: 'check_sources' })
});
```

---

### Пример 2: Парсинг конкретной новости

```javascript
const response = await fetch('https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'parse',
    url: 'https://example.com/news/article-123'
  })
});

const result = await response.json();
console.log('Переведенный заголовок:', result.translated.title);
console.log('Картинка:', result.original.image);
```

---

## ⚙️ Автоматизация через GitHub Actions

Создайте файл `.github/workflows/news-bot.yml`:

```yaml
name: News Bot Auto-Check

on:
  schedule:
    - cron: '0 */2 * * *'  # Каждые 2 часа
  workflow_dispatch:

jobs:
  check_news:
    runs-on: ubuntu-latest
    steps:
      - name: Check news sources
        run: |
          curl -X POST https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d \
            -H "Content-Type: application/json" \
            -d '{"action":"check_sources"}'
```

**Результат:** Бот будет проверять новости каждые 2 часа автоматически!

---

## 🐛 Решение проблем

### Бот не отправляет модерацию

**Проверьте:**
1. MODERATOR_CHAT_ID правильный (число без кавычек)
2. TELEGRAM_BOT_TOKEN корректный
3. OPENAI_API_KEY активен

**Проверка:**
```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/getMe"
```

---

### Кнопки не работают

**Причина:** Webhook не настроен

**Решение:**
```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d"
```

---

### Бот не находит новости

**Причины:**
1. Неправильный URL источника (должна быть страница со списком новостей)
2. Сайт блокирует автоматические запросы
3. Нестандартная структура HTML

**Решение:** Попробуйте другой источник или настройте селекторы в БД.

---

### Картинки не отправляются

**Причины:**
1. Картинка защищена от загрузки
2. URL картинки относительный (без https://)
3. Формат картинки не поддерживается Telegram

**Решение:** Бот автоматически переключается на текстовое сообщение.

---

## 📊 Статистика и мониторинг

Проверить базу данных:

```sql
-- Сколько новостей в базе
SELECT status, COUNT(*) FROM news_items GROUP BY status;

-- Последние 10 новостей
SELECT url, title, status, created_at FROM news_items ORDER BY created_at DESC LIMIT 10;

-- Активные источники
SELECT name, url, last_checked_at FROM news_sources WHERE is_active = true;
```

---

## 🎓 Расширенные возможности

### Настройка селекторов для сложных сайтов

Обновите запись в БД:

```sql
UPDATE news_sources 
SET 
  selector_title = 'h2.news-title',
  selector_text = 'div.news-content p',
  selector_image = 'img.news-image'
WHERE id = 1;
```

---

### Множественные источники

Добавьте несколько источников с разными интервалами:

```bash
# Источник 1: проверка каждые 30 минут
curl -X POST ... -d '{"action":"add_source","name":"Site1","url":"...","interval":30}'

# Источник 2: проверка каждые 2 часа
curl -X POST ... -d '{"action":"add_source","name":"Site2","url":"...","interval":120}'
```

---

## 💡 Полезные советы

1. **Тестирование:** Сначала добавьте один источник и проверьте вручную
2. **Интервалы:** Не ставьте слишком частую проверку (минимум 30 минут)
3. **Модерация:** Всегда проверяйте перевод перед публикацией
4. **Резервные копии:** Периодически экспортируйте базу данных

---

## 📞 Поддержка

- Сообщество: https://t.me/+QgiLIa1gFRY4Y2Iy
- Документация: https://docs.poehali.dev

---

**URL вашего бота:**
```
https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d
```

Бот готов к работе! Добавьте API ключи выше и начинайте модерировать новости! 🚀
