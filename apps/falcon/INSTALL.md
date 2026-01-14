# Falcon Trading Platform - Installation Guide

## Overview

This guide covers the installation of the Falcon Trading Platform using the FHS-compliant GNU Make-based installer. The installation follows the **Filesystem Hierarchy Standard (FHS)** and includes:

- Dedicated `falcon` service account (no login, no home directory)
- FHS-compliant directory structure
- Python application with isolated virtual environment
- Database abstraction layer (SQLite or PostgreSQL)
- SystemD service for automatic startup
- Nginx reverse proxy with HTTPS/SSL
- Proper permission management
- Configuration management system

## System Requirements

### Minimum Requirements
- **OS:** Linux (Debian/Ubuntu/Raspberry Pi OS)
- **Architecture:** ARM64 or x86_64
- **Memory:** 2GB+ RAM recommended
- **Disk:** 3GB free space
- **Python:** 3.9+

### Required Packages
- python3
- python3-venv
- pip3
- nginx
- systemd
- openssl
- rsync

### Optional Packages
- postgresql (if using PostgreSQL instead of SQLite)
- postgresql-client

### Root Access
Installation requires root/sudo privileges.

## Quick Start

```bash
# 1. Clone or download the repository
cd /home/ospartners/src/falcon

# 2. Check dependencies
make

# 3. Install as root (creates service account, sets up FHS directories)
sudo make install

# 4. Configure API keys
sudo nano /etc/falcon/secrets.env

# 5. Start services
sudo make start

# 6. Check status
sudo make status

# 7. Access at https://localhost/
```

## Installation Directory Structure

The installer creates an FHS-compliant directory structure:

```
/opt/falcon/                    # Application installation
├── venv/                       # Python virtual environment
├── www/                        # Web interface files
├── db_manager.py              # Database abstraction layer
├── config.py                  # Configuration management
├── dashboard_server.py        # Flask application
├── youtube_strategies.py      # YouTube extraction module
└── ...

/etc/falcon/                    # Configuration (root:falcon, 750)
├── config.conf                # General configuration (644)
└── secrets.env                # API keys & secrets (640, root:falcon)

/var/lib/falcon/                # Runtime data (falcon:falcon, 750)
├── paper_trading.db           # SQLite database (if using SQLite)
└── market_data/               # Downloaded market data

/var/cache/falcon/              # Cache data (falcon:falcon, 750)

/var/log/falcon/                # Application logs (falcon:falcon, 750)

/etc/systemd/system/
└── falcon-dashboard.service   # SystemD service file

/etc/nginx/
├── sites-available/falcon     # Nginx configuration
├── sites-enabled/falcon -> sites-available/falcon
└── ssl/
    ├── falcon.crt             # SSL certificate
    └── falcon.key             # SSL private key
```

## Service Account

The installer creates a dedicated system service account:

- **Username:** `falcon`
- **Group:** `falcon`
- **Home:** `/var/lib/falcon` (logical, not actual home directory)
- **Shell:** `/bin/false` (no login)
- **Type:** System account (`-r` flag, UID < 1000)

This follows security best practices for service accounts:
- No interactive login
- No home directory clutter
- Minimal privileges
- Dedicated ownership of data/config

## Detailed Installation Steps

### Step 1: Pre-Installation Check

```bash
make
```

This will:
- ✓ Check for Python 3, pip, systemd
- ✓ Warn if nginx or rsync is missing (will auto-install nginx)
- ✓ Display next steps

### Step 2: Full Installation

```bash
sudo make install
```

This performs:

1. **Nginx Installation** (if needed)
   - Installs nginx via apt
   - Verifies installation

2. **Service Account Creation**
   - Creates `falcon` system user with no login
   - Sets home to `/var/lib/falcon` (for systemd compatibility)

3. **FHS Directory Structure**
   - Creates `/opt/falcon`, `/etc/falcon`, `/var/lib/falcon`, `/var/cache/falcon`, `/var/log/falcon`
   - Copies application files to `/opt/falcon`
   - Sets proper ownership and permissions

