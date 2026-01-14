#!/usr/bin/env python3
"""
Strategy Parser - AI-Powered Code Generation
Converts YouTube strategy text rules into executable backtrader code
"""

import anthropic
import json
import re
from typing import Dict, Tuple, Optional
from strategy_manager import StrategyManager


class StrategyCodeGenerator:
    """Converts text strategy rules to executable backtrader code using Claude AI"""

    def __init__(self, claude_api_key: str):
        """
        Initialize strategy code generator

        Args:
            claude_api_key: Claude API key for AI generation
        """
        self.client = anthropic.Anthropic(api_key=claude_api_key)
        self.strategy_manager = StrategyManager()

    def parse_strategy_rules(self, entry_rules: str, exit_rules: str,
                            risk_management: str, strategy_name: str) -> Dict:
        """
        Use Claude to extract structured components from text rules

        Args:
            entry_rules: Text description of entry conditions
            exit_rules: Text description of exit conditions
            risk_management: Text description of risk management
            strategy_name: Name of the strategy

        Returns:
            Dict with parsed components:
            {
                'indicators': ['RSI', 'SMA'],
                'parameters': {'rsi_period': 14, 'sma_period': 50},
                'entry_condition': 'self.rsi < 30 and self.data.close > self.sma',
                'exit_condition': 'self.rsi > 70 or bars_held > 10',
                'position_size_pct': 0.10,
                'stop_loss_pct': 0.02,
                'take_profit_pct': 0.05
            }
        """
        prompt = f"""Parse these trading strategy rules into structured components for a backtrader Strategy implementation.

STRATEGY NAME: {strategy_name}

ENTRY RULES:
{entry_rules}

EXIT RULES:
{exit_rules}

RISK MANAGEMENT:
{risk_management}

Extract and return JSON with the following structure:
{{
    "indicators": ["RSI", "SMA", "MACD", "Volume", etc.],
    "parameters": {{"rsi_period": 14, "sma_period": 50, "entry_threshold": 30, etc.}},
    "entry_condition": "Python expression like 'self.rsi < self.params.entry_threshold and self.data.close > self.sma'",
    "exit_condition": "Python expression like 'self.rsi > 70 or self.bars_held >= self.params.hold_days'",
    "position_size_pct": 0.10,
    "stop_loss_pct": 0.02,
    "take_profit_pct": 0.05,
    "additional_state": ["entry_price", "bars_held"] (any state variables needed)
}}

IMPORTANT RULES:
1. Use proper backtrader indicator names (bt.indicators.RSI, bt.indicators.SMA, etc.)
2. Reference indicators as self.<indicator_name> (e.g., self.rsi, self.sma)
3. Reference parameters as self.params.<param_name>
4. Entry/exit conditions must be valid Python expressions
5. Position size should be a decimal (0.10 = 10% of capital)
6. Stop loss and take profit should be decimals (0.02 = 2%)
7. If rules mention "bars held" or "days", include bars_held in additional_state

Return ONLY the JSON object, no other text."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Extract JSON from response
            json_match = re.search(r'\{[\s\S]*\}', content)
            if json_match:
                parsed = json.loads(json_match.group())
                print(f"[PARSER] Successfully parsed strategy rules")
                return parsed
            else:
                raise ValueError("Could not extract JSON from Claude response")

        except Exception as e:
            print(f"[PARSER] Error parsing rules: {e}")
            raise

    def generate_backtrader_code(self, parsed_rules: Dict,
                                 strategy_name: str) -> str:
        """
        Generate complete backtrader Strategy class from parsed rules

        Args:
            parsed_rules: Output from parse_strategy_rules()
            strategy_name: Name of the strategy

        Returns:
            Complete Python code for backtrader Strategy class
        """
        # Clean strategy name for class name
        class_name = ''.join(c for c in strategy_name if c.isalnum() or c == '_')
        if not class_name:
            class_name = "GeneratedStrategy"

        # Extract components
        indicators = parsed_rules.get('indicators', [])
        parameters = parsed_rules.get('parameters', {})
        entry_condition = parsed_rules.get('entry_condition', 'False')
        exit_condition = parsed_rules.get('exit_condition', 'False')
        position_size_pct = parsed_rules.get('position_size_pct', 0.10)
        stop_loss_pct = parsed_rules.get('stop_loss_pct', 0.02)
        take_profit_pct = parsed_rules.get('take_profit_pct', 0.05)
        additional_state = parsed_rules.get('additional_state', [])

        # Build params tuple
        params_list = [f"('{k}', {v})" for k, v in parameters.items()]
        params_list.append(f"('position_size_pct', {position_size_pct})")
        params_list.append(f"('stop_loss_pct', {stop_loss_pct})")
        params_list.append(f"('take_profit_pct', {take_profit_pct})")
        params_str = ',\n        '.join(params_list)

        # Build indicator initialization
        indicator_init = []
        for indicator in indicators:
            if indicator == 'RSI':
                period = parameters.get('rsi_period', 14)
                indicator_init.append(f"self.rsi = bt.indicators.RSI(self.data.close, period={period})")
            elif indicator == 'SMA':
                period = parameters.get('sma_period', 50)
                indicator_init.append(f"self.sma = bt.indicators.SMA(self.data.close, period={period})")
            elif indicator == 'MACD':
                indicator_init.append("self.macd = bt.indicators.MACD(self.data.close)")
            elif indicator == 'Volume':
                indicator_init.append("self.volume = self.data.volume")
            elif indicator == 'EMA':
                period = parameters.get('ema_period', 20)
                indicator_init.append(f"self.ema = bt.indicators.EMA(self.data.close, period={period})")

        indicator_init_str = '\n        '.join(indicator_init)

        # Build state variable initialization
        state_vars = ['self.order = None', 'self.entry_price = None']
        for var in additional_state:
            state_vars.append(f"self.{var} = None")
        state_vars_str = '\n        '.join(state_vars)

        # Generate code
        code = f'''"""
{strategy_name}
Auto-generated trading strategy from text rules
"""

import backtrader as bt


class {class_name}(bt.Strategy):
    """
    {strategy_name}

    Generated from YouTube strategy rules
    """

    params = (
        {params_str}
    )

    def __init__(self):
        """Initialize indicators and state"""
        # Technical indicators
        {indicator_init_str}

        # State tracking
        {state_vars_str}

    def next(self):
        """Execute strategy logic"""
        # Skip if we have a pending order
        if self.order:
            return

        # Entry logic
        if not self.position:
            # Check entry condition
            if {entry_condition}:
                # Calculate position size
                cash = self.broker.getcash()
                size = int((cash * self.params.position_size_pct) / self.data.close[0])

                if size > 0:
                    self.entry_price = self.data.close[0]
                    self.bars_held = 0
                    self.order = self.buy(size=size)
                    print(f"BUY {{size}} @ {{self.data.close[0]:.2f}}")

        # Exit logic
        else:
            # Update bars held counter
            if hasattr(self, 'bars_held'):
                self.bars_held += 1

            # Calculate stop loss and take profit levels
            if self.entry_price:
                stop_loss_price = self.entry_price * (1 - self.params.stop_loss_pct)
                take_profit_price = self.entry_price * (1 + self.params.take_profit_pct)

                # Check stop loss
                if self.data.close[0] <= stop_loss_price:
                    self.order = self.close()
                    print(f"STOP LOSS @ {{self.data.close[0]:.2f}}")
                    return

                # Check take profit
                if self.data.close[0] >= take_profit_price:
                    self.order = self.close()
                    print(f"TAKE PROFIT @ {{self.data.close[0]:.2f}}")
                    return

            # Check exit condition
            if {exit_condition}:
                self.order = self.close()
                print(f"EXIT @ {{self.data.close[0]:.2f}}")

    def notify_order(self, order):
        """Handle order notifications"""
        if order.status in [order.Completed]:
            if order.isbuy():
                print(f"BUY EXECUTED @ {{order.executed.price:.2f}}")
            elif order.issell():
                print(f"SELL EXECUTED @ {{order.executed.price:.2f}}")
                self.entry_price = None
                self.bars_held = None

            self.order = None

        elif order.status in [order.Canceled, order.Margin, order.Rejected]:
            print(f"Order Canceled/Margin/Rejected")
            self.order = None
'''

        return code

    def validate_and_fix(self, code: str, max_attempts: int = 3) -> Tuple[bool, str, str]:
        """
        Validate generated code and use Claude to fix errors if needed

        Args:
            code: Generated strategy code
            max_attempts: Maximum number of fix attempts

        Returns:
            Tuple of (success, validated_code, error_message)
        """
        for attempt in range(max_attempts):
            print(f"[PARSER] Validation attempt {attempt + 1}/{max_attempts}")

            # Validate with StrategyManager
            valid, results = self.strategy_manager.validate_strategy(code)

            if valid:
                print(f"[PARSER] Code validation successful")
                return True, code, ""

            # Extract error message
            error_msg = results.get('error', 'Unknown validation error')
            print(f"[PARSER] Validation failed: {error_msg}")

            if attempt < max_attempts - 1:
                # Ask Claude to fix the errors
                code = self._fix_code_with_ai(code, error_msg)
            else:
                return False, code, error_msg

        return False, code, "Max fix attempts reached"

    def _fix_code_with_ai(self, code: str, error: str) -> str:
        """
        Use Claude to fix code errors

        Args:
            code: Strategy code with errors
            error: Error message from validation

        Returns:
            Fixed code
        """
        prompt = f"""Fix the following Python backtrader strategy code. It has validation errors.

