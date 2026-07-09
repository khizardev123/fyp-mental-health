#!/bin/bash
echo "🚀 Starting SereneMind Services Locally (No-DB Mode)"
echo "----------------------------------------------------"

# Clean up any previously running instances
pkill -f "node.*auth-service" || true
pkill -f "node.*journal-service" || true
pkill -f "uvicorn.*main:app" || true
pkill -f "next.*dev" || true

# Services are now stateless and mocked in frontend where appropriate.
# Only starting core ML and Avatar services.




# 4. Start AI Service
echo "Starting AI Service on port 8000..."
cd services/ai-service
../../ml/venv/bin/pip install -r requirements.txt > /dev/null 2>&1
PYTHONPATH=. ../../ml/venv/bin/uvicorn main:app --port 8000 &
cd ../..

# 4b. Start Avatar Service
echo "Starting Avatar Service on port 8001..."
cd services/avatar-service
../../ml/venv/bin/pip install -r requirements.txt > /dev/null 2>&1
../../ml/venv/bin/uvicorn main:app --port 8001 &
cd ../..

# 5. Start Frontend
echo "Starting Frontend on port 3000..."
cd frontend
npm install > /dev/null 2>&1
NEXT_PUBLIC_API_URL=http://localhost:3000/api npm run dev &
cd ..

echo "----------------------------------------------------"
echo "✅ All services are starting up in the background."
echo "⏳ Wait ~10 seconds for servers to initialize, then open http://localhost:3000"
echo "🛑 To stop them all, run: pkill -f node && pkill -f uvicorn"
