# Falcon Trading System - Services Guide

## Overview

The Falcon Trading System consists of two systemd services that can run automatically:

1. **falcon-orchestrator** - Automated trading engine
2. **falcon-dashboard** - Web interface and REST API

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│                    Systemd Services                         │
└────────────────────────────────────────────────────────────┘

┌──────────────────────────┐    ┌──────────────────────────┐
│  falcon-orchestrator     │    │   falcon-dashboard       │
│  (Trading Engine)        │    │   (Web Interface)        │
│                          │    │                          │
│  - Paper Trading Bot     │    │  - REST API              │
│  - Strategy Executor     │    │  - Web Dashboard         │
│  - Strategy Optimizer    │    │  - Strategy Management   │
│  - Strategy Analytics    │    │  - Performance Charts    │
└──────────────────────────┘    └──────────────────────────┘
            │                                  │
            └──────────────┬───────────────────┘
                           │
                ┌──────────▼──────────┐
                │   Database          │
                │   /var/lib/falcon/  │
                │   paper_trading.db  │
                └─────────────────────┘
```

## Installation

### Quick Install (Both Services)

```bash
cd /home/ospartners/src/falcon
sudo ./install_services.sh
```

### Install Orchestrator Only

```bash
sudo ./install_services.sh --orchestrator-only
```

### Install Dashboard Only

```bash
sudo ./install_services.sh --dashboard-only
```

## Configuration

After installation, edit `/opt/falcon/.env`:

```bash
sudo nano /opt/falcon/.env
```

Required configuration:

```bash
# Polygon.io API Key (required)
MASSIVE_API_KEY=your_polygon_api_key_here

# Claude API Key (required for AI features)
CLAUDE_API_KEY=your_claude_api_key_here

# Trading Configuration (optional)
TRADING_SYMBOLS=SPY,QQQ,AAPL
INITIAL_BALANCE=10000
UPDATE_INTERVAL=60
```

## Service Management

### Orchestrator (Trading Engine)

Start the automated trading engine:

```bash
# Start service
sudo systemctl start falcon-orchestrator

# Stop service
sudo systemctl stop falcon-orchestrator

# Restart service
sudo systemctl restart falcon-orchestrator

# Check status
sudo systemctl status falcon-orchestrator

# View logs (live)
sudo journalctl -u falcon-orchestrator -f

# View logs (last 100 lines)
sudo journalctl -u falcon-orchestrator -n 100

# Enable auto-start on boot
sudo systemctl enable falcon-orchestrator

# Disable auto-start
sudo systemctl disable falcon-orchestrator
```

### Dashboard (Web Interface)

Start the web dashboard:

```bash
# Start service
sudo systemctl start falcon-dashboard

# Stop service
sudo systemctl stop falcon-dashboard

# Restart service
sudo systemctl restart falcon-dashboard

# Check status
sudo systemctl status falcon-dashboard

# View logs (live)
sudo journalctl -u falcon-dashboard -f

# Enable auto-start on boot
sudo systemctl enable falcon-dashboard
```

## Typical Workflow

### 1. Initial Setup

```bash
# Install services
sudo ./install_services.sh

# Edit configuration
sudo nano /opt/falcon/.env
# Add your API keys

# Start dashboard first
sudo systemctl start falcon-dashboard

# Verify dashboard is running
curl http://localhost:5000/health
```

### 2. Add Trading Strategies

```bash
# Via API (dashboard must be running)
curl -X POST http://localhost:5000/api/strategies/youtube/1/activate \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["SPY", "QQQ"],
    "allocation_pct": 25.0
  }'
```

### 3. Start Automated Trading

```bash
# Start orchestrator
sudo systemctl start falcon-orchestrator

# Watch it work
sudo journalctl -u falcon-orchestrator -f
```

### 4. Monitor Performance

```bash
# View active strategies
curl http://localhost:5000/api/strategies/active

