FROM golang:1.23-bookworm AS webtunnel-builder
ENV GOPROXY=https://proxy.golang.org,direct
RUN go install gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/webtunnel/main/server@v0.0.4 \
    && mv /go/bin/server /go/bin/webtunnel-server \
    && go install gitlab.torproject.org/tpo/anti-censorship/pluggable-transports/webtunnel/main/client@v0.0.4 \
    && mv /go/bin/client /go/bin/webtunnel-client

FROM debian:bookworm-slim
COPY --from=webtunnel-builder /go/bin/webtunnel-server /usr/local/bin/webtunnel-server
COPY --from=webtunnel-builder /go/bin/webtunnel-client /usr/local/bin/webtunnel-client

RUN apt-get update && apt-get install -y --no-install-recommends \
    tor \
    tor-geoipdb \
    privoxy \
    obfs4proxy \
    snowflake-client \
    python3 \
    python3-pip \
    python3-venv \
    tini \
    supervisor \
    curl \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

RUN ln -s /usr/bin/python3 /usr/bin/python
RUN python3 -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
COPY requirements.txt /tmp/requirements.txt
RUN pip3 install --no-cache-dir -r /tmp/requirements.txt
RUN mkdir -p /config /var/lib/tor /var/log/tor /var/log/supervisor
COPY supervisord.conf /etc/supervisor/supervisord.conf
COPY entrypoint.sh /entrypoint.sh
COPY app/ /app
RUN chmod +x /entrypoint.sh
RUN useradd -r -s /bin/false torproxy \
    && chown -R torproxy:torproxy /config /var/lib/tor /var/log/tor /var/log/supervisor
EXPOSE 8080 9050 8118 9051 9053
VOLUME ["/config", "/var/lib/tor", "/var/log/tor"]
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://127.0.0.1:8080/api/status | python3 -c "import sys,json; d=json.load(sys.stdin); sys.exit(0 if d.get('bootstrapped') else 1)"
ENTRYPOINT ["/usr/bin/tini", "--", "/entrypoint.sh"]
