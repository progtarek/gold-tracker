#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

SESSION_NAME="gold-tracker"

# Check for .env
if [ ! -f .env ]; then
    echo "No .env file found!"
    echo "  cp .env.example .env"
    echo "  nano .env  # add your GOLDAPI_KEY from goldapi.io"
    exit 1
fi

# Create venv if needed
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "Installing dependencies..."
pip install -q -r requirements.txt

# Check if already running
if tmux has-session -t "$SESSION_NAME" 2>/dev/null; then
    echo "Gold tracker is already running in tmux session '$SESSION_NAME'."
    echo ""
    echo "  Attach:  tmux attach -t $SESSION_NAME"
    echo "  Stop:    tmux kill-session -t $SESSION_NAME"
    exit 0
fi

# Start in tmux
echo "Starting gold tracker in tmux session '$SESSION_NAME'..."
tmux new-session -d -s "$SESSION_NAME" "cd $SCRIPT_DIR && source venv/bin/activate && python scheduler.py; echo 'Press enter to close.'; read"

echo ""
echo "Gold tracker is running!"
echo ""
echo "  Attach to see logs:  tmux attach -t $SESSION_NAME"
echo "  Detach from tmux:    Ctrl+B then D"
echo "  Stop the tracker:    tmux kill-session -t $SESSION_NAME"
