#!/bin/bash
# Nginx Configuration Installer for Falcon Trading Platform
# FHS-compliant installation
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Variables
INSTALL_DIR="${1:-/opt/falcon}"
DATA_DIR="${2:-/var/lib/falcon}"
NGINX_AVAILABLE="/etc/nginx/sites-available"
NGINX_ENABLED="/etc/nginx/sites-enabled"
SSL_DIR="/etc/nginx/ssl"

echo -e "${BLUE}Installing nginx configuration...${NC}"

# Create nginx configuration
cat > "${NGINX_AVAILABLE}/falcon" << 'EOF'
# Falcon Trading Platform - Nginx Configuration
# Reverse proxy to Flask dashboard with HTTPS support

upstream falcon_dashboard {
    server 127.0.0.1:5000;
}

# Redirect HTTP to HTTPS
server {
    listen 80 default_server;
    listen [::]:80 default_server;
    server_name _;
    return 301 https://$host$request_uri;
}

# HTTPS server
server {
    listen 443 ssl default_server;
    listen [::]:443 ssl default_server;
    server_name _;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/falcon.crt;
    ssl_certificate_key /etc/nginx/ssl/falcon.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;

    # Logging
    access_log /var/log/nginx/falcon_access.log;
    error_log /var/log/nginx/falcon_error.log;

    # Root for static files (landing page, etc.)
    root INSTALL_DIR_PLACEHOLDER/www;
    index index.html;

    # Landing page
    location = / {
        try_files /index.html =404;
    }

    # Static HTML pages
    location ~* \.(html|css|js)$ {
        try_files $uri =404;
        expires 1h;
    }

    # Falcon Dashboard API and UI
    location /dashboard {
        proxy_pass http://falcon_dashboard/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API endpoints - direct proxy
    location /api/ {
        proxy_pass http://falcon_dashboard/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # For Server-Sent Events
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400s;
    }

    # Static files from falcon directory
    location /static/ {
        alias INSTALL_DIR_PLACEHOLDER/www/static/;
        expires 1d;
    }

    # Health check endpoint
    location /health {
        return 200 'OK';
        add_header Content-Type text/plain;
    }
}
EOF

# Replace placeholder with actual path
sed -i "s|INSTALL_DIR_PLACEHOLDER|${INSTALL_DIR}|g" "${NGINX_AVAILABLE}/falcon"

echo -e "${GREEN}✓ Nginx configuration file created${NC}"

# Remove default nginx site if it exists
if [ -L "${NGINX_ENABLED}/default" ]; then
    echo -e "${YELLOW}Removing default nginx site...${NC}"
    rm -f "${NGINX_ENABLED}/default"
fi

# Enable falcon site
if [ -L "${NGINX_ENABLED}/falcon" ]; then
    rm -f "${NGINX_ENABLED}/falcon"
fi
ln -s "${NGINX_AVAILABLE}/falcon" "${NGINX_ENABLED}/falcon"
echo -e "${GREEN}✓ Nginx site enabled${NC}"

# Set permissions on www directory
if [ -d "${INSTALL_DIR}/www" ]; then
    chmod -R 755 "${INSTALL_DIR}/www"
    echo -e "${GREEN}✓ WWW directory permissions set${NC}"
fi

echo -e "${GREEN}✓ Nginx configuration installed successfully${NC}"
