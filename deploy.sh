#!/usr/bin/env bash
# Выкатка портфолио на Excelsior (/var/www/lebedev, a-lebedev.ru).
# Запуск из корня проекта:  bash deploy.sh
#
# Копирует только файлы из git (git archive), поэтому локальный мусор, .env и
# data.db на сервер не попадают. База на сервере синхронизируется из seed.py
# при старте. Первый запуск ставит venv, systemd и nginx; повторные — только код.
set -euo pipefail
cd "$(dirname "$0")"

H=excelsior
R=/var/www/lebedev
STAMP=$(date +%Y%m%d-%H%M)

echo "1/5 код → сервер"
ssh -o BatchMode=yes $H "mkdir -p $R/backups && cd $R \
  && { [ -f data.db ] && cp data.db backups/data-$STAMP.db || true; }"
git archive --format=tar HEAD | ssh -o BatchMode=yes $H "tar -x -C $R"

echo "2/5 окружение python"
ssh -o BatchMode=yes $H "cd $R \
  && { [ -d venv ] || python3 -m venv venv; } \
  && venv/bin/pip install -q -r requirements.txt"

echo "3/5 .env"
if ssh -o BatchMode=yes $H "[ -f $R/.env ]"; then
  echo "   есть, не трогаю"
else
  scp -o BatchMode=yes .env $H:$R/.env
  ssh -o BatchMode=yes $H "grep -q '^SITE_URL=' $R/.env || echo 'SITE_URL=https://a-lebedev.ru' >> $R/.env"
  echo "   скопирован локальный .env + SITE_URL. Проверь ADMIN_PASSWORD и SECRET_KEY на сервере!"
fi

echo "4/5 systemd + nginx"
ssh -o BatchMode=yes $H "cp $R/deploy/lebedev.service /etc/systemd/system/lebedev.service \
  && systemctl daemon-reload && systemctl enable -q lebedev && systemctl restart lebedev && sleep 2 \
  && curl -s -o /dev/null -w '   uvicorn 8010: %{http_code}\n' http://127.0.0.1:8010/"
if ! ssh -o BatchMode=yes $H "[ -f /etc/nginx/sites-enabled/rsk.a-lebedev.ru ]"; then
  echo "   первый раз: переношу «Дорожную карту» на rsk.a-lebedev.ru, портфолио — в корень"
  ssh -o BatchMode=yes $H "cp /etc/nginx/sites-enabled/a-lebedev.ru /root/a-lebedev.ru.nginx.$STAMP.bak \
    && cp $R/deploy/nginx/rsk.a-lebedev.ru /etc/nginx/sites-available/rsk.a-lebedev.ru \
    && ln -sf /etc/nginx/sites-available/rsk.a-lebedev.ru /etc/nginx/sites-enabled/rsk.a-lebedev.ru \
    && cp $R/deploy/nginx/a-lebedev.ru /etc/nginx/sites-available/a-lebedev.ru \
    && ln -sf /etc/nginx/sites-available/a-lebedev.ru /etc/nginx/sites-enabled/a-lebedev.ru \
    && nginx -t && systemctl reload nginx \
    && certbot --nginx -n --agree-tos -d a-lebedev.ru -d www.a-lebedev.ru 2>&1 | tail -2"
  # Сертификат для поддомена — отдельно: если DNS ещё не прописан, корень не пострадает.
  if ssh -o BatchMode=yes $H "getent hosts rsk.a-lebedev.ru >/dev/null"; then
    ssh -o BatchMode=yes $H "certbot --nginx -n --agree-tos -d rsk.a-lebedev.ru 2>&1 | tail -2"
  else
    echo "   !! rsk.a-lebedev.ru не резолвится: A-запись на 217.114.15.200 не прописана. Поддомен пока без SSL, перезапусти deploy.sh после DNS."
  fi
fi

echo "5/5 проверка снаружи"
curl -s -o /dev/null -w "   https://www.a-lebedev.ru: %{http_code} (ждём 200)\n" https://www.a-lebedev.ru/
curl -s -o /dev/null -w "   https://rsk.a-lebedev.ru: %{http_code} (ждём 200 или 302 на вход)\n" https://rsk.a-lebedev.ru/
echo "готово."
