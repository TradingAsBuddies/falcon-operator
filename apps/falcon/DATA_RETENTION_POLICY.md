# Falcon Data Retention Policy (Raspberry Pi Optimized)

## Storage Constraints
- **Device:** Raspberry Pi with 28GB total, ~9.6GB available
- **Current Usage:** 410MB for Falcon project
- **Goal:** Keep usage under 500MB, maintain critical data only

---

## Retention Policies

### 1. Trading Data (paper_trading.db)
| Data Type | Retention Period | Rationale |
|-----------|------------------|-----------|
| **Current account state** | Permanent | Essential |
| **Open positions** | Permanent | Essential |
| **Orders (completed)** | 30 days | Sufficient for analysis |
| **Performance metrics** | 90 days | Strategy evaluation |
| **Backtest results** | Keep best 10 per strategy | Comparison data |

**Expected Growth:** ~100KB/day → 3MB/month
**Action:** Monthly vacuum and cleanup of old orders

### 2. AI Screener Results (screened_stocks.json)
| Data Type | Retention Period | Size Impact |
|-----------|------------------|-------------|
| **Morning/evening screens** | 7 days | ~50KB total |
| **Recommendations** | 7 days | Sufficient for backtesting |

**Action:** Weekly cleanup, keep only last 7 days

### 3. Strategy Versions (strategy_history/)
| Data Type | Retention Period | Size Impact |
|-----------|------------------|-------------|
| **Active strategy** | Permanent | ~2KB |
| **Historical versions** | Keep last 5 | ~10KB |
| **Git commits** | All (compressed) | Negligible |

**Action:** Keep only 5 most recent versions, all in git

### 4. Python Cache (__pycache__, *.pyc)
| Data Type | Retention Period | Size Impact |
|-----------|------------------|-------------|
| **Compiled bytecode** | Regenerate as needed | ~100MB |

**Action:** Weekly cleanup, regenerates on import

### 5. Logs and Temporary Files
| Data Type | Retention Period | Size Impact |
|-----------|------------------|-------------|
| **System logs** | 7 days | Varies |
| **Backup files (~)** | Delete immediately | ~10KB |
| **Temp files** | Delete after use | Varies |

**Action:** Daily cleanup

### 6. Market Data (if stored locally)
| Data Type | Retention Period | Notes |
|-----------|------------------|-------|
| **Live prices** | Do NOT store | Use API only |
| **Historical OHLCV** | Do NOT store locally | Use yfinance or Polygon API |
| **Cached quotes** | 1 hour max | Memory only |

**Critical:** Do NOT download full historical datasets to disk

---

## Automated Cleanup Schedule

### Daily (5:00 AM)
```bash
python3 storage_cleanup.py --apply --quick
```
- Remove Python cache
- Remove backup files (~)
- Remove temp files

### Weekly (Sunday 2:00 AM)
```bash
python3 storage_cleanup.py --apply
```
- Full cleanup (all operations)
- Optimize database (30-day retention)
- Clean old screener results (7-day retention)
- Clean old strategy versions (keep 5)

### Monthly (1st of month, 3:00 AM)
```bash
python3 storage_cleanup.py --apply --aggressive
sqlite3 paper_trading.db "VACUUM"
```
- Aggressive database optimization
- Archive old backtest results
- System storage report

---

## Storage Monitoring

### Warning Thresholds
- **Yellow (80% used):** 22.4GB / 28GB
- **Red (90% used):** 25.2GB / 28GB

### Actions at Thresholds
**Yellow:**
- Review non-essential files
- Clean Python cache immediately
- Check for large log files

**Red:**
- Emergency cleanup
- Stop non-essential services
- Move data to external storage if needed

---

## What to NEVER Delete

1. **active_strategy.py** - Current deployed strategy
2. **paper_trading.db** - Current account/position state
3. **.env** - API keys and configuration
4. **systemd service files** - In /etc/systemd/system/
5. **Git repository** - Strategy version history

---

## Space-Saving Best Practices

### DO:
✅ Use API calls for real-time data (don't cache)
✅ Compress backtest results (JSON → gzip)
✅ Store only summary metrics, not raw ticks
✅ Use SQLite with VACUUM regularly
✅ Keep strategy code lean (<5KB per version)
✅ Clean Python cache weekly
✅ Use systemd journal rotation (default)

### DON'T:
❌ Download historical data to disk
❌ Store tick-by-tick data
❌ Keep all screening results forever
❌ Log verbose trade details
❌ Save chart images/PDFs
❌ Keep old CSV exports
❌ Store redundant backups

---

## Recovery Strategy

If storage becomes critically low:

1. **Immediate (Manual):**
   ```bash
   python3 storage_cleanup.py --apply --aggressive
   find . -name "*.pyc" -delete
   find . -name "__pycache__" -type d -exec rm -rf {} +
   ```

2. **Export Critical Data:**
   ```bash
   sqlite3 paper_trading.db ".dump" | gzip > backup_$(date +%Y%m%d).sql.gz
   ```

3. **Archive & Clear:**
   - Move backups to external storage
   - Reset screened_stocks.json
   - Prune old order history

---

## Monitoring Commands

```bash
# Check total usage
du -sh /home/ospartners/src/falcon

# Check disk space
df -h /

# Run cleanup report
python3 storage_cleanup.py

# Database size
ls -lh paper_trading.db

# Strategy history size
du -sh strategy_history/
```

---

## Expected Steady-State Usage

| Component | Size | Notes |
|-----------|------|-------|
| Python venv (backtest/) | 403MB | Static after install |
| Source code | ~500KB | Grows slowly |
| Database | 3-5MB | With 30-day retention |
| Screener results | ~50KB | With 7-day retention |
| Strategy history | ~10KB | Keep last 5 versions |
| Python cache | 0-100MB | Cleaned weekly |
| **Total** | **~410-510MB** | Sustainable |

---

*Last Updated: 2026-01-08*
*Review Period: Quarterly*
