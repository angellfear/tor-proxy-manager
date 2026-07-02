from flask import Blueprint, jsonify, request
api_bp = Blueprint('api', __name__, url_prefix='/api')

@api_bp.route('/status')
def api_status():
    from app.services.tor_service import get_status
    return jsonify(get_status())

@api_bp.route('/config')
def api_get_config():
    from app.utils.config import load_settings
    return jsonify(load_settings())

@api_bp.route('/config', methods=['POST'])
def api_save_config():
    from app.utils.config import load_settings, save_settings, load_torrc_base, save_torrc_base, generate_torrc
    from app.services.tor_service import reload_tor, set_privoxy_state
    import re
    data = request.get_json()
    if not data: return jsonify({'error': 'Invalid JSON'}), 400
    settings = load_settings()
    for k, v in data.items():
        settings[k] = v
    save_settings(settings)
    if 'http_proxy_enabled' in data or 'http_port' in data:
        set_privoxy_state(settings.get('http_proxy_enabled', True), settings.get('http_port', 8118))
    if 'log_level' in data:
        base = load_torrc_base()
        base = re.sub(r'^Log\s+\S+', f'Log {data["log_level"].upper()}', base, flags=re.M)
        save_torrc_base(base)
        generate_torrc(settings)
        reload_tor()
    return jsonify({'status': 'ok'})

@api_bp.route('/restart', methods=['POST'])
def api_restart():
    from app.services.tor_service import restart_tor
    return jsonify({'status': 'ok' if restart_tor() else 'error'})

@api_bp.route('/reload', methods=['POST'])
def api_reload():
    from app.services.tor_service import reload_tor
    return jsonify({'status': 'ok' if reload_tor() else 'error'})

@api_bp.route('/newnym', methods=['POST'])
def api_newnym():
    from app.services.tor_service import newnym
    return jsonify({'status': 'ok' if newnym() else 'error'})

@api_bp.route('/log')
def api_log():
    from app.services.tor_service import get_logs
    lines = request.args.get('lines', 100, type=int)
    return jsonify({'log': get_logs(lines)})
