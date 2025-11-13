#!/bin/bash
#
# Start Next.js Dashboard Frontend
# Runs on http://localhost:3000
#

set -e

echo "🎨 Starting Comversa Executive Dashboard..."

cd "$(dirname "$0")/../dashboard" || exit 1

# Install dependencies if node_modules doesn't exist
if [ ! -d "node_modules" ]; then
    echo "📦 Installing frontend dependencies..."
    npm install
fi

# Start Next.js dev server
echo ""
echo "=" * 60
echo "🌐 Dashboard Starting..."
echo "=" * 60
echo "URL: http://localhost:3000"
echo "API: http://localhost:8000"
echo "=" * 60
echo ""

npm run dev