4. **Python Virtual Environment**
   - Creates venv at `/opt/falcon/venv`
   - Installs all Python dependencies
   - Upgrades pip, setuptools, wheel

5. **Configuration Files**
   - Creates `/etc/falcon/config.conf` (general settings)
   - Creates `/etc/falcon/secrets.env` (API keys, mode 640)
   - Sets proper permissions (root:falcon)

6. **Database Initialization**
   - Initializes SQLite database (default) or prepares for PostgreSQL
   - Creates tables for trading, strategies
   - Sets proper permissions

7. **SSL Certificate Generation**
   - Creates self-signed certificate (365 days)
   - Stored in `/etc/nginx/ssl/`
   - Configures for HTTPS

8. **Nginx Configuration**
   - Creates `/etc/nginx/sites-available/falcon`
   - Enables the site
   - Configures reverse proxy to Flask
   - Sets up HTTPS redirect
   - Tests configuration

9. **SystemD Service Setup**
   - Creates `/etc/systemd/system/falcon-dashboard.service`
   - Configures auto-restart with security hardening
   - Loads configuration from `/etc/falcon/`
   - Sets up logging to journald
   - Reloads systemd

### Step 3: Configuration

#### API Keys Setup

Edit the secrets file:

```bash
sudo nano /etc/falcon/secrets.env
```

Configure your API keys:

```bash
# Required for paper trading
MASSIVE_API_KEY=your_polygon_api_key_here

# Required for AI features
CLAUDE_API_KEY=your_claude_api_key_here

# Optional for additional AI agents
OPENAI_API_KEY=your_openai_key_here
PERPLEXITY_API_KEY=your_perplexity_key_here

# Optional: Custom Finviz screener
FINVIZ_SCREENER_URL=https://finviz.com/screener.ashx?v=...
```

#### Database Configuration (SQLite vs PostgreSQL)

**Default: SQLite** (no additional configuration needed)

The default configuration uses SQLite stored at `/var/lib/falcon/paper_trading.db`.

**Optional: PostgreSQL**

To use PostgreSQL instead:

1. Install PostgreSQL:
```bash
sudo apt-get install postgresql postgresql-client
```

2. Install Python PostgreSQL driver:
```bash
/opt/falcon/venv/bin/pip3 install -r /opt/falcon/requirements-postgresql.txt
```

3. Create database and user:
```bash
sudo -u postgres psql
CREATE USER falcon WITH PASSWORD 'your_secure_password';
CREATE DATABASE falcon OWNER falcon;
GRANT ALL PRIVILEGES ON DATABASE falcon TO falcon;
\q
```

4. Edit configuration:
```bash
sudo nano /etc/falcon/config.conf
```

Uncomment and configure PostgreSQL settings:
```bash
# Database
DB_TYPE=postgresql
DB_HOST=localhost
DB_PORT=5432
DB_NAME=falcon
DB_USER=falcon
```

5. Add PostgreSQL password to secrets:
```bash
sudo nano /etc/falcon/secrets.env
```

Add:
```bash
DB_PASSWORD=your_secure_password
```

6. Initialize database:
```bash
cd /opt/falcon
sudo -u falcon FALCON_ENV=production ./venv/bin/python3 db_manager.py
```

### Step 4: Start Services

```bash
sudo make start
```

This will:
- Enable falcon-dashboard service (auto-start on boot)
- Start falcon-dashboard
- Restart nginx
- Display status

### Step 5: Verify Installation

```bash
# Check service status
sudo make status

# View detailed logs
sudo journalctl -u falcon-dashboard -f

# Test nginx
sudo nginx -t

# Validate configuration
sudo make validate
```

### Step 6: Access the Application

- **HTTPS (recommended):** https://localhost/ or https://your-ip/
- **HTTP:** Automatically redirects to HTTPS

#### Available Endpoints:
- `/` - Main dashboard landing page
- `/strategies.html` - YouTube strategy collection
- `/dashboard` - Trading dashboard
- `/api/recommendations` - AI stock recommendations
- `/api/youtube-strategies` - YouTube strategies API
- `/health` - Health check endpoint

## Makefile Commands

### Build Commands

```bash
make              # Check dependencies and prepare
make clean        # Clean Python cache files
make help         # Show all available commands
```

### Installation Commands (require root)

```bash
sudo make install    # Full FHS-compliant installation
sudo make uninstall  # Remove installation (preserves data)
```

### Service Management (require root)

```bash
sudo make start      # Start all services
sudo make stop       # Stop all services
sudo make restart    # Restart all services
sudo make status     # Check service status
sudo make validate   # Validate configuration
```

## Configuration Files

### /etc/falcon/config.conf

General application configuration:

```bash
# Environment
FALCON_ENV=production

# Database
DB_TYPE=sqlite
DB_PATH=/var/lib/falcon/paper_trading.db

# Flask server
FLASK_HOST=127.0.0.1
FLASK_PORT=5000
FLASK_DEBUG=false
```

### /etc/falcon/secrets.env

Sensitive credentials (mode 640, root:falcon):

```bash
MASSIVE_API_KEY=...
CLAUDE_API_KEY=...
OPENAI_API_KEY=...
PERPLEXITY_API_KEY=...
DB_PASSWORD=...  # If using PostgreSQL
```

## Troubleshooting

### Service Won't Start

```bash
# Check service status
sudo systemctl status falcon-dashboard

# View detailed logs
sudo journalctl -u falcon-dashboard -n 50 --no-pager

# Common issues:
# 1. Missing API keys in /etc/falcon/secrets.env
# 2. Python dependencies not installed
# 3. Database permissions
# 4. Port 5000 already in use

# Check if port is in use
sudo netstat -tlnp | grep :5000

# Fix database permissions
sudo chown -R falcon:falcon /var/lib/falcon
```

### Nginx Configuration Errors

```bash
# Test nginx configuration
sudo nginx -t

# View nginx error log
sudo tail -f /var/log/nginx/falcon_error.log

# Restart nginx
sudo systemctl restart nginx
```

### SSL Certificate Issues

```bash
# Regenerate SSL certificate
sudo rm /etc/nginx/ssl/falcon.*
sudo make setup-ssl
sudo systemctl restart nginx
```

### Database Issues

#### SQLite

```bash
# Check database file
ls -l /var/lib/falcon/paper_trading.db

# Reset database (WARNING: deletes all data)
sudo -u falcon rm /var/lib/falcon/paper_trading.db
cd /opt/falcon
sudo -u falcon FALCON_ENV=production ./venv/bin/python3 db_manager.py
```

#### PostgreSQL

```bash
# Test connection
sudo -u falcon psql -h localhost -U falcon -d falcon

# Reset database (WARNING: deletes all data)
sudo -u postgres psql -c "DROP DATABASE falcon; CREATE DATABASE falcon OWNER falcon;"
cd /opt/falcon
sudo -u falcon FALCON_ENV=production ./venv/bin/python3 db_manager.py --reset --type=postgresql
```

### Permission Issues

```bash
# Fix application ownership
sudo chown -R falcon:falcon /opt/falcon /var/lib/falcon /var/cache/falcon /var/log/falcon

# Fix config permissions
sudo chown root:falcon /etc/falcon/secrets.env
sudo chmod 640 /etc/falcon/secrets.env
sudo chmod 644 /etc/falcon/config.conf

# Fix web directory permissions
sudo chmod -R 755 /opt/falcon/www
```

### Configuration Validation

```bash
# Validate configuration
cd /opt/falcon
sudo -u falcon FALCON_ENV=production ./venv/bin/python3 config.py --validate
```

## Upgrading

To upgrade to a new version:

