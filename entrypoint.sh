#!/bin/bash
set -e

if [ ! -f /config/torrc_base ]; then
    cp /app/config/default_torrc /config/torrc_base
fi
if [ ! -f /config/bridges.txt ]; then
    touch /config/bridges.txt
fi
if [ ! -f /config/settings.json ]; then
    echo '{"socks_port": 9050, "http_port": 8118, "control_port": 9051, "dns_port": 9053, "log_level": "notice", "use_bridges": true, "auto_start": true, "require_auth": false, "http_proxy_enabled": true, "exclude_countries": "ru,by,ua"}' > /config/settings.json
fi
if [ ! -f /config/users.json ]; then
    python3 -c "import hashlib, secrets, json; salt=secrets.token_hex(16); h=hashlib.sha256((salt+'admin123').encode()).hexdigest(); json.dump({'admin':{'password':f'{salt}:{h}','role':'admin'}}, open('/config/users.json','w'), indent=2)"
fi
if [ ! -f /etc/privoxy/config ]; then
    cat > /etc/privoxy/config << PRIVOXY
confdir /etc/privoxy
logdir /var/log/tor
listen-address  0.0.0.0:8118
forward-socks5t / 127.0.0.1:9050 .
forward          /  .
PRIVOXY
fi

# Генерируем полный torrc из базы + бриджей + настроек
cd /app && python3 -c "
import sys; sys.path.insert(0, '/')
from app.utils.config import load_settings, generate_torrc
generate_torrc(load_settings())
" || echo 'Warning: torrc generation failed (will be generated on first web save)'

# Периодическая чистка логов старше 3 часов (запуск в фоне)
cleanup_logs() {
    while true; do
        find /var/log/tor -name '*.log' -mmin +180 -delete 2>/dev/null
        sleep 3600
    done
}
cleanup_logs &
chown -R torproxy:torproxy /config /var/lib/tor /var/log/tor /var/log/supervisor /etc/privoxy
exec /usr/bin/supervisord -c /etc/supervisor/supervisord.conf
