#!/bin/bash
# Systemd Service Installer for Falcon Trading Platform
# FHS-compliant with service account support
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
INSTALL_DIR="${1:-/opt/falcon}"
CONFIG_DIR="${2:-/etc/falcon}"
SERVICE_USER="${3:-falcon}"
SYSTEMD_DIR="/etc/systemd/system"

echo -e "${BLUE}Installing systemd service...${NC}"

# Create systemd service file
cat > "${SYSTEMD_DIR}/falcon-dashboard.service" << EOF
[Unit]
Description=Falcon Trading Dashboard
After=network.target
Wants=network-online.target

[Service]
Type=simple
User=${SERVICE_USER}
Group=${SERVICE_USER}
WorkingDirectory=${INSTALL_DIR}
Environment="PATH=${INSTALL_DIR}/venv/bin:/usr/local/bin:/usr/bin:/bin"
Environment="FALCON_ENV=production"
EnvironmentFile=-${CONFIG_DIR}/config.conf
EnvironmentFile=-${CONFIG_DIR}/secrets.env
ExecStart=${INSTALL_DIR}/venv/bin/python3 ${INSTALL_DIR}/dashboard_server.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

# Security settings
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/var/lib/falcon
ReadWritePaths=/var/cache/falcon
ReadWritePaths=/var/log/falcon
ReadOnlyPaths=${CONFIG_DIR}

[Install]
WantedBy=multi-user.target
EOF

echo -e "${GREEN}✓ Service file created${NC}"

# Reload systemd (skip in Docker build)
if [ -z "$DOCKER_BUILD" ]; then
    systemctl daemon-reload
    echo -e "${GREEN}✓ Systemd reloaded${NC}"
else
    echo -e "${YELLOW}⚠ Skipping systemctl daemon-reload (Docker build)${NC}"
fi

echo -e "${GREEN}✓ Service installed successfully${NC}"
echo -e "${YELLOW}Note: Configure API keys in ${CONFIG_DIR}/secrets.env${NC}"