# View strategy leaderboard
curl http://localhost:5000/api/strategies/leaderboard

# View aggregate statistics
curl http://localhost:5000/api/strategies/aggregate
```

## Service Details

### falcon-orchestrator.service

**Purpose:** Automated trading engine that runs strategies in parallel

**What it does:**
- Loads active strategies from database
- Fetches market data every 60 seconds (configurable)
- Evaluates strategy signals
- Executes trades with performance-weighted allocation
- Monitors performance and triggers AI optimization
- Runs 24/7 without manual intervention

**User:** falcon
**Working Directory:** /opt/falcon
**Database:** /var/lib/falcon/paper_trading.db
**Logging:** journalctl (systemd journal)

**Resource Limits:**
- Memory: 1GB max
- CPU: 50% max

### falcon-dashboard.service

**Purpose:** Web interface and REST API for management

**What it does:**
- Provides REST API for strategy management
- Serves web dashboard on port 5000
- Allows activating/pausing strategies
- Shows performance metrics and charts
- Enables YouTube strategy extraction

**User:** falcon
**Working Directory:** /opt/falcon
**Port:** 5000 (HTTP)
**Logging:** journalctl (systemd journal)

**Resource Limits:**
- Memory: 512MB max
- CPU: 25% max

## Auto-Start on Boot

To have services start automatically when the system boots:

```bash
# Enable orchestrator
sudo systemctl enable falcon-orchestrator

# Enable dashboard
sudo systemctl enable falcon-dashboard

# Check enabled status
systemctl is-enabled falcon-orchestrator
systemctl is-enabled falcon-dashboard
```

To disable auto-start:

```bash
sudo systemctl disable falcon-orchestrator
sudo systemctl disable falcon-dashboard
```

## Troubleshooting

### Service Won't Start

Check the status and logs:

```bash
sudo systemctl status falcon-orchestrator
sudo journalctl -u falcon-orchestrator -n 50
```

Common issues:

**1. API Keys Not Set**
```
ERROR: MASSIVE_API_KEY not set
```
Solution: Edit `/opt/falcon/.env` and add API keys

**2. Permission Denied**
```
OperationalError: unable to open database file
```
Solution: Check database ownership
```bash
sudo chown -R falcon:falcon /var/lib/falcon
```

**3. Module Not Found**
```
ModuleNotFoundError: No module named 'anthropic'
```
Solution: Install missing dependencies
```bash
sudo pip3 install anthropic --break-system-packages
```

**4. Port Already in Use** (dashboard)
```
OSError: [Errno 98] Address already in use
```
Solution: Check what's using port 5000
```bash
sudo lsof -i :5000
# Kill the process or change dashboard port
```

### View Service Status

Check if services are running:

```bash
# Quick status
systemctl is-active falcon-orchestrator
systemctl is-active falcon-dashboard

# Detailed status
sudo systemctl status falcon-orchestrator
sudo systemctl status falcon-dashboard

# List all falcon services
systemctl list-units falcon-*
```

### Restart After Configuration Change

After editing `/opt/falcon/.env`:

```bash
# Restart orchestrator
sudo systemctl restart falcon-orchestrator

# Restart dashboard
sudo systemctl restart falcon-dashboard
```

### Check Resource Usage

Monitor service resource consumption:

```bash
# CPU and memory usage
systemctl status falcon-orchestrator
systemctl status falcon-dashboard

# Or use top
top -p $(pgrep -f strategy_orchestrator)
```

## File Locations

| Path | Purpose |
|------|---------|
| `/opt/falcon/` | Application files |
| `/opt/falcon/.env` | Configuration (API keys) |
| `/var/lib/falcon/` | Database and data files |
| `/var/lib/falcon/paper_trading.db` | Main database |
| `/etc/systemd/system/falcon-*.service` | Service definitions |
| `/etc/falcon/` | Additional configuration |

## Security

Services run as the `falcon` user with restricted permissions:

- **No root access:** Services don't run as root
- **Protected home:** Cannot access user home directories
- **Protected system:** Read-only access to system files
- **Private temp:** Each service has isolated /tmp
- **Limited resources:** CPU and memory limits enforced

## Monitoring

### Check if Orchestrator is Working

```bash
# View recent log entries
sudo journalctl -u falcon-orchestrator -n 50

