#!/bin/bash
# Deploy Momentum Breakout Strategy
# Run this to deploy the winning strategy

echo "Deploying Momentum Breakout Strategy..."
echo ""
echo "WARNING: This will replace active_strategy.py"
read -p "Continue? (y/n) " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    # Backup current strategy
    cp active_strategy.py active_strategy.py.backup_$(date +%Y%m%d_%H%M%S)
    
    # Deploy new strategy
    ./backtest/bin/python3 strategy_manager.py deploy -f strategies/momentum_breakout_strategy.py --force
    
    echo ""
    echo "✓ Strategy deployed!"
    echo "✓ Backup saved to active_strategy.py.backup_*"
    echo ""
    echo "Next steps:"
    echo "  1. Restart falcon-orchestrator service"
    echo "  2. Monitor performance closely"
    echo "  3. Rollback if needed: ./backtest/bin/python3 strategy_manager.py rollback"
else
    echo "Deployment cancelled"
fi
