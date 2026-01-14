#!/bin/bash
# Setup automated cleanup cron jobs for Falcon

FALCON_DIR="/home/ospartners/src/falcon"
PYTHON="/usr/bin/python3"

echo "Setting up Falcon storage cleanup cron jobs..."

# Create temporary cron file
CRON_FILE=$(mktemp)

# Get existing cron jobs (excluding Falcon cleanup)
crontab -l 2>/dev/null | grep -v "storage_cleanup.py" > "$CRON_FILE"

# Add daily quick cleanup (5:00 AM)
echo "# Falcon - Daily quick cleanup" >> "$CRON_FILE"
echo "0 5 * * * cd $FALCON_DIR && $PYTHON storage_cleanup.py --apply --quick >> /tmp/falcon_cleanup_daily.log 2>&1" >> "$CRON_FILE"

# Add weekly full cleanup (Sunday 2:00 AM)
echo "" >> "$CRON_FILE"
echo "# Falcon - Weekly full cleanup" >> "$CRON_FILE"
echo "0 2 * * 0 cd $FALCON_DIR && $PYTHON storage_cleanup.py --apply >> /tmp/falcon_cleanup_weekly.log 2>&1" >> "$CRON_FILE"

# Add monthly aggressive cleanup (1st of month, 3:00 AM)
echo "" >> "$CRON_FILE"
echo "# Falcon - Monthly aggressive cleanup and vacuum" >> "$CRON_FILE"
echo "0 3 1 * * cd $FALCON_DIR && $PYTHON storage_cleanup.py --apply --aggressive && sqlite3 paper_trading.db 'VACUUM' >> /tmp/falcon_cleanup_monthly.log 2>&1" >> "$CRON_FILE"

# Install new crontab
crontab "$CRON_FILE"
rm "$CRON_FILE"

echo "✓ Cron jobs installed successfully!"
echo ""
echo "Scheduled cleanups:"
echo "  Daily:   5:00 AM - Quick cleanup (cache, temp files)"
echo "  Weekly:  Sunday 2:00 AM - Full cleanup"
echo "  Monthly: 1st @ 3:00 AM - Aggressive cleanup + vacuum"
echo ""
echo "View logs:"
echo "  tail -f /tmp/falcon_cleanup_*.log"
echo ""
echo "Verify cron:"
echo "  crontab -l | grep falcon"
