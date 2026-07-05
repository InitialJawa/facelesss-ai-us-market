#!/usr/bin/env bash
set -euo pipefail

echo "=== FACELess AI - Setup ==="

# Create virtual environment
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo "✓ Virtual environment created"
fi

source .venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt
echo "✓ Dependencies installed"

# Create .env from example if not exists
if [ ! -f ".env" ]; then
    cp .env.example .env
    echo "✓ .env created from .env.example — edit it with your keys"
fi

# Create directories
mkdir -p output assets voices logs brain/memory
echo "✓ Directories created"

# Init database
echo "Run this to init database:"
echo "  python -c 'import asyncio; from database.session import init_db; asyncio.run(init_db())'"

echo ""
echo "=== Setup complete! Run 'python main.py' to start ==="
