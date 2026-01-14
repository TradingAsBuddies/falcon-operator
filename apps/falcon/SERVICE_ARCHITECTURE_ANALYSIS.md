# Falcon Service Architecture Analysis

**Date**: 2026-01-12
**Question**: Should ai_stock_screener be separated as a service?
**Answer**: ✅ **It already is!**

---

## Current Service Architecture

### Running Services

```bash
# Check all Falcon services
sudo systemctl list-units --type=service --state=running | grep falcon
```

| Service | Status | Purpose | PID |
|---------|--------|---------|-----|
| `falcon-screener.service` | ✅ Running (3 days) | AI stock screening | 39081 |
| `falcon-dashboard.service` | ✅ Running | Web interface/API | 131786 |
| `falcon-orchestrator.service` | ✅ Running | Strategy orchestrator | - |
| `falcon-orchestrator-daemon.service` | ✅ Running | Multi-strategy orchestrator | - |

---

## AI Stock Screener Service Details

### Service Configuration

**File**: `/etc/systemd/system/falcon-screener.service`

```ini
[Unit]
Description=Falcon AI Stock Screener
After=network.target

[Service]
Type=simple
User=ospartners
WorkingDirectory=/home/ospartners/src/falcon
EnvironmentFile=/home/ospartners/.local/.env
Environment="PYTHONUNBUFFERED=1"
Environment="PYTHONIOENCODING=utf-8"
Environment="LC_ALL=C.UTF-8"
ExecStart=/home/ospartners/src/falcon/backtest/bin/python3 /home/ospartners/src/falcon/ai_stock_screener.py
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
ProtectSystem=strict
ProtectHome=read-only
ReadWritePaths=/home/ospartners/src/falcon
PrivateTmp=true

[Install]
WantedBy=multi-user.target
```

### Current Status

```
✅ Active: active (running) since Jan 9, 2026
✅ Enabled: starts automatically on boot
✅ Auto-restart: RestartSec=10 (restarts 10s after crash)
✅ Security: NoNewPrivileges, ProtectSystem, ProtectHome
✅ Environment: Loads API keys from .env file
✅ Working: Last successful run today at 9:00 AM
```

### Recent Activity Log

```
Jan 12 04:00:38 - Morning screen complete: 5 recommendations
Jan 12 09:00:57 - Midday update complete: 5 recommendations
```

---

## Service Architecture Benefits

### ✅ Already Implemented

1. **Process Isolation**
   - Runs independently from dashboard
   - Can crash/restart without affecting web interface
   - Separate PID, memory space, and resources

2. **Automatic Management**
   - Starts on boot automatically
   - Auto-restarts on failure (10-second delay)
   - Managed by systemd (robust process supervisor)

3. **Security Hardening**
   - Runs as non-root user (ospartners)
   - Read-only filesystem access
   - Private /tmp directory
   - No new privileges escalation

4. **Resource Management**
   - Systemd tracks CPU/memory usage
   - Can set limits via systemd directives
   - Easy to monitor with `systemctl status`

5. **Logging**
   - Integrated with systemd journal
   - View logs: `journalctl -u falcon-screener -f`
   - Persistent logs across reboots

6. **Scheduled Execution**
   - Built-in scheduling in Python (4 AM, 9 AM-12 PM, 7 PM)
   - No need for cron jobs
   - Self-contained scheduling logic

---

## Communication Architecture

### How Services Communicate

```
┌─────────────────────────────────────────────────────┐
│              Falcon System Architecture              │
└─────────────────────────────────────────────────────┘

┌──────────────────────────┐
│  falcon-screener.service │  (PID 39081)
│  ai_stock_screener.py    │
│                          │
│  Schedule:               │
│  - 4:00 AM Morning       │
│  - 9:00-12:00 Hourly     │
│  - 7:00 PM Evening       │
└────────────┬─────────────┘
             │
             │ writes JSON
             ▼
   ┌─────────────────────┐
   │ screened_stocks.json│  (File-based IPC)
   └─────────┬───────────┘
             │
             │ reads JSON
             ▼
┌──────────────────────────┐
│ falcon-dashboard.service │  (PID 131786)
│  dashboard_server.py     │
│                          │
│  Endpoints:              │
│  - /api/recommendations  │
│  - /dashboard            │
│  - /strategies.html      │
└──────────────────────────┘
             │
             │ HTTP
             ▼
      ┌─────────────┐
      │   Browser   │
      │ 192.168.1.162│
      └─────────────┘
```

