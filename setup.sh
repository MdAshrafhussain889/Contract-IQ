#!/bin/bash

# Document to Markdown Converter API - Setup Script

echo "🚀 Setting up Document to Markdown Converter API..."

# Check Python version
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "✓ Python version: $python_version"

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "⚙️  Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Check for Tesseract (optional but recommended for OCR)
echo ""
echo "🔍 Checking for Tesseract (required for scanned PDF support)..."
if command -v tesseract &> /dev/null; then
    tesseract_version=$(tesseract --version 2>&1 | head -1)
    echo "✓ Tesseract found: $tesseract_version"
else
    echo "⚠️  Tesseract not found. Installing..."
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install tesseract
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install tesseract-ocr
    else
        echo "❌ Please install Tesseract manually from: https://github.com/UB-Mannheim/tesseract/wiki"
    fi
fi

# Temp directory (auto-created by the app on first run)
echo "📁 tempfolder/ (uploads + markdown) is auto-created by the app on first run"

echo ""
echo "✅ Setup complete!"
echo ""
echo "🚀 To start the API, run:"
echo "   python main.py"
echo ""
echo "📖 API will be available at: http://localhost:8000"
echo "📚 API docs at: http://localhost:8000/docs"
