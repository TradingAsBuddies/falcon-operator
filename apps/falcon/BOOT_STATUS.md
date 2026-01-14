# Falcon Trading System - Auto-Start Configuration

## Status: ✅ CONFIGURED

Both Falcon services are now enabled to start automatically on system boot.

## Enabled Services

### 1. falcon-orchestrator.service
- **Status:** ✅ Enabled
- **Current State:** Running
- **Purpose:** Automated trading engine
- **Components:**
  - Paper Trading Bot
  - Strategy Executor
  - Strategy Optimizer
  - Strategy Analytics

### 2. falcon-dashboard.service
- **Status:** ✅ Enabled
- **Current State:** Running
- **Purpose:** Web interface and REST API
- **URL:** http://localhost:5000

## Verification

Services are enabled and will start on boot:

```bash
$ systemctl is-enabled falcon-orchestrator
enabled

$ systemctl is-enabled falcon-dashboard
enabled
```

Current running status:

```bash
$ systemctl is-active falcon-orchestrator
active

$ systemctl is-active falcon-dashboard
active
```

## What Happens on Boot

1. **System starts**
2. **Network comes online**
3. **falcon-orchestrator starts automatically**
   - Loads strategies from database
   - Connects to Polygon.io for market data
   - Begins evaluating strategies every 60 seconds
   - Executes trades when conditions are met
4. **falcon-dashboard starts automatically**
   - Web interface available at http://localhost:5000
   - REST API endpoints ready
   - Strategy management interface active

## Commands Reference

### View Status
```bash
# Quick check
systemctl is-enabled falcon-orchestrator
systemctl is-active falcon-orchestrator

# Detailed status
sudo systemctl status falcon-orchestrator
sudo systemctl status falcon-dashboard
```

### View Logs
```bash
# Live logs (tail -f style)
sudo journalctl -u falcon-orchestrator -f
sudo journalctl -u falcon-dashboard -f

# Both services at once
sudo journalctl -u falcon-orchestrator -u falcon-dashboard -f
```

### Restart Services
```bash
# After configuration changes
sudo systemctl restart falcon-orchestrator
sudo systemctl restart falcon-dashboard
```

### Disable Auto-Start
```bash
# If you want to disable auto-start
sudo systemctl disable falcon-orchestrator
sudo systemctl disable falcon-dashboard
```

## Active Strategy

Currently running strategy:
- **ID:** 1
- **Name:** Test RSI Mean Reversion
- **Symbols:** SPY
- **Status:** Active
- **Allocation:** 100%

The orchestrator is evaluating this strategy every 60 seconds and will execute trades when RSI conditions are met.

## Configuration

All configuration is in `/opt/falcon/.env`:
- API keys (Polygon.io, Claude)
- Trading symbols
- Initial balance
- Update interval

To modify configuration:
```bash
sudo nano /opt/falcon/.env
sudo systemctl restart falcon-orchestrator
```

## Test Boot Behavior

To verify services start on boot:

```bash
# Reboot the system
sudo reboot

# After reboot, check services started automatically
systemctl status falcon-orchestrator
systemctl status falcon-dashboard

# View startup logs
sudo journalctl -u falcon-orchestrator -b
```

## Resource Usage

Services have resource limits configured:

**Orchestrator:**
- Memory: 1GB max
- CPU: 50% max

**Dashboard:**
- Memory: 512MB max
- CPU: 25% max

## Security

Services run with these security features:
- ✅ Non-root user (`falcon`)
- ✅ Protected system directories
- ✅ Protected home directories
- ✅ Private /tmp
- ✅ No new privileges
- ✅ Resource limits enforced

## Monitoring

### Check if Trading is Active
```bash
# View recent orchestrator activity
sudo journalctl -u falcon-orchestrator -n 50

# Look for:
[EXECUTOR] Signal: BUY/SELL ...
[EXECUTOR] BUY executed: ...
```

### Check Performance
```bash
# Query database for strategy performance
sudo -u falcon python3 <<EOF
import sqlite3
conn = sqlite3.connect('/var/lib/falcon/paper_trading.db')
cursor = conn.cursor()
cursor.execute('SELECT id, strategy_name, status FROM active_strategies WHERE status="active"')
print("Active Strategies:")
for row in cursor.fetchall():
    print(f"  {row[0]}: {row[1]} ({row[2]})")
conn.close()
EOF
```

## Troubleshooting

### Service Won't Start
```bash
# Check logs for errors
sudo journalctl -u falcon-orchestrator -n 100

# Common issues:
# - API keys not set in /opt/falcon/.env
# - Database permissions issue
# - Missing Python dependencies
```

### Service Crashes
```bash
# Check systemd will auto-restart
systemctl show falcon-orchestrator | grep Restart=

# View crash logs
sudo journalctl -u falcon-orchestrator --since "1 hour ago"
```

## Next Steps

The system is now fully automated:

1. ✅ Services start on boot
2. ✅ Orchestrator evaluating strategies
3. ✅ Dashboard accessible for management
4. ✅ Auto-restart on failure configured

**No manual intervention required** - the system will:
- Start automatically on every boot
- Trade automatically when conditions are met
- Optimize strategies automatically when performance drops
- Restart automatically if it crashes

## Files and Locations

| Item | Path |
|------|------|
| Service Definitions | `/etc/systemd/system/falcon-*.service` |
| Application Code | `/opt/falcon/*.py` |
| Configuration | `/opt/falcon/.env` |
| Database | `/var/lib/falcon/paper_trading.db` |
| Logs | `journalctl -u falcon-*` |

---

**System Status:** Fully operational and configured for automatic operation on boot.

Last Updated: 2026-01-07
