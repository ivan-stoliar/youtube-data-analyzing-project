#!/bin/bash

echo "=================================="
echo "🎯 YouTube Niche Analyzer Dashboard"
echo "=================================="
echo ""

# Check if we're in the right directory
if [ ! -d "frontend" ] || [ ! -d "backend" ]; then
    echo "❌ Please run this script from the youtube-dashboard directory"
    exit 1
fi

# Check if Node.js is installed
if ! command -v node &> /dev/null; then
    echo "❌ Node.js is not installed"
    echo "Please install Node.js from: https://nodejs.org/"
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    echo "Please install Python 3.11+"
    exit 1
fi

echo "✅ Node.js: $(node --version)"
echo "✅ Python: $(python3 --version)"
echo ""

# Setup backend
echo "📦 Setting up backend..."
cd backend

if [ ! -d "venv" ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing Python dependencies..."
pip install -q -r requirements.txt

echo "✅ Backend ready!"
echo ""

cd ..

# Setup frontend
echo "📦 Setting up frontend..."
cd frontend

if [ ! -d "node_modules" ]; then
    echo "Installing Node dependencies..."
    npm install
else
    echo "Dependencies already installed"
fi

echo "✅ Frontend ready!"
echo ""

cd ..

# Ask how to start
echo "=================================="
echo "How would you like to start?"
echo "=================================="
echo "1) Start both (recommended)"
echo "2) Backend only"
echo "3) Frontend only"
echo ""
read -p "Choice (1-3): " choice

case $choice in
  1)
    echo ""
    echo "Starting backend on http://localhost:8000"
    echo "Starting frontend on http://localhost:5173"
    echo ""
    echo "Press Ctrl+C to stop both servers"
    echo ""

    # Start backend in background
    cd backend
    source venv/bin/activate
    python main.py &
    BACKEND_PID=$!
    cd ..

    # Wait a bit for backend to start
    sleep 3

    # Start frontend (foreground)
    cd frontend
    npm run dev

    # When frontend stops, kill backend
    kill $BACKEND_PID
    ;;

  2)
    echo ""
    echo "Starting backend on http://localhost:8000"
    cd backend
    source venv/bin/activate
    python main.py
    ;;

  3)
    echo ""
    echo "Starting frontend on http://localhost:5173"
    echo "Make sure backend is running on http://localhost:8000"
    cd frontend
    npm run dev
    ;;

  *)
    echo "Invalid choice"
    exit 1
    ;;
esac
