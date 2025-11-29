# Heart Gym ML Production - Quick Start Guide

## 🚀 One-Command Startup

### To Start Everything:
```bash
START_ALL.bat
```

This single command will:
1. ✅ Start Airflow (Docker containers)
2. ✅ Start Grafana (Docker)
3. ✅ Start FastAPI (new terminal window)
4. ✅ Start Streamlit (new terminal window)

**Wait 30 seconds**, then access:
- **FastAPI**: http://localhost:8000/docs
- **Streamlit**: http://localhost:8501
- **Airflow**: http://localhost:8080 (user: `airflow`, pass: `airflow`)
- **Grafana**: http://localhost:3000 (user: `admin`, pass: `admin`)

---

## 🛑 One-Command Shutdown

### To Stop Everything:
```bash
STOP_ALL.bat
```

This will gracefully shut down all services.

---

## 📋 What's Running?

After startup, you'll see:
- **2 new terminal windows**: FastAPI and Streamlit (keep them open!)
- **Docker containers**: Airflow (6 containers) + Grafana (1 container)

---

## 🔍 Quick Health Check

Verify all services are running:

```bash
# Check Docker containers
docker ps

# Check FastAPI
curl http://localhost:8000/docs

# Check Streamlit
# Open browser: http://localhost:8501

# Check Airflow
# Open browser: http://localhost:8080

# Check Grafana
# Open browser: http://localhost:3000
```

---

## 📊 Demo Flow

1. **Open Streamlit**: http://localhost:8501
2. **Make a prediction**
3. **Check Grafana**: http://localhost:3000 - See real-time data
4. **Check Airflow**: http://localhost:8080 - See DAG runs

---

## 🔧 Troubleshooting

### Issue: Docker not running
**Solution**: Start Docker Desktop before running `START_ALL.bat`

### Issue: Port already in use
**Solution**: 
```bash
# Stop conflicting services
STOP_ALL.bat

# Or manually check and kill processes
netstat -ano | findstr :8000
netstat -ano | findstr :8501
```

### Issue: FastAPI/Streamlit window closes immediately
**Solution**: Check for Python errors in the terminal. Usually means dependencies missing:
```bash
pip install -r requirements.txt
```

---

## 📁 Project Structure

```
heart-gym-ml-prod/
├── START_ALL.bat           ← One-command startup
├── STOP_ALL.bat            ← One-command shutdown
├── fastapi_service/        ← API code
├── streamlit/              ← Web app code
├── airflow/dags/           ← Airflow DAGs
├── src/database.py         ← PostgreSQL models
├── expectations/           ← Great Expectations suite
└── monitoring/             ← Grafana setup docs
```

---

## 🎯 For Your Defense

**Startup Demo:**
1. Show stopping everything: `STOP_ALL.bat`
2. Show one-command startup: `START_ALL.bat`
3. Wait 30 seconds
4. Open all 4 URLs
5. Demo the complete flow

**This demonstrates:**
- ✅ Production-ready deployment
- ✅ Automated orchestration
- ✅ Microservices architecture
- ✅ Containerization (Docker)
- ✅ Real-time monitoring

---

## ⚡ Quick Commands Reference

```bash
# Start everything
START_ALL.bat

# Stop everything
STOP_ALL.bat

# View logs (in Docker terminal windows)
docker compose logs -f

# Restart just Airflow
cd airflow && docker compose restart && cd ..

# Restart just Grafana
docker compose -f docker-compose-grafana.yaml restart

# Check database
docker exec airflow-postgres-1 psql -U airflow -d airflow -c "\dt"
```

---

**That's it! One command to rule them all!** 🎉
