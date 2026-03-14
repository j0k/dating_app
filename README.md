# Dating App MVP

Веб-приложение с рекомендательной системой в формате dating-сервиса: профили, карточки, лайки/пропуски, матчи и чат. Дизайн вдохновлён [Happy Banana](https://happybanana.solutions/) — тёплый, аккуратный интерфейс.

## Возможности

- **Регистрация и вход** — email + пароль
- **Профиль** — имя, возраст, пол, город, о себе, интересы, видимость в рекомендациях
- **Лента** — карточки рекомендаций с фильтрами (возраст, пол, город)
- **Лайк / пропуск** — отправка реакции по API; при взаимном лайке создаётся матч
- **Матчи** — список матчей с переходом в чат
- **Чат** — обмен сообщениями в рамках матча
- **Логирование** — в файл `logs/dating_app.log` (в production) и консоль

## Стек

- **Backend:** Python 3.10+, Flask, Flask-Login, Flask-WTF, PyMongo
- **БД:** MongoDB (подключение через `MONGODB_URI`, по умолчанию `mongodb://localhost:27017/dating_app`)
- **Frontend:** Jinja2, vanilla JS, CSS (шрифты Outfit, DM Sans)

## Запуск локально

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
export FLASK_ENV=development
# Запустите MongoDB локально или задайте MONGODB_URI
python run.py
```

Откройте http://127.0.0.1:5000 (или порт из `PORT`).

## Production и HTTPS

Развёртывание на **https://agent.happybanana.solutions/** с Gunicorn, Nginx и Let's Encrypt описано в [DEPLOY.md](DEPLOY.md). В каталоге `deploy/` лежат:

- `nginx.conf` — виртуальный хост с SSL
- `letsencrypt.sh` — получение сертификата
- `dating-app.service` — unit для systemd (Gunicorn)

Перед запуском в production задайте `SECRET_KEY` в окружении или в `.env`.
