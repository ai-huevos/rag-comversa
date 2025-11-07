#!/bin/bash
# Setup script for Intelligence Capture System

echo "🚀 Setting up Intelligence Capture System..."

# Check if .env exists
if [ ! -f .env ]; then
    echo ""
    echo "⚠️  No .env file found!"
    echo ""
    echo "Please create a .env file with your OpenAI API key:"
    echo "  1. Copy .env.example to .env"
    echo "  2. Add your OpenAI API key"
    echo ""
    echo "Example:"
    echo "  cp .env.example .env"
    echo "  # Then edit .env and add your key"
    echo ""
    exit 1
fi

# Activate virtual environment
echo "✓ Activating virtual environment..."
source venv/bin/activate

echo ""
echo "✅ Setup complete!"
echo ""
echo "You can now run:"
echo "  python intelligence_capture/run.py --test    # Test with one interview"
echo "  python intelligence_capture/run.py           # Process all interviews"
echo "  python intelligence_capture/run.py --stats   # Show database stats"
echo ""
