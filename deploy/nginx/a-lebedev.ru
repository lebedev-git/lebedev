# Портфолио: корень домена. Статику отдаёт nginx, остальное — uvicorn на 8010.
# Канонический адрес — www.a-lebedev.ru: сертификат Let's Encrypt выпущен на него,
# а голый a-lebedev.ru имеет AAAA-запись на парковку Timeweb, из-за чего проверка
# certbot по IPv6 проваливается. Когда AAAA удалят — добавить a-lebedev.ru в сертификат:
#   certbot --nginx --expand --cert-name www.a-lebedev.ru -d www.a-lebedev.ru -d a-lebedev.ru
server {
    listen 80;
    listen [::]:80;
    server_name a-lebedev.ru www.a-lebedev.ru;
    return 301 https://www.a-lebedev.ru$request_uri;
}

server {
    listen 443 ssl;
    listen [::]:443 ssl;
    server_name a-lebedev.ru www.a-lebedev.ru;

    ssl_certificate /etc/letsencrypt/live/www.a-lebedev.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/www.a-lebedev.ru/privkey.pem;
    include /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam /etc/letsencrypt/ssl-dhparams.pem;

    client_max_body_size 6m;

    location /static/ {
        alias /var/www/lebedev/app/static/;
        expires 30d;
        add_header Cache-Control "public";
    }

    location / {
        proxy_pass http://127.0.0.1:8010;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
