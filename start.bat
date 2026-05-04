@echo off
echo ============================================
echo   AI Workflow Automation System — Start
echo ============================================

echo.
echo [1/3] Setting up backend...
cd backend

if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

call venv\Scripts\activate

echo Installing dependencies...
pip install -r requirements.txt --quiet

if not exist ".env" (
    echo Creating .env from example...
    copy .env.example .env
)

echo Seeding demo data...
python -m scripts.seed_data

echo.
echo [2/3] Starting backend server (http://localhost:8000)...
start "Backend" cmd /k "call venv\Scripts\activate && uvicorn app.main:app --reload --port 8000"

cd ..\frontend

echo.
echo [3/3] Setting up frontend...
if not exist "node_modules" (
    echo Installing npm packages (this may take a minute)...
    npm install
)

echo Starting frontend (http://localhost:5173)...
start "Frontend" cmd /k "npm run dev"

cd ..

echo.
echo ============================================
echo   Both servers are starting up!
echo   Backend:  http://localhost:8000
echo   Frontend: http://localhost:5173
echo   API Docs: http://localhost:8000/docs
echo ============================================
echo.
echo Press any key to exit this window (servers keep running)
pause > nul
