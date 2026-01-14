#!/bin/bash
# Install Falcon Trading Services (Orchestrator + Dashboard)

set -e

echo "================================================================"
echo "Falcon Trading System - Service Installation"
echo "================================================================"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo "ERROR: This script must be run as root (use sudo)"
    exit 1
fi

# Configuration
INSTALL_ORCHESTRATOR=true
INSTALL_DASHBOARD=true

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --orchestrator-only)
            INSTALL_DASHBOARD=false
            shift
            ;;
        --dashboard-only)
            INSTALL_ORCHESTRATOR=false
            shift
            ;;
        *)
            echo "Usage: $0 [--orchestrator-only|--dashboard-only]"
            exit 1
            ;;
    esac
done

echo "Installing:"
if [ "$INSTALL_ORCHESTRATOR" = true ]; then
    echo "  - Orchestrator (automated trading engine)"
fi
if [ "$INSTALL_DASHBOARD" = true ]; then
    echo "  - Dashboard (web interface and API)"
fi
echo ""

# Check if falcon user exists
if ! id -u falcon &>/dev/null; then
    echo "Creating falcon user..."
    useradd -r -s /bin/false -d /opt/falcon falcon
fi

# Create directories
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
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Core files (needed by both)
cp "$SCRIPT_DIR/db_manager.py" /opt/falcon/
cp "$SCRIPT_DIR/strategy_manager.py" /opt/falcon/
cp "$SCRIPT_DIR/init_strategy_tables.py" /opt/falcon/
cp "$SCRIPT_DIR/youtube_strategies.py" /opt/falcon/ 2>/dev/null || true

if [ "$INSTALL_ORCHESTRATOR" = true ]; then
    echo "Installing orchestrator files..."
    cp "$SCRIPT_DIR/strategy_orchestrator.py" /opt/falcon/
    cp "$SCRIPT_DIR/strategy_executor.py" /opt/falcon/
    cp "$SCRIPT_DIR/strategy_analytics.py" /opt/falcon/
    cp "$SCRIPT_DIR/strategy_optimizer.py" /opt/falcon/
    cp "$SCRIPT_DIR/strategy_parser.py" /opt/falcon/
    cp "$SCRIPT_DIR/paper_trading_bot.py" /opt/falcon/
fi

if [ "$INSTALL_DASHBOARD" = true ]; then
    echo "Installing dashboard files..."
    cp "$SCRIPT_DIR/dashboard_server.py" /opt/falcon/
fi

# Set permissions
chown -R falcon:falcon /opt/falcon

# Check for required Python dependencies
echo "Checking Python dependencies..."
MISSING_DEPS=""

if ! python3 -c "import flask" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS flask"
fi
if ! python3 -c "import anthropic" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS anthropic"
fi
if ! python3 -c "import dotenv" 2>/dev/null; then
    MISSING_DEPS="$MISSING_DEPS python-dotenv"
fi

if [ -n "$MISSING_DEPS" ]; then
    echo "Installing missing dependencies:$MISSING_DEPS"
    pip3 install $MISSING_DEPS --break-system-packages
fi

# Check for .env file
if [ ! -f /opt/falcon/.env ]; then
    echo ""
    echo "WARNING: /opt/falcon/.env not found!"
    echo ""
    echo "Creating template .env file..."
    cat > /opt/falcon/.env << 'EOF'
# Falcon Trading System Configuration

# Polygon.io API Key (required)
MASSIVE_API_KEY=your_polygon_api_key_here

# Claude API Key (required for AI features)
CLAUDE_API_KEY=your_claude_api_key_here

# Trading Configuration (optional)
TRADING_SYMBOLS=SPY,QQQ,AAPL
INITIAL_BALANCE=10000
UPDATE_INTERVAL=60

# Database (optional, defaults to /var/lib/falcon/paper_trading.db)
# DB_PATH=/var/lib/falcon/paper_trading.db
EOF
    chown falcon:falcon /opt/falcon/.env
    chmod 600 /opt/falcon/.env

    echo ""
    echo "Template created at /opt/falcon/.env"
    echo "You MUST edit this file and add your API keys!"
    echo ""
    read -p "Press Enter to continue or Ctrl+C to abort and edit .env..."
fi

# Initialize database tables
echo "Initializing database..."
if [ -f /var/lib/falcon/paper_trading.db ]; then
    echo "Database exists, ensuring strategy tables exist..."
    sudo -u falcon python3 /opt/falcon/init_strategy_tables.py /var/lib/falcon/paper_trading.db || true
else
    echo "Creating new database..."
    sudo -u falcon python3 /opt/falcon/init_strategy_tables.py /var/lib/falcon/paper_trading.db
fi

# Install systemd services
echo ""
echo "Installing systemd services..."

if [ "$INSTALL_ORCHESTRATOR" = true ]; then
    cp "$SCRIPT_DIR/falcon-orchestrator.service" /etc/systemd/system/
    echo "  - falcon-orchestrator.service installed"
fi

if [ "$INSTALL_DASHBOARD" = true ]; then
    cp "$SCRIPT_DIR/falcon-dashboard-fhs.service" /etc/systemd/system/falcon-dashboard.service
    echo "  - falcon-dashboard.service installed"
fi

# Reload systemd
echo "Reloading systemd..."
systemctl daemon-reload

echo ""
echo "================================================================"
echo "Installation Complete!"
echo "================================================================"
echo ""

if [ "$INSTALL_ORCHESTRATOR" = true ]; then
    echo "Orchestrator Service:"
    echo "  Start:   sudo systemctl start falcon-orchestrator"
    echo "  Stop:    sudo systemctl stop falcon-orchestrator"
    echo "  Status:  sudo systemctl status falcon-orchestrator"
    echo "  Logs:    sudo journalctl -u falcon-orchestrator -f"
    echo "  Enable:  sudo systemctl enable falcon-orchestrator  (auto-start on boot)"
    echo ""
fi

if [ "$INSTALL_DASHBOARD" = true ]; then
    echo "Dashboard Service:"
    echo "  Start:   sudo systemctl start falcon-dashboard"
    echo "  Stop:    sudo systemctl stop falcon-dashboard"
    echo "  Status:  sudo systemctl status falcon-dashboard"
    echo "  Logs:    sudo journalctl -u falcon-dashboard -f"
    echo "  Enable:  sudo systemctl enable falcon-dashboard  (auto-start on boot)"
    echo "  URL:     http://localhost:5000"
    echo ""
fi

echo "Configuration:"
echo "  User:           falcon"
echo "  Working Dir:    /opt/falcon"
echo "  Database:       /var/lib/falcon/paper_trading.db"
echo "  Environment:    /opt/falcon/.env"
echo ""
echo "Quick Start:"
echo "  1. Edit /opt/falcon/.env and add your API keys"
echo "  2. Start services:"
if [ "$INSTALL_DASHBOARD" = true ]; then
    echo "     sudo systemctl start falcon-dashboard"
fi
if [ "$INSTALL_ORCHESTRATOR" = true ]; then
    echo "     sudo systemctl start falcon-orchestrator"
fi
echo "  3. Check status:"
if [ "$INSTALL_DASHBOARD" = true ]; then
    echo "     sudo systemctl status falcon-dashboard"
fi
if [ "$INSTALL_ORCHESTRATOR" = true ]; then
    echo "     sudo systemctl status falcon-orchestrator"
fi
if [ "$INSTALL_DASHBOARD" = true ]; then
    echo "  4. Add strategies via API: http://localhost:5000"
fi
echo ""
echo "================================================================"
