import secrets
import json
from pathlib import Path
from flask import Blueprint, render_template, request, session, flash, redirect, jsonify
config_bp = Blueprint('config', __name__)

@config_bp.route('/config')
def config_page():
    from app.utils.config import load_settings
    return render_template('config.html', settings=load_settings(),
                           current_user=session.get('user', ''))

@config_bp.route('/config/toggle_http_proxy', methods=['POST'])
def toggle_http_proxy():
    from app.utils.config import load_settings, save_settings
    from app.services.tor_service import set_privoxy_state
    data = request.get_json()
    if not data: return jsonify({'error': 'Invalid JSON'}), 400
    settings = load_settings()
    settings['http_proxy_enabled'] = data.get('enabled', False)
    settings['http_port'] = data.get('port', 8118)
    save_settings(settings)
    ok = set_privoxy_state(settings['http_proxy_enabled'], settings['http_port'])
    return jsonify({'status': 'ok' if ok else 'error'})

@config_bp.route('/config/save_exclude_countries', methods=['POST'])
def save_exclude_countries():
    from app.utils.config import load_settings, save_settings, load_torrc_base, save_torrc_base, generate_torrc
    from app.services.tor_service import reload_tor
    import re
    data = request.get_json()
    if not data: return jsonify({'error': 'Invalid JSON'}), 400
    countries = data.get('exclude_countries', '').strip()
    settings = load_settings()
    settings['exclude_countries'] = countries
    save_settings(settings)
    base = load_torrc_base()
    cc = ','.join('{' + c.strip() + '}' for c in countries.split(',') if c.strip()) if countries else ''
    if cc:
        if re.search(r'^ExcludeExitNodes\s', base, re.M):
            base = re.sub(r'^ExcludeExitNodes\s.*$', f'ExcludeExitNodes {cc}', base, flags=re.M)
        else:
            base += f'\nExcludeExitNodes {cc}'
        if not re.search(r'^StrictNodes\s', base, re.M):
            base += '\nStrictNodes 1'
    else:
        base = re.sub(r'^ExcludeExitNodes\s.*$', '', base, flags=re.M).strip()
        base = re.sub(r'^StrictNodes\s.*$', '', base, flags=re.M).strip()
    save_torrc_base(base)
    generate_torrc(settings)
    reload_tor()
    return jsonify({'status': 'ok'})

@config_bp.route('/config/set_log_level', methods=['POST'])
def set_log_level():
    from app.utils.config import load_settings, save_settings, load_torrc_base, save_torrc_base, generate_torrc
    from app.services.tor_service import reload_tor
    import re
    data = request.get_json()
    if not data: return jsonify({'error': 'Invalid JSON'}), 400
    lvl = data.get('log_level', 'notice')
    if lvl not in ('debug', 'info', 'notice', 'warn', 'error'):
        return jsonify({'error': 'Invalid log level'}), 400
    settings = load_settings()
    settings['log_level'] = lvl
    save_settings(settings)
    base = load_torrc_base()
    base = re.sub(r'^Log\s+\S+', f'Log {lvl.upper()}', base, flags=re.M)
    save_torrc_base(base)
    generate_torrc(settings)
    reload_tor()
    return jsonify({'status': 'ok'})

@config_bp.route('/config/apply_auth', methods=['POST'])
def apply_auth():
    from app.utils.config import load_settings, save_settings
    import hashlib, json
    username = request.form.get('username', '').strip()
    password = request.form.get('password', '')
    require_auth = request.form.get('require_auth') == 'on'
    settings = load_settings()
    settings['require_auth'] = require_auth
    save_settings(settings)
    if require_auth and username and password:
        if len(password) < 6:
            flash('Password must be at least 6 characters', 'danger')
            return redirect('/config')
        salt = secrets.token_hex(16)
        h = hashlib.sha256((salt + password).encode()).hexdigest()
        users = {username: {'password': f'{salt}:{h}', 'role': 'admin'}}
        Path('/config/users.json').write_text(json.dumps(users, indent=2))
        flash('Authentication enabled and user saved', 'success')
    elif require_auth:
        flash('Username and password required when auth is enabled', 'danger')
    else:
        flash('Authentication disabled', 'success')
    return redirect('/config')
