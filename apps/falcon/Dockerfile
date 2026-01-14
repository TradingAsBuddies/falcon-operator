# Falcon Trading Platform - Production Container
# Multi-stage build for optimized image size

FROM debian:bookworm-slim AS builder

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    openssl \
    rsync \
    make \
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Create working directory
WORKDIR /build

# Copy source code
COPY . /build/

# Note: Skip 'make' check here since systemctl isn't available during build
# The full 'make install' will be run in the production stage

# Production stage
FROM debian:bookworm-slim

LABEL org.opencontainers.image.title="Falcon Trading Platform"
LABEL org.opencontainers.image.description="AI-powered algorithmic trading system"
LABEL org.opencontainers.image.authors="Falcon Team"
LABEL org.opencontainers.image.source="https://github.com/davdunc/falcon"

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    python3 \
    python3-pip \
    python3-venv \
    nginx \
    openssl \
    rsync \
    make \
    systemd \
    ca-certificates \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy source from builder
COPY --from=builder /build /opt/falcon-src

# Set working directory
WORKDIR /opt/falcon-src

# Create falcon user (will be recreated by make install, but needed for permissions)
RUN useradd -r -s /bin/false -d /var/lib/falcon -M falcon

# Run installation with Docker build flag
ENV DOCKER_BUILD=1
RUN make install

# Create entrypoint script
RUN cat > /usr/local/bin/falcon-entrypoint.sh << 'EOF'
#!/bin/bash
set -e

echo "Falcon Trading Platform - Container Starting"
echo "=============================================="

# Check if secrets are configured
if [ ! -f "/etc/falcon/secrets.env" ]; then
    echo "WARNING: /etc/falcon/secrets.env not found"
    echo "Creating template secrets file..."
    cp /etc/falcon/secrets.env /etc/falcon/secrets.env.template 2>/dev/null || true
fi

# Validate configuration
echo "Validating configuration..."
cd /opt/falcon
FALCON_ENV=production /opt/falcon/venv/bin/python3 config.py --validate || {
    echo "WARNING: Configuration validation failed"
    echo "Please check /etc/falcon/secrets.env"
}

# Start nginx (optional - may fail in container)
echo "Starting nginx..."
nginx -t && nginx || {
    echo "WARNING: nginx failed to start (this is OK in container mode)"
    echo "Flask will serve directly on port 5000"
}

# Start falcon dashboard
echo "Starting Falcon Dashboard..."
echo "=============================================="
cd /opt/falcon
exec /opt/falcon/venv/bin/python3 dashboard_server.py
EOF

RUN chmod +x /usr/local/bin/falcon-entrypoint.sh

# Expose ports
EXPOSE 80 443 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Volume mounts for persistence (not /etc/falcon - configs are baked into image)
VOLUME ["/var/lib/falcon", "/var/cache/falcon", "/var/log/falcon"]

# Run as falcon user
USER falcon

# Set environment
ENV FALCON_ENV=production
ENV PYTHONUNBUFFERED=1

# Entrypoint
ENTRYPOINT ["/usr/local/bin/falcon-entrypoint.sh"]
