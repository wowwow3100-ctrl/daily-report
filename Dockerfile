# Railway static hosting for the news site (GitHub Pages ignores this file)
FROM caddy:2-alpine
COPY Caddyfile /etc/caddy/Caddyfile
COPY . /srv
