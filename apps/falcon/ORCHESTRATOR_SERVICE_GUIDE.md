# Falcon Orchestrator Systemd Service Guide

## Overview

The Falcon Multi-Strategy Orchestrator now runs as a systemd service, providing:
- **Automatic startup** on system boot
- **Automatic restart** if the process crashes
- **Centralized logging** via systemd journal
- **Resource limits** to prevent runaway processes
- **Professional service management** with systemctl commands

---

## Service Details

| Property | Value |
|----------|-------|
| **Service Name** | `falcon-orchestrator-daemon.service` |
| **Service File** | `/etc/systemd/system/falcon-orchestrator-daemon.service` |
| **Working Directory** | `/home/ospartners/src/falcon` |
| **User** | `ospartners` |
| **Python** | `/home/ospartners/src/falcon/backtest/bin/python3` |
| **Script** | `/home/ospartners/src/falcon/run_orchestrator.py` |
| **Environment** | `/home/ospartners/.local/.env` |

---

## Service Management Commands

### Using systemctl (Standard Way)

```bash
# Start the service
sudo systemctl start falcon-orchestrator-daemon.service

# Stop the service
sudo systemctl stop falcon-orchestrator-daemon.service

# Restart the service
sudo systemctl restart falcon-orchestrator-daemon.service

# Check service status
sudo systemctl status falcon-orchestrator-daemon.service

# Enable service (start on boot)
sudo systemctl enable falcon-orchestrator-daemon.service

# Disable service (don't start on boot)
sudo systemctl disable falcon-orchestrator-daemon.service

# View logs
sudo journalctl -u falcon-orchestrator-daemon.service -n 50

# Follow logs in real-time
sudo journalctl -u falcon-orchestrator-daemon.service -f
```

### Using Helper Script (Easy Way)

```bash
# Start the service
./orchestrator-service-helper.sh start

# Stop the service
./orchestrator-service-helper.sh stop

# Restart the service
./orchestrator-service-helper.sh restart

# Check status
./orchestrator-service-helper.sh status

# View logs (last 50 lines)
./orchestrator-service-helper.sh logs

# View logs (last 100 lines)
./orchestrator-service-helper.sh logs 100

# Follow logs in real-time
./orchestrator-service-helper.sh follow

# Show service info
./orchestrator-service-helper.sh info

# Enable/disable service
./orchestrator-service-helper.sh enable
./orchestrator-service-helper.sh disable
```

---

## What the Service Does

The orchestrator runs continuously with 5-minute cycles:

### Each Cycle:
1. **Process AI Screener Results** - Reads `screened_stocks.json` for new recommendations
2. **Validate Entries** - Checks prices against AI recommended ranges
3. **Route to Strategies** - Assigns stocks to optimal strategies (RSI, Momentum, Bollinger)
4. **Generate Signals** - Each engine analyzes market conditions
5. **Execute Trades** - Places orders when signals are strong
6. **Monitor Positions** - Checks all open positions for exit signals
7. **Track Performance** - Logs routing decisions and trade outcomes

### Every 10 Cycles (50 minutes):
- Shows full account status
- Displays performance summary

---

## Service Features

### Automatic Restart
If the orchestrator crashes or encounters an error, systemd will automatically restart it after 30 seconds.

### Resource Limits
- **Memory**: Maximum 1GB
- **CPU**: Maximum 50% of one core
- **Tasks**: Maximum 100 concurrent tasks

### Security Hardening
- No new privileges allowed
- Protected system directories
- Home directory read-only (except working directory)
- Private temporary directory
- Kernel tunables protected

### Logging
All output goes to the systemd journal, viewable with:
```bash
sudo journalctl -u falcon-orchestrator-daemon.service
```

---

## Monitoring the Service

### Check if Service is Running
```bash
systemctl is-active falcon-orchestrator-daemon.service
# Output: active or inactive
```

### Check if Service is Enabled
```bash
systemctl is-enabled falcon-orchestrator-daemon.service
# Output: enabled or disabled
```

### View Real-Time Logs
```bash
sudo journalctl -u falcon-orchestrator-daemon.service -f
```

### View Recent Activity
```bash
./orchestrator-service-helper.sh logs 100
```

### Check Current Positions
```bash
python3 run_orchestrator.py --status
```

---

## Troubleshooting

### Service Won't Start

1. Check the logs:
   ```bash
   sudo journalctl -u falcon-orchestrator-daemon.service -n 100
   ```

