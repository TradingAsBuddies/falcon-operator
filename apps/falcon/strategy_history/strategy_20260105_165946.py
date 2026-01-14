"""
Strategy Version: 20260105_165946
Modified: 2026-01-05T16:59:46.082185
Backtest Results: {
  "initial_value": 10000.0,
  "final_value": 10589.549318116051,
  "return_pct": 5.895493181160509,
  "sharpe_ratio": 0.7756521813802312,
  "max_drawdown": 9.606390303274202,
  "total_trades": 4,
  "winning_trades": 3,
  "win_rate": 75.0
}
"""

"""
AI-Modified Trading Strategy
Deployed via Strategy Manager API
"""
import backtrader as bt

class AIOptimizedStrategy(bt.Strategy):
    """
    AI-optimized RSI mean reversion strategy
    - Relaxed entry threshold for more trades
    - Tighter profit target
    """
    params = (
        ('rsi_period', 14),
        ('rsi_buy', 45),      # Relaxed from 35
        ('rsi_sell', 55),     # Relaxed from 65
        ('hold_days', 12),
        ('profit_target', 0.025),  # 2.5% target
        ('position_size', 0.92),
    )

    def __init__(self):
        self.rsi = bt.indicators.RSI(self.data.close, period=self.params.rsi_period)
        self.order = None
        self.buy_price = None
        self.buy_bar = None

    def next(self):
        if self.order:
            return

        if not self.position:
            if self.rsi[0] < self.params.rsi_buy:
                cash = self.broker.getcash()
                size = int((cash * self.params.position_size) / self.data.close[0])
                if size > 0:
                    self.order = self.buy(size=size)
        else:
            bars_held = len(self) - self.buy_bar if self.buy_bar else 0
            profit_pct = (self.data.close[0] - self.buy_price) / self.buy_price if self.buy_price else 0

            if (self.rsi[0] > self.params.rsi_sell or
                bars_held >= self.params.hold_days or
                profit_pct >= self.params.profit_target):
                self.order = self.sell()

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                self.buy_price = order.executed.price
                self.buy_bar = len(self)
        self.order = None
