# 📸 Telegram Camera Bot

Бот на **aiogram 3.x** с веб-страницей для съёмки с фронтальной и основной камеры устройства.

## 📋 Возможности

- Инлайн-кнопки в Telegram
- Генерация уникальной ссылки для каждого пользователя
- Адаптивная веб-страница с запросом доступа к камере
- Автоматическая съёмка с фронтальной и основной камер
- Отправка фото обратно в чат Telegram
- Готов к деплою на Render.com / PythonAnywhere

## 🚀 Быстрый старт

### 1. Локальный запуск

```bash
# Клонируйте репозиторий
cd telegram-camera-bot

# Установка зависимостей
pip install -r requirements.txt

# Создайте .env файл (см. .env.example)
cp .env.example .env
# Отредактируйте .env, добавив BOT_TOKEN и WEB_APP_URL

# Запуск
python web_app.py
```

### 2. Настройка Render.com

1. Создайте **Web Service** на [Render](https://render.com), подключив GitHub-репозиторий
2. Добавьте **Environment Variables**:
   - `BOT_TOKEN` — от [@BotFather](https://t.me/botfather)
   - `WEB_APP_URL` — ваш URL на Render (например, `https://your-app.onrender.com`)
3. Получите **Deploy Hook URL** в настройках сервиса
4. Добавьте его в GitHub Secrets как `RENDER_DEPLOY_HOOK_URL`

### 3. Настройка PythonAnywhere

1. Загрузите код на PythonAnywhere
2. Установите зависимости в виртуальное окружение
3. В `.env` установите `USE_WEBHOOK=true`
4. Настройте веб-приложение (WSGI) на `web_app:app`
5. Добавьте секреты `PA_API_TOKEN`, `PA_USERNAME`, `PA_DOMAIN` в GitHub

## ⚠️ Важные замечания

- **HTTPS обязателен** для работы `getUserMedia()` (доступ к камере)
- На **iOS** открывайте ссылку в **Safari**, а не внутри Telegram (in-app browser может блокировать камеру)
- На бесплатном Render сервер "засыпает" — используйте внешний пинг (например, UptimeRobot) или платный тариф
- Для PythonAnywhere **polling запрещён** — используйте только `USE_WEBHOOK=true`

## 📁 Структура проекта

```
.
├── bot.py              # Логика Telegram-бота
├── web_app.py          # FastAPI сервер + веб-страница
├── requirements.txt    # Зависимости Python
├── .env.example        # Шаблон переменных окружения
├── render.yaml         # Конфигурация Render.com
├── .github/
│   └── workflows/
│       └── deploy.yml  # GitHub Actions CI/CD
└── static/             # Статические файлы (если понадобятся)
```

## 🛡️ Безопасность

- Храните `BOT_TOKEN` только в переменных окружения
- Никогда не коммитьте `.env` файл
- Используйте HTTPS в продакшене
