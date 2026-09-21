# Портфолио: корень домена. Статику отдаёт nginx, остальное — uvicorn на 8010.
# SSL-блок дописывает certbot --nginx.
server {
    listen 80;
    listen [::]:80;
    server_name a-lebedev.ru www.a-lebedev.ru;

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
