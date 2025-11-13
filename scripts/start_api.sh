#!/bin/bash
#
# Start FastAPI Backend Server
# Runs on http://localhost:8000
#

set -e

echo "🚀 Starting Comversa Executive Dashboard API..."

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
    echo "✓ Virtual environment activated"
fi

# Check DATABASE_URL is set
if [ -z "$DATABASE_URL" ]; then
    echo "⚠️  DATABASE_URL not set, using default: postgresql://postgres@localhost:5432/comversa_rag"
    export DATABASE_URL="postgresql://postgres@localhost:5432/comversa_rag"
fi

# Install dependencies if needed
if ! python3 -c "import fastapi" 2>/dev/null; then
    echo "📦 Installing API dependencies..."
    pip3 install -r api/requirements.txt
fi

# Start the server
echo ""
echo "=" * 60
echo "📡 API Server Starting..."
echo "=" * 60
echo "Docs: http://localhost:8000/api/docs"
echo "Dashboard Endpoint: http://localhost:8000/api/dashboard"
echo "=" * 60
echo ""

cd "$(dirname "$0")/.." || exit 1

python3 -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload
