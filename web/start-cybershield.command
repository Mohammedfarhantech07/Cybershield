
#!/bin/bash

# CyberShield - macOS Launcher

cd "$(dirname "$0")"

echo "=================================="
echo "       CYBERSHIELD LAUNCHER"
echo "=================================="

# Check Python
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is not installed!"
    read -p "Press Enter to exit..."
    exit 1
fi

# Create virtual environment if missing
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate environment
source venv/bin/activate

# Upgrade pip
python -m pip install --upgrade pip

# Install requirements
if [ -f "requirements.txt" ]; then
    echo "Installing dependencies..."
    pip install -r requirements.txt
fi

echo ""
echo "Starting CyberShield..."
echo "=================================="

# Launch Streamlit if app.py uses Streamlit
if grep -q "import streamlit\|from streamlit" app.py 2>/dev/null; then
    python -m streamlit run app.py
else
    python app.py
fi

echo ""
echo "CyberShield stopped."
read -p "Press Enter to exit..."
