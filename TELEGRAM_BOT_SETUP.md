# 🤖 Telegram бот для новостей на марийском языке

## 📋 Что делает бот

✅ Копирует новости с любого сайта  
✅ Переводит текст на марийский язык через GPT-4  
✅ Публикует в Telegram канал или личные сообщения  
✅ Работает автоматически по ссылке  

---

## 🚀 Быстрый старт (3 шага)

### Шаг 1: Получить API ключи

#### OPENAI_API_KEY
1. Зайдите на https://platform.openai.com/api-keys
2. Войдите в аккаунт (или зарегистрируйтесь)
3. Нажмите **"Create new secret key"**
4. Скопируйте ключ (выглядит как `sk-proj-abc123...`)
5. Вставьте в поле выше

**Пример:** `sk-proj-aBcDeFgHiJkLmNoPqRsTuVwXyZ123456789`

#### TELEGRAM_BOT_TOKEN
1. Откройте Telegram и найдите [@BotFather](https://t.me/BotFather)
2. Отправьте команду `/newbot`
3. Придумайте имя бота (например: "Mari News Bot")
4. Придумайте username (например: `mari_news_translator_bot`)
5. BotFather отправит токен (выглядит как `1234567890:ABCdefGHIjklMNOpqrsTUVwxyz`)
6. Скопируйте токен и вставьте в поле выше

**Пример:** `7123456789:AAHdqTcvCH1vGWJxfSeofSAs0K5PALDsaw`

---

### Шаг 2: Настроить канал (опционально)

#### Если хотите публиковать в канал:

1. Создайте канал в Telegram
2. Добавьте вашего бота в администраторы канала:
   - Откройте канал → **Настройки → Администраторы**
   - Нажмите **Добавить администратора**
   - Найдите вашего бота по username
   - Включите права: **Публикация сообщений**
3. Узнайте ID канала:
   - Перешлите любое сообщение из канала боту [@userinfobot](https://t.me/userinfobot)
   - Он покажет `Forwarded from chat: -1001234567890`
   - Это и есть channel_id (начинается с `-100`)

**Пример channel_id:** `-1001234567890`

---

### Шаг 3: Использовать бота

#### Вариант А: Через личные сообщения

1. Найдите вашего бота в Telegram (по username)
2. Нажмите **Start**
3. Отправьте ссылку на новость
4. Бот автоматически:
   - Скачает текст новости
   - Переведет на марийский
   - Отправит вам переведенный текст

#### Вариант Б: Программная публикация в канал

```bash
curl -X POST https://ваш-url-функции \
  -H "Content-Type: application/json" \
  -d '{
    "action": "parse",
    "url": "https://example.com/news/article"
  }'
```

Затем опубликовать:

```bash
curl -X POST https://ваш-url-функции \
  -H "Content-Type: application/json" \
  -d '{
    "action": "publish",
    "channel_id": "-1001234567890",
    "title": "Переведенный заголовок",
    "text": "Переведенный текст",
    "url": "https://example.com/news/article"
  }'
```

---

## 📝 API Endpoints

### 1. Парсинг и перевод новости

**Метод:** `POST`  
**Параметры:**
```json
{
  "action": "parse",
  "url": "https://example.com/news"
}
```

**Ответ:**
```json
{
  "success": true,
  "original": {
    "title": "Оригинальный заголовок",
    "text": "Оригинальный текст...",
    "url": "https://example.com/news"
  },
  "translated": {
    "title": "Кушкын марий йылме",
    "text": "Переведенный текст на марийском..."
  },
  "timestamp": "2025-10-22T10:00:00"
}
```

---

### 2. Публикация в Telegram

**Метод:** `POST`  
**Параметры:**
```json
{
  "action": "publish",
  "channel_id": "-1001234567890",
  "title": "Заголовок",
  "text": "Текст новости",
  "url": "https://example.com"
}
```

**Для личных сообщений:**
```json
{
  "action": "publish",
  "chat_id": "123456789",
  "title": "Заголовок",
  "text": "Текст"
}
```

---

## 🎯 Примеры использования

### Пример 1: Простой парсинг

```javascript
const response = await fetch('https://ваш-url-функции', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'parse',
    url: 'https://mari-el.gov.ru/news/123'
  })
});

const result = await response.json();
console.log(result.translated.text);
```

---

### Пример 2: Парсинг + публикация в канал

```javascript
// 1. Получить переведенную новость
const parseRes = await fetch('https://ваш-url-функции', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'parse',
    url: 'https://example.com/news'
  })
});

const { translated, original } = await parseRes.json();

// 2. Опубликовать в канал
await fetch('https://ваш-url-функции', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    action: 'publish',
    channel_id: '-1001234567890',
    title: translated.title,
    text: translated.text,
    url: original.url
  })
});
```

---

### Пример 3: Автоматизация через webhook

Настройте webhook для вашего бота:

```bash
curl "https://api.telegram.org/bot<ВАШ_ТОКЕН>/setWebhook?url=https://ваш-url-функции"
```

Теперь бот будет автоматически обрабатывать все ссылки, которые ему присылают!

---

## 🔧 Настройка автоматического постинга

### Вариант 1: Cron на вашем сервере

```bash
# Запускать каждый час
0 * * * * curl -X POST https://ваш-url-функции -d '{"action":"parse","url":"https://news-site.com/latest"}'
```

### Вариант 2: GitHub Actions (бесплатно)

Создайте `.github/workflows/news-parser.yml`:

```yaml
name: Parse News

on:
  schedule:
    - cron: '0 */3 * * *'  # Каждые 3 часа

jobs:
  parse:
    runs-on: ubuntu-latest
    steps:
      - name: Parse and translate
        run: |
          curl -X POST ${{ secrets.BOT_URL }} \
            -H "Content-Type: application/json" \
            -d '{"action":"parse","url":"https://example.com/news"}'
```

---

## 📊 Как работает перевод

Бот использует GPT-4 для качественного перевода на марийский язык:

1. **Парсинг:** Извлекается текст новости (заголовок + основной текст)
2. **Перевод:** GPT-4 переводит на луговой марийский язык
3. **Форматирование:** Сохраняется структура и разбиение на абзацы
4. **Публикация:** Отправляется в Telegram с оригинальной ссылкой

**Качество перевода:** GPT-4 обучен на марийском языке и дает качественный литературный перевод.

---

## 🛡️ Безопасность

✅ Все API ключи хранятся как секреты в облаке  
✅ Ключи никогда не попадают в код или логи  
✅ HTTPS шифрование для всех запросов  
✅ Бот не сохраняет личные данные  

---

## 🐛 Решение проблем

### Ошибка "OPENAI_API_KEY не настроен"
- Добавьте ключ через форму выше
- Проверьте, что ключ начинается с `sk-`

### Ошибка "TELEGRAM_BOT_TOKEN не настроен"
- Получите токен у @BotFather
- Проверьте, что токен содержит `:`

### Бот не публикует в канал
- Убедитесь, что бот добавлен в администраторы
- Проверьте права на публикацию
- ID канала должен начинаться с `-100`

### Не парсится сайт
- Некоторые сайты блокируют автоматические запросы
- Попробуйте другой источник новостей
- Убедитесь, что URL содержит текст (не PDF/видео)

---

## 💡 Полезные ссылки

- [Документация Telegram Bot API](https://core.telegram.org/bots/api)
- [OpenAI Platform](https://platform.openai.com)
- [Как создать бота в Telegram](https://core.telegram.org/bots/tutorial)
- [Как узнать ID канала](https://stackoverflow.com/questions/33858927/how-to-obtain-the-chat-id-of-a-private-telegram-channel)

---

## 🎓 Примеры сайтов для парсинга

Подходящие источники новостей:

- Новостные порталы Марий Эл
- RSS ленты новостей
- Блоги и статьи
- Пресс-релизы

**Важно:** Сайт должен иметь обычную HTML структуру (не SPA с динамической загрузкой).

---

## 📞 Поддержка

Вопросы? Пишите в сообщество: https://t.me/+QgiLIa1gFRY4Y2Iy

---

**URL вашей функции:**
```
https://functions.poehali.dev/85b72ebd-10f6-4e6b-9ae2-6a964c714f5d
```

Используйте этот URL для всех API запросов!
