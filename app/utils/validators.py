import re
BRIDGE_PATTERNS = [re.compile(r'^(?:Bridge\s+)?obfs4\s+\S+\s+\d+\s+\S+'), re.compile(r'^(?:Bridge\s+)?webtunnel\s+\S+:\d+'), re.compile(r'^(?:Bridge\s+)?snowflake\s*'), re.compile(r'^(?:Bridge\s+)?[a-zA-Z0-9]+\s+\S+:\d+')]
def validate_port(port):
    try:
        p = int(port)
        return 1 <= p <= 65535
    except: return False
def validate_bridge_line(line):
    line = line.strip()
    if not line or line.startswith('#'): return True
    return any(p.match(line) for p in BRIDGE_PATTERNS)
def normalize_bridge_line(line):
    return line.strip()
def validate_torrc(content):
    errors = []
    for i, line in enumerate(content.split('\n'), 1):
        s = line.strip()
        if s and not s.startswith('#'):
            if 'SOCKSPort' in s:
                parts = s.split()
                if len(parts) >= 2 and not validate_port(parts[-1].split(':')[-1]):
                    errors.append(f'Line {i}: Invalid SOCKS port')
            if 'ControlPort' in s:
                parts = s.split()
                if len(parts) >= 2 and not validate_port(parts[-1].split(':')[-1]):
                    errors.append(f'Line {i}: Invalid Control port')
    return errors
