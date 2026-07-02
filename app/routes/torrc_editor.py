from flask import Blueprint, render_template, request, flash, redirect, Response
torrc_bp = Blueprint('torrc', __name__)
DEFAULT_TORRC = 'SOCKSPort 0.0.0.0:9050\nControlPort 0.0.0.0:9051\nLog NOTICE stdout\nDataDirectory /var/lib/tor\nAvoidDiskWrites 1\nSafeLogging 1\nCookieAuthentication 1\nHashedControlPassword ""\nGeoIPFile /usr/share/tor/geoip\nGeoIPv6File /usr/share/tor/geoip6\nExcludeExitNodes {ru},{by},{ua}\nStrictNodes 1\nUseBridges 1\nClientTransportPlugin obfs4 exec /usr/bin/obfs4proxy\nClientTransportPlugin snowflake exec /usr/bin/snowflake-client\nClientTransportPlugin webtunnel exec /usr/local/bin/webtunnel-client\n'

@torrc_bp.route('/torrc')
def torrc_page():
    from app.utils.config import load_torrc_base
    return render_template('torrc_editor.html', torrc_content=load_torrc_base())

@torrc_bp.route('/torrc/save', methods=['POST'])
def save_torrc():
    from app.utils.config import save_torrc_base, load_settings, generate_torrc
    from app.utils.validators import validate_torrc
    content = request.form.get('torrc_content', '')
    errors = validate_torrc(content)
    if errors:
        for e in errors: flash(e, 'danger')
        return redirect('/torrc')
    save_torrc_base(content)
    generate_torrc(load_settings())
    from app.services.tor_service import reload_tor
    reload_tor()
    flash('torrc saved and Tor reloaded', 'success')
    return redirect('/torrc')

@torrc_bp.route('/torrc/default', methods=['POST'])
def restore_default():
    from app.utils.config import save_torrc_base, load_settings, generate_torrc
    save_torrc_base(DEFAULT_TORRC)
    generate_torrc(load_settings())
    from app.services.tor_service import reload_tor
    reload_tor()
    flash('Default torrc restored', 'success')
    return redirect('/torrc')

@torrc_bp.route('/torrc/download')
def download_torrc():
    from app.utils.config import load_torrc_base
    return Response(load_torrc_base(), mimetype='text/plain', headers={'Content-Disposition': 'attachment; filename=torrc_base'})

@torrc_bp.route('/torrc/upload', methods=['POST'])
def upload_torrc():
    from app.utils.config import save_torrc_base, load_settings, generate_torrc
    from app.utils.validators import validate_torrc
    file = request.files.get('torrc_file')
    if not file: flash('No file uploaded', 'danger'); return redirect('/torrc')
    content = file.read().decode('utf-8')
    errors = validate_torrc(content)
    if errors:
        for e in errors: flash(e, 'danger')
        return redirect('/torrc')
    save_torrc_base(content)
    generate_torrc(load_settings())
    flash('torrc uploaded and Tor reloaded', 'success')
    return redirect('/torrc')
