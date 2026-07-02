from flask import Blueprint, render_template, request, flash, redirect
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
    normalized = []
    errors = []
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'): normalized.append(line); continue
        if not validate_bridge_line(stripped): errors.append(f'Line {i}: Invalid bridge format'); continue
        normalized.append(normalize_bridge_line(stripped))
    if errors:
        for e in errors: flash(e, 'danger')
        return redirect('/bridges')
    _save_bridges('\n'.join(normalized))
    generate_torrc(load_settings())
    from app.services.tor_service import reload_tor
    reload_tor()
    flash('Bridges saved and Tor reloaded', 'success')
    return redirect('/bridges')
