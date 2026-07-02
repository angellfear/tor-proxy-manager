import json
from pathlib import Path

SETTINGS_PATH = Path('/config/settings.json')
TORRC_PATH = Path('/config/torrc')
TORRC_BASE_PATH = Path('/config/torrc_base')
BRIDGES_PATH = Path('/config/bridges.txt')

DEFAULT_SETTINGS = {
    'socks_port': 9050, 'http_port': 8118, 'control_port': 9051, 'dns_port': 9053,
    'log_level': 'notice', 'use_bridges': False, 'auto_start': True, 'nickname': '',
    'require_auth': False, 'http_proxy_enabled': True,
    'exclude_countries': 'ru,by,ua'
}

def load_settings():
    if SETTINGS_PATH.exists():
        with open(SETTINGS_PATH) as f:
            merged = DEFAULT_SETTINGS.copy()
            merged.update(json.load(f))
            return merged
    return dict(DEFAULT_SETTINGS)

def save_settings(data):
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(SETTINGS_PATH, 'w') as f:
        json.dump(data, f, indent=2)

def load_torrc():
    if TORRC_PATH.exists():
        return TORRC_PATH.read_text()
    return ''

def save_torrc(content):
    TORRC_PATH.parent.mkdir(parents=True, exist_ok=True)
    TORRC_PATH.write_text(content)

def load_torrc_base():
    if TORRC_BASE_PATH.exists():
        return TORRC_BASE_PATH.read_text()
    return ''

def save_torrc_base(content):
    TORRC_BASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    TORRC_BASE_PATH.write_text(content)

def load_bridges():
    if BRIDGES_PATH.exists():
        return BRIDGES_PATH.read_text()
    return ''

def save_bridges(content):
    BRIDGES_PATH.parent.mkdir(parents=True, exist_ok=True)
    BRIDGES_PATH.write_text(content)

def generate_torrc(settings):
    base = load_torrc_base()
    parts = [base.rstrip('\n')]
    if settings.get('use_bridges'):
        bridges = load_bridges()
        for bline in bridges.strip().split('\n'):
            bline = bline.strip()
            if bline and not bline.startswith('#'):
                prefix = 'Bridge ' if not bline.startswith('Bridge ') else ''
                parts.append(f'{prefix}{bline}')
    parts.append('')
    content = '\n'.join(parts)
    save_torrc(content)
    return content
