import time, os
from flask import Blueprint, render_template, Response, stream_with_context
logs_bp = Blueprint('logs', __name__)
@logs_bp.route('/logs')
def logs_page():
    return render_template('logs.html')
@logs_bp.route('/logs/stream')
def stream_logs():
    def sse(data):
        for line in data.rstrip('\n').split('\n'):
            yield f'data: {line}\n'
        yield '\n'
    def generate():
        from app.services.tor_service import get_logs
        yield from sse(get_logs(50))
        last_size = 0
        logfile = '/var/log/tor/notices.log'
        if not os.path.exists(logfile): logfile = '/var/log/tor/tor-stdout.log'
        while True:
            try:
                if os.path.exists(logfile):
                    current_size = os.path.getsize(logfile)
                    if current_size < last_size:
                        last_size = 0
                    if current_size > last_size:
                        with open(logfile) as f:
                            f.seek(last_size)
                            new_data = f.read()
                            yield from sse(new_data)
                            last_size = f.tell()
            except: pass
            time.sleep(1)
    return Response(stream_with_context(generate()), mimetype='text/event-stream')
@logs_bp.route('/logs/download')
def download_logs():
    from app.services.tor_service import get_logs
    return Response(get_logs(5000), mimetype='text/plain', headers={'Content-Disposition': 'attachment; filename=tor.log'})
