#!/bin/bash

# ==========================================
# Receipt App Single-Command Launcher
# ==========================================

echo "🚀 Starting Receipt Management System..."

# Function to check if a command exists
command_exists () {
    type "$1" &> /dev/null ;
}

# 1. Check prerequisites
echo "⏳ Checking prerequisites..."
if ! command_exists node ; then
    echo "❌ Error: Node.js is not installed. Please install Node.js first."
    exit 1
fi

if ! command_exists python3 ; then
    echo "❌ Error: Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# 2. Setup Backend (Django)
echo "----------------------------------------"
echo "🐍 Setting up Backend (Django)..."
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "📦 Creating Python virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install requirements
echo "📦 Installing Python dependencies..."
pip install -r requirements.txt

# Run migrations
echo "🗄️ Running database migrations..."
python manage.py migrate

cd ..

# 3. Setup Frontend (Next.js)
echo "----------------------------------------"
echo "⚛️  Setting up Frontend (Next.js)..."
cd frontend

# Install npm dependencies
echo "📦 Installing Node dependencies..."
npm install

cd ..

# 4. Start Servers
echo "----------------------------------------"
echo "🌟 Starting both servers..."

# Function to handle cleanup on script exit
cleanup() {
    echo "Stopping servers..."
    kill 0
}

# Catch Ctrl+C and run cleanup
trap cleanup EXIT

# Start backend in background
echo "-> Starting Django on http://localhost:8000"
cd backend
source venv/bin/activate
python manage.py runserver &
BACKEND_PID=$!
cd ..

# Start frontend in background
echo "-> Starting Next.js on http://localhost:3000"
cd frontend
npm run dev &
FRONTEND_PID=$!
cd ..

echo "✅ Both servers are running!"
echo "Press Ctrl+C to stop both servers."

# Wait for background processes to keep script alive
wait