ORIGINAL CODE:
```python
{code}
```

ERROR:
{error}

Please provide the corrected code. Return ONLY the complete corrected Python code, no explanations."""

        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-5-20250929",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            content = response.content[0].text

            # Extract code from response
            code_match = re.search(r'```python\n([\s\S]*?)\n```', content)
            if code_match:
                fixed_code = code_match.group(1)
                print(f"[PARSER] Claude provided fix")
                return fixed_code
            else:
                # If no code block, assume entire response is code
                print(f"[PARSER] Using full response as code")
                return content

        except Exception as e:
            print(f"[PARSER] Error getting fix from Claude: {e}")
            return code  # Return original if fix fails

    def generate_from_youtube_strategy(self, youtube_strategy: Dict) -> Tuple[bool, str, str]:
        """
        Complete pipeline: YouTube strategy → Validated code

        Args:
            youtube_strategy: Dict from YouTubeStrategyDB.get_strategy_by_id()

        Returns:
            Tuple of (success, code, error_message)
        """
        try:
            print(f"[PARSER] Generating code for: {youtube_strategy.get('title', 'Unknown')}")

            # Step 1: Parse text rules
            parsed_rules = self.parse_strategy_rules(
                entry_rules=youtube_strategy.get('entry_rules', ''),
                exit_rules=youtube_strategy.get('exit_rules', ''),
                risk_management=youtube_strategy.get('risk_management', ''),
                strategy_name=youtube_strategy.get('title', 'Generated Strategy')
            )

            # Step 2: Generate code
            code = self.generate_backtrader_code(
                parsed_rules,
                youtube_strategy.get('title', 'Generated Strategy')
            )

            # Step 3: Validate and fix
            success, validated_code, error = self.validate_and_fix(code)

            if success:
                print(f"[PARSER] Successfully generated valid strategy code")
                return True, validated_code, ""
            else:
                print(f"[PARSER] Failed to generate valid code: {error}")
                return False, validated_code, error

        except Exception as e:
            print(f"[PARSER] Error in generation pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False, "", str(e)


def main():
    """Test the strategy parser"""
    import os
    import sys

    claude_key = os.getenv('CLAUDE_API_KEY')
    if not claude_key:
        print("ERROR: CLAUDE_API_KEY not set")
        sys.exit(1)

    # Test with a sample strategy
    generator = StrategyCodeGenerator(claude_key)

    sample_strategy = {
        'title': 'Simple RSI Mean Reversion',
        'entry_rules': 'Enter when RSI drops below 30, indicating oversold conditions',
        'exit_rules': 'Exit when RSI rises above 70, or after holding for 5 days',
        'risk_management': 'Risk 10% of capital per trade, with 2% stop loss and 5% take profit'
    }

    print("Testing strategy code generation...")
    print("=" * 60)

    success, code, error = generator.generate_from_youtube_strategy(sample_strategy)

    if success:
        print("\nGENERATED CODE:")
        print("=" * 60)
        print(code)
        print("=" * 60)
        print("\nSUCCESS: Valid strategy code generated")
    else:
        print(f"\nFAILED: {error}")
        print("\nGENERATED CODE (with errors):")
        print("=" * 60)
        print(code)
        print("=" * 60)


if __name__ == '__main__':
    main()