**Communication Method**: File-based (screened_stocks.json)

**Pros**:
- Simple and reliable
- No network overhead
- Easy to debug (can inspect JSON file)
- Decoupled services
- No complex IPC needed

**Cons**:
- File locking considerations (not an issue with read-only access)
- Not real-time (dashboard reads periodically)
- No bidirectional communication

---

## Is the Current Architecture Good?

### ✅ YES - It's Well Designed

**Strengths**:

1. **Separation of Concerns**
   - Screener focuses on AI analysis
   - Dashboard focuses on presentation
   - Each service has clear responsibility

2. **Fault Tolerance**
   - Screener crash doesn't affect dashboard
   - Dashboard crash doesn't affect screening
   - Independent restart policies

3. **Scalability**
   - Can move screener to different machine
   - Can run multiple screeners (different strategies)
   - Easy to add more services

4. **Maintainability**
   - Each service can be updated independently
   - Clear service boundaries
   - Easy to troubleshoot

5. **Performance**
   - No blocking - screener runs async
   - Dashboard responds immediately
   - Background processing doesn't slow UI

### ⚠️ Potential Improvements

While the current architecture is good, here are optional enhancements:

1. **Add Health Checks**
   - Monitor if screened_stocks.json is stale
   - Alert if screener hasn't run in X hours
   - Dashboard shows "last updated" timestamp

2. **Structured Logging**
   - Use JSON logs for better parsing
   - Centralized log aggregation
   - Metrics collection

3. **Service Dependencies**
   - Dashboard could declare dependency on screener
   - Systemd would manage startup order
   - Example: `After=falcon-screener.service`

4. **API-Based Communication** (Alternative)
   - Screener exposes REST API
   - Dashboard fetches via HTTP
   - More complex, but enables:
     - Real-time notifications
     - Bi-directional communication
     - Status queries
     - Remote deployment

---

## Recommendations

### Keep Current Architecture If:

✅ Single-user system (your case)
✅ File-based communication is sufficient
✅ No need for real-time updates
✅ Simple debugging is important
✅ Low complexity is a priority

### Consider API-Based If:

- Multiple users/clients
- Need real-time push notifications
- Want remote screener deployment
- Building microservices architecture
- Need service discovery

---

## Service Management Commands

### Check Status
```bash
# Screener status
sudo systemctl status falcon-screener

# View recent logs
journalctl -u falcon-screener -n 50

# Follow logs in real-time
journalctl -u falcon-screener -f

# Check resource usage
systemctl show falcon-screener | grep -E "CPU|Memory"
```

### Control Services
```bash
# Restart screener
sudo systemctl restart falcon-screener

# Stop screener
sudo systemctl stop falcon-screener

# Start screener
sudo systemctl start falcon-screener

# Disable auto-start on boot
sudo systemctl disable falcon-screener

# Enable auto-start on boot
sudo systemctl enable falcon-screener
```

### View All Falcon Services
```bash
# List all running
sudo systemctl list-units --type=service --state=running | grep falcon

# List all (including inactive)
sudo systemctl list-units --type=service | grep falcon

# Check if enabled on boot
systemctl is-enabled falcon-screener
```

---

## Monitoring & Health

### Check if Screener is Working

```bash
# 1. Is service running?
sudo systemctl is-active falcon-screener
# Should output: active

# 2. When was last successful run?
ls -lh screened_stocks.json
# Check timestamp

# 3. How many recommendations?
cat screened_stocks.json | python3 -m json.tool | grep -c '"ticker"'

# 4. Recent errors?
journalctl -u falcon-screener --since "1 hour ago" | grep -i error

# 5. CPU/Memory usage?
ps aux | grep ai_stock_screener
```

### Health Check Script

Create `/home/ospartners/src/falcon/check_screener_health.sh`:

