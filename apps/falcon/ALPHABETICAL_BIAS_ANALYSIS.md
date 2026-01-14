# Alphabetical Bias Issue - Analysis and Fix

## Problem Identified

**Issue**: All traded stocks begin with letter "A" (ACI, ABR, ACHC, ALIT, ASNS)

**Root Cause**: The Finviz screener URL lacks a sort parameter, causing it to return results in default alphabetical order by ticker symbol.

**Current URL**:
```
https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o750,sh_price_u20,ta_rsi_os40&auth=...
```

**Breakdown**:
- `v=111` - View type (overview)
- `f=sh_avgvol_o750` - Filter: Average volume > 750K shares
- `f=sh_price_u20` - Filter: Price under $20
- `f=ta_rsi_os40` - Filter: RSI oversold (under 40)
- **MISSING**: Sort parameter (`o=`)

## Impact

1. **Limited Stock Universe**: Only analyzing stocks starting with "A"
2. **Missed Opportunities**: Better trading setups in B-Z stocks ignored
3. **AI Bias**: AI screener only sees alphabetically-first stocks
4. **Poor Diversification**: All positions from same alphabetical range

## Solution Options

### Option 1: Sort by Performance Today (Momentum)
**URL Addition**: `&o=-change`
- Prioritizes stocks with strongest intraday momentum
- Good for momentum/breakout strategies
- Finds stocks already moving

### Option 2: Sort by RSI Value (Most Oversold First)
**URL Addition**: `&o=rsi`
- Prioritizes most oversold stocks
- Perfect for mean reversion strategies
- Matches the strategy's RSI focus

### Option 3: Sort by Relative Volume (Unusual Activity)
**URL Addition**: `&o=-relativevolume`
- Prioritizes stocks with volume spikes
- Finds unusual institutional activity
- Good for catching early moves

### Option 4: Sort by Volume (Most Liquid)
**URL Addition**: `&o=-volume`
- Prioritizes most actively traded stocks
- Better liquidity for entries/exits
- Lower slippage risk

## Recommended Fix

**For RSI Mean Reversion Strategy**, use Option 2:

**New URL**:
```
https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o750,sh_price_u20,ta_rsi_os40&o=rsi&auth=...
```

This sorts results by RSI value (lowest first), ensuring the AI analyzes the MOST oversold stocks, not just the alphabetically-first ones.

## Alternative: Random Sampling

If you want diversity without bias:
1. Fetch all results (no sort parameter)
2. Randomly shuffle the list before AI analysis
3. Limit to top N stocks after shuffle

## Implementation

Update `.env` file:
```bash
# Add Finviz Elite auth key (get from finviz.com)
FINVIZ_AUTH_KEY=your_auth_key_here

# Update screener URL with sort parameter (auth will be added automatically)
FINVIZ_SCREENER_URL=https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o750,sh_price_u20,ta_rsi_os40&o=rsi
```

Or for momentum-focused trading:
```bash
FINVIZ_SCREENER_URL=https://finviz.com/screener.ashx?v=111&f=sh_avgvol_o750,sh_price_u20,ta_rsi_os40&o=-change
```

## Verification

After updating, check `screened_stocks.json` to confirm tickers are no longer all "A" stocks.

## Additional Considerations

1. **Pagination**: Finviz may limit results per page - current code doesn't handle pagination
2. **Result Limit**: May want to limit AI analysis to top 20-30 stocks (currently processes all)
3. **Sorting Strategy**: Different strategies may benefit from different sorts:
   - RSI Mean Reversion → Sort by RSI ascending (`o=rsi`)
   - Momentum Breakout → Sort by performance descending (`o=-change`)
   - Bollinger Mean Reversion → Sort by distance from bands (not available in Finviz)
