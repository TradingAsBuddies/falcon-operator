#!/bin/bash
# Install Falcon Strategy Orchestrator as systemd service

set -e

echo "================================================================"
echo "Falcon Strategy Orchestrator - Service Installation"
echo "================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Check if falcon user exists
if ! id -u falcon &>/dev/null; then
    echo "Creating falcon user..."
    useradd -r -s /bin/false -d /opt/falcon falcon
fi

# Create directories if they don't exist
echo "Setting up directories..."
mkdir -p /opt/falcon
mkdir -p /var/lib/falcon
mkdir -p /etc/falcon

# Set ownership
chown -R falcon:falcon /opt/falcon
chown -R falcon:falcon /var/lib/falcon
chown -R falcon:falcon /etc/falcon

# Copy Python files to /opt/falcon
echo "Copying application files..."
cp strategy_orchestrator.py /opt/falcon/
cp strategy_executor.py /opt/falcon/
cp strategy_analytics.py /opt/falcon/
cp strategy_optimizer.py /opt/falcon/
cp strategy_parser.py /opt/falcon/
cp paper_trading_bot.py /opt/falcon/
cp db_manager.py /opt/falcon/
cp strategy_manager.py /opt/falcon/
cp init_strategy_tables.py /opt/falcon/

# Check for required Python dependencies
echo "Checking Python dependencies..."
if ! python3 -c "import anthropic" 2>/dev/null; then
    echo "Installing anthropic library..."
    pip3 install anthropic --break-system-packages
fi

# Check for .env file
if [ ! -f /opt/falcon/.env ]; then
    echo ""
    echo "WARNING: /opt/falcon/.env not found!"
    echo "You need to create /opt/falcon/.env with:"
    echo "  MASSIVE_API_KEY=your_polygon_api_key"
    echo "  CLAUDE_API_KEY=your_claude_api_key"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to abort..."
fi

# Install systemd service
echo "Installing systemd service..."
cp falcon-orchestrator.service /etc/systemd/system/

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

# Initialize database tables if needed
echo "Initializing database tables..."
if [ -f /var/lib/falcon/paper_trading.db ]; then
    echo "Database exists, checking for strategy tables..."
    sudo -u falcon python3 /opt/falcon/init_strategy_tables.py /var/lib/falcon/paper_trading.db || true
else
    echo "Creating new database..."
    sudo -u falcon python3 /opt/falcon/init_strategy_tables.py /var/lib/falcon/paper_trading.db
fi

echo ""
echo "================================================================"
echo "Installation Complete!"
echo "================================================================"
echo ""
echo "Service: falcon-orchestrator"
echo "User: falcon"
echo "Working Directory: /opt/falcon"
echo "Database: /var/lib/falcon/paper_trading.db"
echo ""
echo "Commands:"
echo "  Start:   sudo systemctl start falcon-orchestrator"
echo "  Stop:    sudo systemctl stop falcon-orchestrator"
echo "  Status:  sudo systemctl status falcon-orchestrator"
echo "  Logs:    sudo journalctl -u falcon-orchestrator -f"
echo "  Enable:  sudo systemctl enable falcon-orchestrator  (start on boot)"
echo ""
echo "Next Steps:"
echo "  1. Ensure /opt/falcon/.env has API keys set"
echo "  2. Start the service: sudo systemctl start falcon-orchestrator"
echo "  3. Check logs: sudo journalctl -u falcon-orchestrator -f"
echo "  4. Add strategies via dashboard API"
echo ""
echo "================================================================"