```bash
# 1. Stop services
sudo make stop

# 2. Backup data
sudo tar -czf /tmp/falcon-backup-$(date +%Y%m%d).tar.gz \
    /var/lib/falcon \
    /etc/falcon

# 3. Pull updates (in source directory)
cd /home/ospartners/src/falcon
git pull origin main

# 4. Reinstall (preserves config and data)
sudo make install

# 5. Restart services
sudo make restart
```

## Migration from Development Setup

If you have an existing development installation (using ospartners user), see [MIGRATION.md](MIGRATION.md) for migration instructions.

## Uninstallation

```bash
# Stop and remove services
sudo make uninstall

# This removes:
# - SystemD service file
# - Nginx configuration
# - Service symlinks

# This preserves:
# - Application files (/opt/falcon)
# - Configuration (/etc/falcon)
# - Database and data (/var/lib/falcon)
# - Logs (/var/log/falcon)
# - Service user account

# To completely remove (WARNING: deletes all data):
sudo rm -rf /opt/falcon /etc/falcon /var/lib/falcon /var/cache/falcon /var/log/falcon
sudo userdel falcon
```

## Security Considerations

### SSL/TLS

The installer creates a **self-signed** SSL certificate. For production:

1. Obtain a proper certificate (Let's Encrypt recommended):
```bash
sudo apt-get install certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com
```

2. Or replace manually:
```bash
sudo cp your-cert.crt /etc/nginx/ssl/falcon.crt
sudo cp your-key.key /etc/nginx/ssl/falcon.key
sudo systemctl restart nginx
```

### Firewall

If using a firewall:

```bash
sudo ufw allow 80/tcp    # HTTP (redirects to HTTPS)
sudo ufw allow 443/tcp   # HTTPS
```

### Secrets Management

- Secrets are stored in `/etc/falcon/secrets.env` (mode 640, root:falcon)
- Only root and falcon user can read secrets
- Never commit secrets to git
- Use environment variables for all sensitive data

### Service Hardening

The systemd service includes security hardening:
- `NoNewPrivileges=true` - Prevents privilege escalation
- `PrivateTmp=true` - Private /tmp directory
- `ProtectSystem=strict` - Read-only filesystem except specific paths
- `ProtectHome=read-only` - Read-only home directories
- Minimal read/write paths (only /var/lib/falcon, /var/cache/falcon, /var/log/falcon)

### Database Security

**SQLite:**
- Database file owned by falcon:falcon
- Mode 640 (read/write for falcon, no access for others)

**PostgreSQL:**
- Use strong password
- Restrict network access (pg_hba.conf)
- Use SSL connections for remote access
- Regular backups

## Getting Help

- **Documentation:** See README.md, CLAUDE.md, YOUTUBE_STRATEGIES_GUIDE.md
- **Logs:** `journalctl -u falcon-dashboard -f`
- **Status:** `sudo make status`
- **Validation:** `sudo make validate`
- **GitHub Issues:** https://github.com/davdunc/falcon/issues

## Advanced Topics

### Custom Installation Directory

```bash
# Install to custom location
sudo make install PREFIX=/usr/local/falcon

# Note: Still uses /etc/falcon for config, /var/lib/falcon for data
```

### PostgreSQL Remote Database

Edit `/etc/falcon/config.conf`:

```bash
DB_TYPE=postgresql
DB_HOST=dbserver.example.com
DB_PORT=5432
DB_NAME=falcon
DB_USER=falcon
```

Add password to `/etc/falcon/secrets.env`:

```bash
DB_PASSWORD=your_password
```

### Multiple Instances

Not officially supported, but possible with:
- Different PREFIX for each instance
- Different Flask ports
- Different nginx server blocks
- Different systemd service names
- Different databases

---

**Installation complete!** Access your Falcon Trading Platform at https://localhost/

For production deployment, remember to:
1. Configure proper SSL certificates
2. Set strong PostgreSQL passwords (if using PostgreSQL)
3. Configure firewall rules
4. Set up regular backups
5. Monitor logs regularly
