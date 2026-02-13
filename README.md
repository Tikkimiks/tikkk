# Forpost (Django)

Проект дипломной работы на Django для управления услугами, бригадами и расписанием.

## Локальный запуск
1. Создайте виртуальное окружение и установите зависимости:
```bash
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

2. Создайте файл `.env` (можно на основе `.env.example`).

3. Примените миграции и запустите сервер:
```bash
python security\manage.py migrate
python security\manage.py runserver
```

## Деплой на Render
В репозитории есть `render.yaml`.

1. Подключите репозиторий в Render.
2. При создании сервиса Render сам применит `render.yaml`.
3. В `Environment` укажите:
- `DJANGO_ALLOWED_HOSTS` — домен вашего сервиса.
- `DJANGO_CSRF_TRUSTED_ORIGINS` — `https://<ваш-домен>`.
- при необходимости `EMAIL_*`, `TELEGRAM_BOT_TOKEN`.

## Примечание по секретам
Секреты теперь берутся из переменных окружения. Старые ключи нужно заменить/отозвать.

