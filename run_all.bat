@echo off
echo ==================================================
echo   AI CONTENT FACTORY - ONE-CLICK LAUNCHER
echo ==================================================
echo.

:: 1. Check Docker Desktop
echo [1/3] Checking Docker Desktop status...
docker info >nul 2>&1
if %errorlevel% neq 0 (
    echo [Error] Docker Desktop is not running!
    echo Please open Docker Desktop on your machine and press any key to retry.
    pause
    echo Retrying Docker check...
    docker info >nul 2>&1
    if %errorlevel% neq 0 (
        echo [Error] Still cannot connect to Docker. Exiting...
        pause
        exit /b 1
    )
)
echo Docker Desktop is running.

:: 2. Start PostgreSQL Container
echo [2/3] Starting PostgreSQL (pgvector) container...
docker start content-creator-db >nul 2>&1
if %errorlevel% neq 0 (
    echo Container not found or stopped. Launching new pgvector database...
    docker run --name content-creator-db -e POSTGRES_PASSWORD=postgres -p 5432:5432 -d pgvector/pgvector:pg16
) else (
    echo Database container content-creator-db started successfully.
)

:: 3. Launch Web UI Server
echo [3/3] Launching local Web UI server...
set PYTHONUTF8=1
start "AI Content Factory Server" cmd /k ".venv\Scripts\python.exe src/ui_server.py"

:: 4. Open Web Browser
echo.
echo Opening browser at http://localhost:8000 ...
timeout /t 3 /nobreak >nul
start http://localhost:8000

echo.
echo ==================================================
echo   LAUNCH COMPLETED! 
echo   Please use the console in your web browser.
echo ==================================================
pause
