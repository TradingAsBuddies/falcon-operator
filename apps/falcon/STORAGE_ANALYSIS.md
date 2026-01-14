# Storage Analysis and Management

**Date**: 2026-01-12
**Status**: HEALTHY (36% free space available)

---

## Current Disk Space

```
Filesystem: /dev/mmcblk0p2
Total Size: 28GB
Used: 17GB (64%)
Available: 9.6GB (36%)
Status: HEALTHY
```

**Assessment**: System has adequate free space. No immediate cleanup required.

---

## Falcon Directory Breakdown

### Total Usage: 335MB

| Component | Size | % of Total | Notes |
|-----------|------|------------|-------|
| **backtest/** | 326MB | 97.3% | Python virtual environment (necessary) |
| **market_data/** | 1.9MB | 0.6% | Well compressed historical data |
| **.git/** | 2.4MB | 0.7% | Git repository |
| **paper_trading.db** | 2.3MB | 0.7% | Trading database |
| **orchestrator/** | 208KB | 0.1% | Orchestrator module |
| **Other** | ~2.2MB | 0.6% | Various files |

---

## Market Data Storage

### Intraday Bars (1-minute data)

```
Location: market_data/intraday_bars/
Total Size: 1.4MB
Files: 40 trading days
Tickers: 6 (SPY, QQQ, AAPL, TSLA, NVDA, JPM)
Date Range: Nov 13, 2025 - Jan 12, 2026
Avg File Size: 33KB compressed
Total Bars: 75,000+ across all tickers
Compression: gzip (excellent compression ratio)
```

**Storage Efficiency**: Each day of 6-ticker 1-minute data uses only ~33KB compressed

**Growth Projection**:
- Per month: ~660KB (20 trading days)
- Per year: ~8MB (250 trading days)
- Very sustainable growth rate

### Daily Bars

```
Location: market_data/daily_bars/
Total Size: 508KB
Files: 124 trading days
Date Range: Jul 16, 2025 - Jan 12, 2026
Avg File Size: ~400 bytes compressed
```

**Growth Projection**:
- Per year: ~100KB (250 trading days)
- Negligible impact on storage

---

## Database Storage

### paper_trading.db: 2.3MB

```
Orders: 38 records
Positions: 5 records
Account: 1 record
```

**Growth Projection**:
- With 1-2 trades/day: ~50-100 orders/month
- Database grows ~100-200KB/month
- Per year: ~1-2MB growth

**Status**: Very efficient, no cleanup needed

---

## Large Components Analysis

### backtest/ Virtual Environment: 326MB

**Contents**:
- numpy: 30MB (required for calculations)
- pandas: 56MB (required for data handling)
- matplotlib: 25MB (required for plotting)
- talib: 20MB (technical analysis library)
- curl_cffi: 22MB (web scraping)
- Other dependencies: ~173MB

**Status**: NECESSARY - Cannot be reduced without breaking functionality

**Recommendation**: Keep as-is. This is a standard Python virtual environment size for a data science/trading application.

---

## Storage Growth Projections

### Next 30 Days
```
Intraday data: +660KB (20 trading days)
Daily bars: +8KB (20 trading days)
Database: +200KB (40 orders)
Logs: +50KB
Total: ~920KB (~1MB)
```

### Next 12 Months
```
Intraday data: +8MB (250 trading days)
Daily bars: +100KB
Database: +2MB
Logs: +600KB
Total: ~11MB
```

**Conclusion**: Storage growth is very sustainable. Current compression strategy is working excellently.

---

## Storage Management Strategy

### Current State: No Action Needed

The system is healthy with 9.6GB free space. However, here are management guidelines:

### When to Take Action

**WARNING Level** (< 2GB free):
- Review and compress old logs
- Consider archiving data older than 6 months

**CRITICAL Level** (< 1GB free):
- Archive data older than 3 months
- Compress paper_trading.db (vacuum)
- Clean up old backtest results

### Cleanup Priorities (if needed)

1. **Old daily_bars** (LOW PRIORITY)
   - Currently only 508KB
   - Could remove data older than 1 year
   - Savings: ~100-200KB (minimal)

2. **Log files** (MEDIUM PRIORITY)
   - Currently negligible (< 5KB)
   - Implement log rotation if they grow
   - Keep last 30 days only

3. **Old screened_stocks.json entries** (LOW PRIORITY)
   - Currently 148KB
   - Could trim to last 30 days
   - Savings: ~50-100KB

4. **Database vacuum** (LOW PRIORITY)
   - Run SQLite VACUUM command
   - Reclaims deleted space
   - Potential savings: 10-20%

### What NOT to Clean

**DO NOT DELETE**:
- backtest/ directory (326MB but essential)
- Current intraday_bars (needed for live trading)
- paper_trading.db (trading history)
- .git directory (version control)

---

## Monitoring Recommendations

### Automated Monitoring

Run weekly disk space check:
```bash
# Check if free space drops below 2GB
FREE_SPACE=$(df /home/ospartners/src/falcon | awk 'NR==2 {print $4}')
if [ $FREE_SPACE -lt 2097152 ]; then
    echo "WARNING: Low disk space"
fi
```

### Manual Checks

Run monthly:
```bash
# Check falcon directory size
du -sh /home/ospartners/src/falcon

# Check market data growth
du -sh market_data/intraday_bars/
du -sh market_data/daily_bars/

# Check database size
ls -lh paper_trading.db

# Check available space
df -h /
```

---

## Cleanup Script

A storage cleanup script has been created: `storage_cleanup.py`

**Usage**:
```bash
# Check what would be cleaned (dry run)
python3 storage_cleanup.py --dry-run

# Clean old data (older than 6 months)
python3 storage_cleanup.py --older-than 180

# Clean old data (older than 1 year)
python3 storage_cleanup.py --older-than 365

# Vacuum database
python3 storage_cleanup.py --vacuum-db

# Full cleanup
python3 storage_cleanup.py --full-cleanup
```

---

## Current Status Summary

**Overall Health**: EXCELLENT

**Strengths**:
- Excellent data compression (33KB per day for 6 tickers)
- Sustainable growth rate (~11MB/year)
- Plenty of free space (9.6GB available)
- No unnecessary large files
- Efficient database usage

**No immediate action required**. The storage management strategy is working well.

**Recommendation**:
1. Monitor quarterly
2. Implement automated cleanup when free space drops below 2GB
3. Continue current compression strategy

---

## Technical Details

### Compression Analysis

**Intraday bars (1-minute)**:
- Uncompressed: ~200KB per day per ticker
- Compressed (gzip): ~5.5KB per day per ticker
- Compression ratio: ~97% reduction
- 6 tickers: ~33KB per day compressed

**Daily bars**:
- Uncompressed: ~2KB per day
- Compressed (gzip): ~400 bytes per day
- Compression ratio: ~80% reduction

**Why compression works so well**:
- CSV format has high redundancy
- gzip efficiently compresses repeated patterns
- Numeric data compresses well

### Storage Best Practices

1. **Keep using gzip compression** for all CSV files
2. **Group data by date** (current strategy is optimal)
3. **Avoid storing duplicate data** (current deduplication working)
4. **Archive old data** to external storage if needed
5. **Regular database vacuum** to reclaim space

---

## Troubleshooting

### If you run low on space

**Immediate actions**:
```bash
# 1. Check what's using space
du -h /home/ospartners/src/falcon | sort -h | tail -20

# 2. Check for large log files
find . -name "*.log" -type f -size +10M

# 3. Clean old intraday data (older than 6 months)
python3 storage_cleanup.py --older-than 180

# 4. Vacuum database
python3 storage_cleanup.py --vacuum-db
```

**Emergency cleanup** (if critical):
```bash
# Remove intraday data older than 3 months (keeps recent data)
find market_data/intraday_bars/ -name "*.csv.gz" -mtime +90 -delete

# Remove daily bars older than 1 year
find market_data/daily_bars/ -name "*.csv.gz" -mtime +365 -delete
```

---

**Analysis Complete**: 2026-01-12
**Status**: HEALTHY (9.6GB free)
**Action Required**: NONE (monitoring only)
**Next Review**: 2026-04-12 (quarterly)