2. Verify Python environment:
   ```bash
   /home/ospartners/src/falcon/backtest/bin/python3 --version
   ```

3. Test the script manually:
   ```bash
   cd /home/ospartners/src/falcon
   ./backtest/bin/python3 run_orchestrator.py --once
   ```

### Service Keeps Restarting

1. View logs for error messages:
   ```bash
   sudo journalctl -u falcon-orchestrator-daemon.service -f
   ```

2. Check for database issues:
   ```bash
   ls -lh paper_trading.db
   ```

3. Verify environment variables:
   ```bash
   cat /home/ospartners/.local/.env | grep API_KEY
   ```

### Service Not Executing Trades

1. Check AI screener is running:
   ```bash
   sudo systemctl status falcon-screener.service
   ```

2. Verify screened stocks file:
   ```bash
   ls -lh screened_stocks.json
   tail -100 screened_stocks.json
   ```

3. View orchestrator logs for rejection reasons:
   ```bash
   ./orchestrator-service-helper.sh logs | grep SKIP
   ```

---

## Integration with Other Services

The orchestrator works alongside other Falcon services:

| Service | Purpose | Dependency |
|---------|---------|------------|
| `falcon-screener.service` | AI stock screening | Provides input data |
| `falcon-dashboard.service` | Web interface | Displays orchestrator results |
| `falcon-orchestrator.service` | Old orchestrator | Can run alongside (different strategies) |

**Note**: The new orchestrator daemon (`falcon-orchestrator-daemon.service`) is independent and can run alongside the old orchestrator service.

---

## Performance Monitoring

### View Performance Summary
```bash
python3 run_orchestrator.py --performance 7
```

### View Account Status
```bash
python3 run_orchestrator.py --status
```

### Check Strategy Metrics
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('paper_trading.db')
cursor = conn.cursor()
cursor.execute('SELECT * FROM strategy_metrics ORDER BY period_end DESC LIMIT 5')
for row in cursor.fetchall():
    print(row)
"
```

---

## Maintenance

### Update Service Configuration

1. Edit the service file:
   ```bash
   sudo nano /etc/systemd/system/falcon-orchestrator-daemon.service
   ```

2. Reload systemd:
   ```bash
   sudo systemctl daemon-reload
   ```

3. Restart service:
   ```bash
   sudo systemctl restart falcon-orchestrator-daemon.service
   ```

### Rotate Logs

Systemd automatically rotates logs, but you can manually clean old logs:
```bash
sudo journalctl --vacuum-time=7d  # Keep last 7 days
sudo journalctl --vacuum-size=100M  # Keep last 100MB
```

### Backup Database

```bash
# Stop service
sudo systemctl stop falcon-orchestrator-daemon.service

# Backup database
cp paper_trading.db paper_trading.db.backup.$(date +%Y%m%d)

# Start service
sudo systemctl start falcon-orchestrator-daemon.service
```

---

## Uninstalling

To remove the service:

```bash
# Stop and disable the service
sudo systemctl stop falcon-orchestrator-daemon.service
sudo systemctl disable falcon-orchestrator-daemon.service

# Remove service file
sudo rm /etc/systemd/system/falcon-orchestrator-daemon.service

# Reload systemd
sudo systemctl daemon-reload
```

---

## Additional Resources

- **Orchestrator Documentation**: `ORCHESTRATOR_COMPLETE.md`
- **Performance Tracker**: `PERFORMANCE_TRACKER_IMPLEMENTATION.md`
- **Strategy Engines**: `STRATEGY_ENGINES_IMPLEMENTATION.md`
- **Trade Executor**: `TRADE_EXECUTOR_IMPLEMENTATION.md`

---

## Quick Reference Card

```
# Service Management
start    : sudo systemctl start falcon-orchestrator-daemon
stop     : sudo systemctl stop falcon-orchestrator-daemon
restart  : sudo systemctl restart falcon-orchestrator-daemon
status   : sudo systemctl status falcon-orchestrator-daemon

# Logs
view     : sudo journalctl -u falcon-orchestrator-daemon -n 50
follow   : sudo journalctl -u falcon-orchestrator-daemon -f

# Orchestrator Commands
status   : python3 run_orchestrator.py --status
monitor  : python3 run_orchestrator.py --monitor
process  : python3 run_orchestrator.py --process
perform  : python3 run_orchestrator.py --performance 7

# Helper Script
./orchestrator-service-helper.sh <command>
```
