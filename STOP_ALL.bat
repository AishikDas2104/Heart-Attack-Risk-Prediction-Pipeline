@echo off
echo ========================================
echo  Stopping Heart Gym ML Production
echo ========================================
echo.

echo [1/3] Stopping Streamlit and FastAPI...
taskkill /FI "WINDOWTITLE eq FastAPI*" /T /F 2>nul
taskkill /FI "WINDOWTITLE eq Streamlit*" /T /F 2>nul

echo.
echo [2/3] Stopping Grafana...
docker compose -f docker-compose-grafana.yaml down

echo.
echo [3/3] Stopping Airflow...
cd airflow
docker compose down
cd ..

echo.
echo ========================================
echo  All Services Stopped!
echo ========================================
echo.
pause
