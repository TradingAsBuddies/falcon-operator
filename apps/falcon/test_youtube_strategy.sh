#!/bin/bash
# Test YouTube Strategy Extraction
# Usage: ./test_youtube_strategy.sh "https://www.youtube.com/watch?v=VIDEO_ID"

set -e

YOUTUBE_URL="${1:-}"

if [ -z "$YOUTUBE_URL" ]; then
    echo "=========================================="
    echo "YouTube Strategy Extraction Test"
    echo "=========================================="
    echo ""
    echo "Usage: ./test_youtube_strategy.sh 'YOUTUBE_URL'"
    echo ""
    echo "Example trading strategy videos to try:"
    echo ""
    echo "Popular Trading Channels:"
    echo "  - Warrior Trading (Ross Cameron)"
    echo "  - SMB Capital"
    echo "  - Rayner Teo"
    echo "  - TraderTV Live"
    echo "  - Adam Khoo"
    echo ""
    echo "Find a video about a specific trading strategy,"
    echo "then run this script with the YouTube URL."
    echo ""
    echo "=========================================="
    exit 1
fi

echo "=========================================="
echo "Testing YouTube Strategy Extraction"
echo "=========================================="
echo ""
echo "URL: $YOUTUBE_URL"
echo ""

# Source environment variables
if [ -f ~/.local/.env ]; then
    echo "[1/5] Loading environment variables..."
    source ~/.local/.env
    if [ -n "$CLAUDE_API_KEY" ]; then
        echo "      ✓ Claude API key found"
    else
        echo "      ✗ Claude API key not found in ~/.local/.env"
        exit 1
    fi
else
    echo "      ✗ ~/.local/.env not found"
    exit 1
fi

# Change to project directory
cd /home/ospartners/src/falcon

echo ""
echo "[2/5] Extracting video ID..."
VIDEO_ID=$(python3 -c "
import sys
sys.path.insert(0, '.')
from youtube_strategies import YouTubeStrategyExtractor
extractor = YouTubeStrategyExtractor()
print(extractor.extract_video_id('$YOUTUBE_URL'))
" 2>/dev/null)
echo "      Video ID: $VIDEO_ID"

echo ""
echo "[3/5] Fetching transcript..."
echo "      (This may take a few seconds...)"

echo ""
echo "[4/5] Analyzing with Claude AI..."
echo "      (This will take 10-30 seconds...)"

echo ""
echo "[5/5] Extracting strategy and saving to database..."

# Run the extraction
python3 youtube_strategies.py "$YOUTUBE_URL"

echo ""
echo "=========================================="
echo "Extraction Complete!"
echo "=========================================="
echo ""
echo "View your strategy at:"
echo "  Web: https://localhost/strategies.html"
echo "  API: curl -k https://localhost/api/youtube-strategies"
echo ""
