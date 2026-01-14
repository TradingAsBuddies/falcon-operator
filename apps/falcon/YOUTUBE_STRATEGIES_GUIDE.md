# YouTube Trading Strategies Feature

## Overview

The Falcon platform now includes a YouTube strategy collection system that automatically extracts trading strategies from YouTube videos using AI analysis.

## Features

- **AI-Powered Extraction**: Uses Claude AI to analyze YouTube video transcripts and extract structured trading strategy information
- **Chart Fanatics-Style Layout**: Professional presentation similar to chartfanatics.com
- **Automatic Categorization**: Extracts tags, trading style, instruments, and performance metrics
- **Web Interface**: Browse, view, and submit strategies through the web UI

## How It Works

1. **Submit YouTube URL**: Paste any YouTube video URL containing trading strategy content
2. **AI Analysis**: Claude AI extracts:
   - Strategy overview
   - Trading style (day trading, swing trading, etc.)
   - Instruments (stocks, options, futures, etc.)
   - Entry and exit rules
   - Risk management approach
   - Strategy code (if mentioned)
   - Tags and categories
   - Pros and cons
3. **Database Storage**: Strategy is saved to SQLite database
4. **Web Display**: View strategy in Chart Fanatics-style layout

## Access Points

### Web Interface
- **All Strategies**: https://your-pi-ip/strategies.html
- **Individual Strategy**: https://your-pi-ip/strategy-view.html?id=STRATEGY_ID
- **Main Dashboard**: https://your-pi-ip/

### API Endpoints
- `GET /api/youtube-strategies` - List all strategies
- `GET /api/youtube-strategies/<id>` - Get specific strategy
- `POST /api/youtube-strategies/submit` - Submit YouTube URL for extraction

## CLI Usage

You can also use the command-line tool directly:

```bash
python3 youtube_strategies.py "https://www.youtube.com/watch?v=VIDEO_ID"
```

## Example API Request

### Submit YouTube URL
```bash
curl -k -X POST https://localhost/api/youtube-strategies/submit \
  -H "Content-Type: application/json" \
  -d '{"youtube_url": "https://www.youtube.com/watch?v=VIDEO_ID"}'
```

### Get All Strategies
```bash
curl -k https://localhost/api/youtube-strategies
```

### Get Specific Strategy
```bash
curl -k https://localhost/api/youtube-strategies/1
```

## Database Schema

Strategies are stored in `paper_trading.db` with the following fields:

- **title**: Strategy name
- **creator**: Video creator/channel name
- **youtube_url**: Original video URL
- **video_id**: YouTube video ID
- **strategy_overview**: Brief description of the strategy
- **trading_style**: Day trading, swing trading, etc.
- **instruments**: Stocks, options, futures, etc.
- **entry_rules**: When to enter trades
- **exit_rules**: When to exit trades
- **risk_management**: Risk control approach
- **strategy_code**: Python/Pine Script code (if mentioned)
- **tags**: Array of category tags
- **performance_metrics**: Win rate, profit factor, etc.
- **pros**: Strategy advantages
- **cons**: Strategy limitations

## Requirements

- Claude API key (stored in ~/.local/.env as CLAUDE_API_KEY)
- YouTube videos must have captions/transcripts enabled
- Internet connection for fetching transcripts

## Technical Details

### Components

1. **youtube_strategies.py**: Core extraction logic
   - `YouTubeStrategyDB`: Database operations
   - `YouTubeStrategyExtractor`: AI-powered extraction

2. **dashboard_server.py**: Flask API endpoints
   - `/api/youtube-strategies`: CRUD operations
   - Automatic initialization with Claude API key

3. **www/strategies.html**: Strategy listing page
4. **www/strategy-view.html**: Individual strategy display

### AI Extraction Pattern

The system uses a fabric-style "extract_wisdom" pattern that analyzes:
- Strategy methodology
- Entry/exit criteria
- Risk management rules
- Performance expectations
- Code examples
- Strengths and weaknesses

## Tips for Best Results

1. **Choose Videos With Transcripts**: Videos with captions/transcripts work best
2. **Detailed Strategy Videos**: Longer, more detailed strategy explanations yield better results
3. **Code Mentions**: Videos that mention or display code will have it extracted
4. **Performance Data**: Videos citing win rates, profit factors, etc. will capture those metrics

## Troubleshooting

### "No transcript available" error
- Video doesn't have captions enabled
- Try a different video or enable captions if it's your channel

### "Claude API key not configured" error
- Ensure CLAUDE_API_KEY is set in ~/.local/.env
- Restart the falcon-dashboard service

### 403 Forbidden on web pages
- Check file permissions: `chmod 755 /home/ospartners/src/falcon/www/*.html`

## Future Enhancements

Potential additions:
- Backtest integration (automatic backtesting of extracted strategies)
- Strategy comparison tools
- Community ratings/comments
- Search and filter functionality
- Export to backtrader format
- Integration with active_strategy.py deployment

---

Built with Claude AI | Part of the Falcon Trading Platform