# Look for these messages:
# [ORCHESTRATOR] System running
# [EXECUTOR] Loaded strategy X
# [EXECUTOR] Signal: BUY/SELL ...
```

### Check Strategy Performance

```bash
# Via API
curl http://localhost:5000/api/strategies/active

# Via database
sudo -u falcon python3 <<EOF
import sqlite3
conn = sqlite3.connect('/var/lib/falcon/paper_trading.db')
cursor = conn.cursor()
cursor.execute('SELECT id, strategy_name, status FROM active_strategies')
for row in cursor.fetchall():
    print(f"Strategy {row[0]}: {row[1]} ({row[2]})")
conn.close()
EOF
```

## Uninstallation

To remove services:

```bash
# Stop services
sudo systemctl stop falcon-orchestrator
sudo systemctl stop falcon-dashboard

# Disable auto-start
sudo systemctl disable falcon-orchestrator
sudo systemctl disable falcon-dashboard

# Remove service files
sudo rm /etc/systemd/system/falcon-orchestrator.service
sudo rm /etc/systemd/system/falcon-dashboard.service

# Reload systemd
sudo systemctl daemon-reload

# Optional: Remove application files
# sudo rm -rf /opt/falcon
# sudo rm -rf /var/lib/falcon

# Optional: Remove user
# sudo userdel falcon
```

## Service Logs

Services log to systemd journal. View logs:

```bash
# Live logs (tail -f style)
sudo journalctl -u falcon-orchestrator -f

# Last N lines
sudo journalctl -u falcon-orchestrator -n 100

# Since specific time
sudo journalctl -u falcon-orchestrator --since "1 hour ago"

# Follow both services
sudo journalctl -u falcon-orchestrator -u falcon-dashboard -f

# Export logs to file
sudo journalctl -u falcon-orchestrator > orchestrator.log
```

## Production Recommendations

For production deployment:

1. **Enable auto-start:**
   ```bash
   sudo systemctl enable falcon-orchestrator
   sudo systemctl enable falcon-dashboard
   ```

2. **Set up log rotation** (systemd does this automatically)

3. **Monitor with alerting:**
   - Set up monitoring for service status
   - Alert if service stops unexpectedly
   - Monitor database size growth

4. **Backup database regularly:**
   ```bash
   # Create backup
   sudo -u falcon cp /var/lib/falcon/paper_trading.db \
                     /var/lib/falcon/paper_trading.db.backup
   ```

5. **Test failover:**
   - Kill process and verify automatic restart
   - Reboot system and verify services start

6. **Security hardening:**
   - Keep API keys in `/opt/falcon/.env` with 600 permissions
   - Use firewall to restrict dashboard access
   - Consider SSL/TLS for dashboard (nginx reverse proxy)

## Performance Tuning

Adjust resource limits by editing service files:

```bash
sudo nano /etc/systemd/system/falcon-orchestrator.service
```

Change limits:

```ini
# Increase memory limit
MemoryMax=2G

# Increase CPU quota
CPUQuota=100%
```

Then reload:

```bash
sudo systemctl daemon-reload
sudo systemctl restart falcon-orchestrator
```

## Support

For issues:

1. Check service status: `systemctl status falcon-orchestrator`
2. Check logs: `journalctl -u falcon-orchestrator -f`
3. Verify configuration: `cat /opt/falcon/.env`
4. Test database: `sudo -u falcon python3 /opt/falcon/init_strategy_tables.py`
5. See: `STRATEGY_EXECUTION_GUIDE.md` for system documentation

---

**Remember:** Always test configuration changes in development before production deployment!
