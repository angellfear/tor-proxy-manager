from flask import Blueprint, render_template, request, flash, redirect, jsonify
bridges_bp = Blueprint('bridges', __name__)
@bridges_bp.route('/bridges')
def bridges_page():
    from app.utils.config import load_bridges
    return render_template('bridges.html', bridges=load_bridges())
@bridges_bp.route('/bridges/save', methods=['POST'])
def save_bridges():
    from app.utils.config import save_bridges as _save_bridges, load_settings, generate_torrc
    from app.utils.validators import validate_bridge_line, normalize_bridge_line
    content = request.form.get('bridges', '')
    lines = content.split('\n')
    seen = set()
    normalized = []
    errors = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'): normalized.append(line); continue
        if not validate_bridge_line(stripped): errors.append(f'Line {i}: Invalid bridge format'); continue
        key = normalize_bridge_line(stripped)
        if key in seen: continue
        seen.add(key)
        normalized.append(key)
    if errors:
        for e in errors: flash(e, 'danger')
        return redirect('/bridges')
    _save_bridges('\n'.join(normalized))
    generate_torrc(load_settings())
    from app.services.tor_service import reload_tor
    reload_tor()
    flash('Bridges saved and Tor reloaded', 'success')
    return redirect('/bridges')
@bridges_bp.route('/bridges/broken', methods=['GET'])
def broken_bridges():
    from app.utils.config import load_bridges
    from app.services.tor_service import get_logs
    import re
    bridges = [l.strip() for l in load_bridges().strip().split('\n') if l.strip()]
    if not bridges: return jsonify({'broken': [], 'working': []})
    logs = get_logs(2000)
    broken = []
    working = []
    for b in bridges:
        addr = b.split()[1] if len(b.split()) > 1 and not b.split()[1].startswith('[') else (b.split()[1] if len(b.split()) > 1 else b)
        fail_patterns = [
            re.escape(addr) + r'.*?(?:not reachable|failed|giving up|timeout|broken)',
            r'(?:not reachable|failed|giving up|timeout).*?' + re.escape(addr),
        ]
        is_broken = any(re.search(p, logs, re.I) for p in fail_patterns)
        if is_broken: broken.append(b)
        else: working.append(b)
    return jsonify({'broken': broken, 'working': working})
@bridges_bp.route('/bridges/remove_broken', methods=['POST'])
def remove_broken():
    from app.utils.config import load_bridges, save_bridges as _save_bridges, load_settings, generate_torrc
    from app.services.tor_service import reload_tor, get_logs
    import re
    bridges = [l.strip() for l in load_bridges().strip().split('\n') if l.strip()]
    if not bridges: return jsonify({'status': 'ok'})
    logs = get_logs(2000)
    good = []
    for b in bridges:
        addr = b.split()[1] if len(b.split()) > 1 and not b.split()[1].startswith('[') else (b.split()[1] if len(b.split()) > 1 else b)
        fail_patterns = [
            re.escape(addr) + r'.*?(?:not reachable|failed|giving up|timeout|broken)',
            r'(?:not reachable|failed|giving up|timeout).*?' + re.escape(addr),
        ]
        if not any(re.search(p, logs, re.I) for p in fail_patterns):
            good.append(b)
    _save_bridges('\n'.join(good))
    generate_torrc(load_settings())
    reload_tor()
    return jsonify({'status': 'ok', 'removed': len(bridges) - len(good), 'remaining': len(good)})