```bash
#!/bin/bash
# Screener Health Check

echo "=== Falcon AI Screener Health Check ==="
echo ""

# Check if service is running
if systemctl is-active --quiet falcon-screener; then
    echo "✅ Service Status: RUNNING"
else
    echo "❌ Service Status: NOT RUNNING"
    exit 1
fi

# Check if JSON file exists and is recent
if [ -f screened_stocks.json ]; then
    AGE=$(( $(date +%s) - $(stat -c %Y screened_stocks.json) ))
    HOURS=$(( AGE / 3600 ))

    if [ $HOURS -lt 6 ]; then
        echo "✅ Data Freshness: ${HOURS} hours old (OK)"
    else
        echo "⚠️  Data Freshness: ${HOURS} hours old (STALE)"
    fi
else
    echo "❌ Data File: NOT FOUND"
fi

# Check recommendation count
COUNT=$(cat screened_stocks.json 2>/dev/null | python3 -c "import sys,json; print(len(json.load(sys.stdin).get('recommendations', [])))" 2>/dev/null)
if [ -n "$COUNT" ]; then
    echo "✅ Recommendations: ${COUNT} stocks"
else
    echo "❌ Recommendations: ERROR reading file"
fi

# Check recent errors
ERRORS=$(journalctl -u falcon-screener --since "1 hour ago" 2>/dev/null | grep -ci error)
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ Recent Errors: None"
else
    echo "⚠️  Recent Errors: ${ERRORS} in last hour"
fi

echo ""
echo "Service uptime:"
systemctl show falcon-screener --property=ActiveEnterTimestamp --value
```

---

## Optional: Convert to API-Based Architecture

If you decide you want API-based communication instead of file-based:

### Step 1: Add API Endpoints to Screener

```python
# In ai_stock_screener.py
from flask import Flask, jsonify
import threading

app = Flask(__name__)

@app.route('/api/recommendations')
def get_recommendations():
    """Return current recommendations"""
    return jsonify(load_recommendations())

@app.route('/api/status')
def get_status():
    """Return screener status"""
    return jsonify({
        "status": "running",
        "last_run": last_run_time,
        "next_run": next_run_time,
        "recommendation_count": len(recommendations)
    })

# Run Flask in separate thread
def run_api():
    app.run(host='0.0.0.0', port=5001)

threading.Thread(target=run_api, daemon=True).start()
```

### Step 2: Update Dashboard to Use API

```python
# In dashboard_server.py
@app.route('/api/recommendations')
def get_recommendations():
    # Fetch from screener API instead of file
    response = requests.get('http://localhost:5001/api/recommendations')
    return jsonify(response.json())
```

**Note**: This adds complexity and is probably **not needed** for your use case.

---

## Comparison: Current vs Alternative Architectures

| Aspect | Current (File-based) | API-based | Message Queue |
|--------|---------------------|-----------|---------------|
| **Complexity** | ⭐ Low | ⭐⭐ Medium | ⭐⭐⭐ High |
| **Reliability** | ⭐⭐⭐ High | ⭐⭐ Medium | ⭐⭐⭐ High |
| **Real-time** | ❌ No | ✅ Yes | ✅ Yes |
| **Debugging** | ⭐⭐⭐ Easy | ⭐⭐ Medium | ⭐ Hard |
| **Scalability** | ⭐⭐ Medium | ⭐⭐⭐ High | ⭐⭐⭐ High |
| **Dependencies** | None | HTTP client | RabbitMQ/Redis |
| **Best For** | Single-user | Multi-client | Event-driven |

**Recommendation**: **Stick with current file-based architecture** ✅

---

## Summary

### Question: Should ai_stock_screener be separated as a service?

### Answer: **It already is a service and it's well architected!**

**Current State**:
- ✅ Running as systemd service since Jan 9
- ✅ Auto-starts on boot
- ✅ Auto-restarts on failure
- ✅ Security hardened
- ✅ Proper logging
- ✅ Independent from dashboard
- ✅ File-based communication (simple and reliable)

**Recommendation**: **No changes needed**

The current architecture is:
- Appropriate for your use case (single-user, local system)
- Simple and maintainable
- Reliable and fault-tolerant
- Easy to debug and monitor
- Well-configured with security best practices

**Optional Enhancements** (only if needed):
1. Add health check monitoring
2. Set up alerting for stale data
3. Add metrics/dashboards

**Not Recommended** (adds complexity without benefit):
- API-based communication
- Message queue architecture
- Service mesh

---

**Document Created**: 2026-01-12
**Current Architecture**: ✅ Excellent
**Recommended Action**: ✅ Keep as-is
**Service Status**: ✅ Running smoothly for 3 days
