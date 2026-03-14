# Развёртывание на https://agent.happybanana.solutions/

## Требования

- Сервер с Ubuntu 20.04+ (или аналог)
- Домен `agent.happybanana.solutions` с DNS A-записью на IP сервера
- Порты 80 и 443 открыты

## 1. Подготовка сервера

```bash
sudo apt update && sudo apt install -y python3 python3-venv nginx certbot python3-certbot-nginx
```

## 2. Код приложения

```bash
sudo mkdir -p /var/www/dating_app
sudo chown "$USER" /var/www/dating_app
cd /var/www/dating_app
git clone <URL_РЕПОЗИТОРИЯ> .
python3 -venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## 3. Переменные окружения

Создайте `/var/www/dating_app/.env`:

```bash
FLASK_ENV=production
SECRET_KEY=<сгенерируйте_длинный_секретный_ключ>
# DATABASE_URL=sqlite:////var/www/dating_app/dating_app.db  # по умолчанию
```

Секрет можно сгенерировать: `python3 -c "import secrets; print(secrets.token_hex(32))"`

## 4. Сертификат Let's Encrypt

```bash
sudo mkdir -p /var/www/certbot
# Временно: простой nginx на 80 для ACME (или остановите nginx)
sudo certbot certonly --webroot -w /var/www/certbot -d agent.happybanana.solutions --email admin@happybanana.solutions --agree-tos --non-interactive
```

Либо используйте скрипт из репозитория:

```bash
chmod +x deploy/letsencrypt.sh
sudo LETSENCRYPT_EMAIL=your@email.com ./deploy/letsencrypt.sh
```

При необходимости обновление сертификата: `sudo certbot renew` (cron уже ставится certbot’ом).

## 5. Nginx

```bash
sudo cp deploy/nginx.conf /etc/nginx/sites-available/agent.happybanana.solutions
sudo ln -s /etc/nginx/sites-available/agent.happybanana.solutions /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
```

Если используете `options-ssl-nginx.conf` от certbot:

```bash
sudo certbot install --nginx -d agent.happybanana.solutions
```

при необходимости подправьте конфиг вручную под proxy_pass на `127.0.0.1:8000`.

## 6. Gunicorn (systemd)

```bash
# Отредактируйте пути и пользователя в deploy/dating-app.service
sudo cp deploy/dating-app.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable dating-app
sudo systemctl start dating-app
sudo systemctl status dating-app
```

## 7. Проверка

- Откройте https://agent.happybanana.solutions/
- Должна открыться главная страница приложения

## Логи

- Приложение: `sudo journalctl -u dating-app -f`
- Nginx: `sudo tail -f /var/log/nginx/error.log`
- Логи приложения (если настроены): `/var/www/dating_app/logs/dating_app.log`
