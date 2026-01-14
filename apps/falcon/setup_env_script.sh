#!/bin/bash
# Setup script for AI Trading Bot

echo "=================================="
echo "AI Trading Bot - Environment Setup"
echo "=================================="

# Create .env file
if [ ! -f .env ]; then
    echo ""
    echo "Creating .env file..."
    cat > .env << 'EOF'
# Required: Massive.com (Polygon.io) API Key
MASSIVE_API_KEY=your_massive_api_key_here

# AI Agents (set at least one, in order of preference)
# Priority 1: Claude (best for structured analysis)
CLAUDE_API_KEY=your_claude_key_here

# Priority 2: ChatGPT (good alternative)
OPENAI_API_KEY=your_openai_key_here

# Priority 3: Perplexity (good for real-time news)
PERPLEXITY_API_KEY=your_perplexity_key_here

# Finviz Screener URL (customize your filters)
# Example: High volume, under $20, RSI oversold
FINVIZ_SCREENER_URL=https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o750,sh_price_u20,ta_rsi_os40
EOF
    echo "✓ Created .env file"
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo ""
else
    echo "✓ .env file already exists"
fi

# Install Python dependencies
echo ""
echo "Installing Python dependencies..."
pip3 install -q requests pandas beautifulsoup4 schedule pytz python-dotenv

if [ $? -eq 0 ]; then
    echo "✓ Dependencies installed"
else
    echo "✗ Failed to install dependencies"
    exit 1
fi

# Initialize database
echo ""
echo "Initializing database..."
python3 init_database.py

if [ $? -eq 0 ]; then
    echo "✓ Database initialized"
else
    echo "✗ Failed to initialize database"
    exit 1
fi

echo ""
echo "=================================="
echo "Setup Complete!"
echo "=================================="
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Customize your Finviz screener URL"
echo "3. Run the bot:"
echo "   python3 integrated_trading_bot.py"
echo ""
echo "Or run paper trading:"
echo "   python3 live_paper_trading.py YOUR_API_KEY"
echo ""
echo "Or run backtesting:"
echo "   python3 paper_trading_bot.py"
echo ""
echo "Or test the screener only:"
echo "   python3 ai_stock_screener.py --test"
echo ""
