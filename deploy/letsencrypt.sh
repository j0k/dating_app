#!/bin/bash
set -e
DOMAIN=agent.happybanana.solutions
EMAIL="${LETSENCRYPT_EMAIL:-admin@happybanana.solutions}"
mkdir -p /var/www/certbot
certbot certonly --webroot -w /var/www/certbot -d "$DOMAIN" --email "$EMAIL" --agree-tos --non-interactive
echo "Done. Configure nginx and reload."
