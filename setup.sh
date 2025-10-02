#!/bin/bash
# Setup script for Podcast Search System

set -e  # Exit on any error

echo "🚀 Podcast Search System - Setup"
echo "================================="

# Check Python version
echo "🐍 Checking Python version..."
python3 --version

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv .venv

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Install dependencies
echo "📚 Installing dependencies..."
pip install -r requirements.txt

# Test basic functionality
echo "🧪 Running basic tests..."
python -m pytest tests/test_parse.py tests/test_chunk.py tests/test_rank.py -v

echo ""
echo "✅ Setup completed successfully!"
echo ""
echo "📋 Next steps:"
echo "1. Activate virtual environment:"
echo "   source .venv/bin/activate"
echo ""
echo "2. Update podcast data:"
echo "   python -m app.cli update"
echo ""
echo "3. Start web interface:"
echo "   uvicorn app.api:app --reload --port 8000"
echo ""
echo "4. Or use CLI search:"
echo '   python -m app.cli search "relativity"'
echo ""
echo "🌐 Web interface will be available at: http://localhost:8000"
