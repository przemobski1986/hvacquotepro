# Minimal Nginx reverse proxy for VPS

Assuming:
- API runs on 127.0.0.1:8000
- Domain: api.yourdomain.com

Install:
```bash
sudo apt update
sudo apt install -y nginx
```

Config `/etc/nginx/sites-available/hvacquotepro-api`:
```nginx
server {
    listen 80;
    server_name api.yourdomain.com;

    client_max_body_size 20m;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }
}
```

Enable:
```bash
sudo ln -s /etc/nginx/sites-available/hvacquotepro-api /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

TLS (recommended): use Certbot or Caddy. 
