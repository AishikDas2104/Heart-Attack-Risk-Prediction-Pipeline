@echo off
echo ========================================
echo  Complete Production Setup
echo ========================================
echo.

echo [Step 1/5] Restarting Airflow with PostgreSQL port exposed...
cd airflow
docker compose down
timeout /t 3 >nul
docker compose up -d
cd ..
echo Waiting for containers to start...
timeout /t 30 >nul

echo.
echo [Step 2/5] Installing Python dependencies...
pip install psycopg2-binary great-expectations --quiet

echo.
echo [Step 3/5] Initializing PostgreSQL tables...
python -c "from src.database import init_db; init_db()"

echo.
echo [Step 4/5] Restarting FastAPI with PostgreSQL...
echo Please restart FastAPI manually with: uvicorn fastapi_service.main:app --reload

echo.
echo [Step 5/5] Starting Grafana...
docker compose -f docker-compose-grafana.yaml up -d

echo.
echo ========================================
echo  Setup Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Restart FastAPI: uvicorn fastapi_service.main:app --reload
echo 2. Configure Grafana at http://localhost:3000
echo    - Add PostgreSQL data source
echo    - Host: localhost:5432
echo    - Database: airflow
echo    - User: airflow
echo    - Password: airflow
echo.
echo 3. Create Grafana dashboards using queries from FULL_SETUP_GUIDE.md
echo.
pause
