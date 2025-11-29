@echo off
echo ========================================
echo  Starting Heart Gym ML Production
echo ========================================
echo.

REM Check if Docker is running
docker ps >nul 2>&1
if errorlevel 1 (
    echo ERROR: Docker is not running!
    echo Please start Docker Desktop and try again.
    pause
    exit /b 1
)

echo [1/4] Starting Airflow (Docker)...
cd airflow
start /min docker compose up
cd ..
echo Waiting for Airflow to start...
timeout /t 20 >nul

echo.
echo [2/4] Starting Grafana (Docker)...
start /min docker compose -f docker-compose-grafana.yaml up

echo.
echo [3/4] Starting FastAPI...
start "FastAPI - Heart Gym" cmd /k "uvicorn fastapi_service.main:app --reload"
timeout /t 5 >nul

echo.
echo [4/4] Starting Streamlit...
start "Streamlit - Heart Gym" cmd /k "streamlit run streamlit/app.py"

echo.
echo ========================================
echo  All Services Started!
echo ========================================
echo.
echo Access your applications:
echo.
echo  - FastAPI:    http://localhost:8000/docs
echo  - Streamlit:  http://localhost:8501
echo  - Airflow:    http://localhost:8080 (user: airflow, pass: airflow)
echo  - Grafana:    http://localhost:3000 (user: admin, pass: admin)
echo.
echo New terminal windows have been opened for FastAPI and Streamlit.
echo Keep those windows open to keep the services running.
echo.
echo To stop all services, run: STOP_ALL.bat
echo.
pause
