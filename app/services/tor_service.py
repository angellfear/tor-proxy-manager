import os
import logging
import subprocess
import threading
from pathlib import Path
from stem import Signal
from stem.control import Controller
logger = logging.getLogger(__name__)

_controller = None
_controller_lock = threading.Lock()

def get_controller():
    global _controller
    if _controller is not None:
        try:
            _controller.get_info('version')
            return _controller
        except:
            try: _controller.close()
            except: pass
            _controller = None
    with _controller_lock:
        if _controller is not None:
            return _controller
        try:
            c = Controller.from_port(port=9051)
            c.authenticate()
            _controller = c
            return c
        except Exception as e:
            logger.error(f'Failed to connect to Tor control: {e}')
            return None

def get_status():
    c = get_controller()
    if not c:
        return {'running': False, 'bootstrapped': False, 'exit_ip': None, 'country': None, 'transport': None, 'bridges_enabled': False, 'tor_version': None, 'uptime': None, 'bootstrap_percent': 0, 'circuits': 0}
    status = {'running': True}
    try:
        bp = c.get_info('status/bootstrap-phase')
        status['bootstrapped'] = 'PROGRESS=100' in bp
        status['bootstrap_percent'] = 0
        for part in bp.split():
            if part.startswith('PROGRESS='):
                try: status['bootstrap_percent'] = int(part.split('=')[1])
                except: pass
        try:
            ver = c.get_info('version')
            status['tor_version'] = ver.split()[0] if ver else None
        except: status['tor_version'] = None
        try:
            uptime_secs = c.get_info('uptime')
            status['uptime'] = int(float(uptime_secs)) if uptime_secs else None
        except: status['uptime'] = None
    except:
        status['bootstrapped'] = False
        status['bootstrap_percent'] = 0
    try:
        circs = c.get_circuits()
        status['circuits'] = len([circ for circ in circs if circ.status == 'BUILT'])
        for circ in circs:
            if circ.status == 'BUILT' and len(circ.path) > 0:
                last = circ.path[-1]
                if last:
                    fp = last[0]
                    try:
                        ns = c.get_network_status(fp)
                        if ns: status['exit_ip'] = ns.address
                    except: pass
                    if not status.get('exit_ip'):
                        status['exit_ip'] = fp[:8] + '...'
                    break
    except: status['circuits'] = 0
    try:
        status['bridges_enabled'] = c.get_conf('UseBridges') == '1'
        transports = c.get_conf('ClientTransportPlugin')
        if transports:
            if 'obfs4' in transports: status['transport'] = 'obfs4'
            elif 'snowflake' in transports: status['transport'] = 'snowflake'
            elif 'webtunnel' in transports: status['transport'] = 'webtunnel'
            else: status['transport'] = 'none'
        else: status['transport'] = 'none'
    except:
        status['bridges_enabled'] = False
        status['transport'] = 'none'
    if status.get('exit_ip') and not status.get('country'):
        try:
            cc = c.get_info(f'ip-to-country/{status["exit_ip"]}')
            if cc and cc != '??':
                status['country'] = cc.upper()
        except: pass
    return status
def newnym():
    c = get_controller()
    if not c: return False
    try: c.signal(Signal.NEWNYM); return True
    except: return False
def reload_tor():
    c = get_controller()
    if not c: return False
    try: c.signal(Signal.RELOAD); return True
    except: return False
def restart_tor():
    global _controller
    try:
        if _controller is not None:
            try: _controller.close()
            except: pass
            _controller = None
        r = subprocess.run(['supervisorctl', 'restart', 'tor'], timeout=10, capture_output=True)
        return r.returncode == 0
    except: return False
def get_logs(lines=100):
    logfile = '/var/log/tor/notices.log'
    if not os.path.exists(logfile): logfile = '/var/log/tor/tor-stdout.log'
    try:
        with open(logfile) as f:
            all_lines = f.readlines()
            return ''.join(all_lines[-lines:])
    except: return ''
def set_privoxy_state(enabled, port=8118):
    try:
        if enabled:
            config = f'''confdir /etc/privoxy
logdir /var/log/tor
listen-address  0.0.0.0:{port}
forward-socks5t / 127.0.0.1:9050 .
forward          /  .
'''
            Path('/etc/privoxy/config').write_text(config)
            subprocess.run(['supervisorctl', 'start', 'privoxy'], timeout=10, capture_output=True)
        else:
            subprocess.run(['supervisorctl', 'stop', 'privoxy'], timeout=10, capture_output=True)
        return True
    except Exception as e:
        logger.error(f'Failed to set privoxy state: {e}')
        return False
