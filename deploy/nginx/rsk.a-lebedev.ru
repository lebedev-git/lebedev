# «Дорожная карта» (Project/Rabota): переехала с корня домена на поддомен.
# Приложение под PM2 на 3000, конфиг проксирования тот же, что был у a-lebedev.ru.
# SSL-блок дописывает certbot --nginx.
server {
    listen 80;
    listen [::]:80;
    server_name rsk.a-lebedev.ru;

    client_max_body_size 50m;

    location / {
        proxy_pass http://127.0.0.1:3000;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
