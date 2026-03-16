# Telegram-бот магазина рыбы (Strapi + Redis)

В проекте реализован Telegram-бот с каталогом товаров, корзиной и шагом оформления заказа.  

## Установка и запуск

1. Убедитесь, что установлен **Python 3.10–3.12**  
2. Склонируйте репозиторий.
3. Создайте виртуальное окружение:
```bash
python3 -m venv venv
```
4. Активируйте виртуальное окружение:
- Windows:
```bash
venv\Scripts\activate
```
- Linux/macOS:
```bash
source venv/bin/activate
```
5. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Переменные окружения

В корне проекта создайте файл **.env**:

```ini
TG_BOT_TOKEN=токен_вашего_телеграм_бота

DATABASE_HOST=localhost
DATABASE_PORT=6379
DATABASE_PASSWORD=пароль_redis

STRAPI_API_TOKEN=api_token_из_strapi
STRAPI_BASE_URL=http://localhost:1337
```

### Описание параметров

- **TG_BOT_TOKEN** — токен Telegram-бота (получить у [BotFather](https://t.me/BotFather)).
- **DATABASE_HOST** — хост Redis.
- **DATABASE_PORT** — порт Redis.
- **DATABASE_PASSWORD** — пароль Redis (если не используется, оставьте пустым).
- **STRAPI_API_TOKEN** — токен доступа к Strapi API.
- **STRAPI_BASE_URL** — базовый URL Strapi (по умолчанию `http://localhost:1337`).

## Запуск бота

```bash
python main.py
```
