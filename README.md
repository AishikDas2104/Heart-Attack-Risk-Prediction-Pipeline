# Heart Attack Risk Prediction - MLOps Pipeline

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com/)
[![Airflow](https://img.shields.io/badge/Airflow-2.7+-red.svg)](https://airflow.apache.org/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-orange.svg)](https://streamlit.io/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-13+-blue.svg)](https://www.postgresql.org/)
[![Grafana](https://img.shields.io/badge/Grafana-Latest-orange.svg)](https://grafana.com/)

Production-grade **MLOps pipeline** for heart attack risk prediction featuring automated data ingestion, quality validation, scheduled predictions, and real-time monitoring dashboards.

---

## Project Overview

This project implements a complete **end-to-end machine learning system** following MLOps best practices. It demonstrates:

- **Automated Data Pipelines** - Continuous data ingestion with quality validation
- **Model Serving** - REST API for real-time predictions
- **Workflow Orchestration** - Scheduled batch predictions using Airflow
- **Real-Time Monitoring** - Grafana dashboards for data quality and model drift
- **User Interface** - Interactive web app for predictions and insights
- **Data Validation** - Great Expectations for robust quality checks
- **Production Ready** - Docker containerization with one-command deployment

---

## Architecture

```
┌─────────────┐
│  Raw Data   │ (CSV files)
└──────┬──────┘
       │
       ↓
┌──────────────────────────────────┐
│  Airflow - Ingestion DAG         │
│  • Validate data quality         │
│  • Save statistics to PostgreSQL │
│  • Move to good_data/bad_data    │
└───────┬──────────────────────────┘
        │
        ↓
┌─────────────┐    ┌────────────────────┐
│  good_data  │───→│ Airflow - Pred DAG │
└─────────────┘    │ • Batch predictions│
                   └─────────┬──────────┘
                             │
                             ↓
                   ┌─────────────────────┐
                   │   FastAPI Service   │
                   │   • /predict        │
                   │   • /past-predictions│
                   └──────────┬──────────┘
                              │
                              ↓
                   ┌──────────────────────┐
                   │  PostgreSQL Database │
                   │  • predictions       │
                   │  • ingestion_stats   │
                   │  • data_quality_issues│
                   └──────────┬───────────┘
                              │
              ┌───────────────┴────────────┐
              ↓                            ↓
     ┌────────────────┐         ┌──────────────────┐
     │   Streamlit    │         │     Grafana      │
     │   • UI         │         │  • Dashboards    │
     │   • Monitoring │         │  • Alerts        │
     └────────────────┘         └──────────────────┘
```

---

## Features

### Data Quality Monitoring
- **7+ validation checks**: Missing columns, null values, type mismatches, out-of-range values
- **Real-time dashboards**: Grafana panels showing data quality metrics
- **Automated alerts**: Notifications for critical data issues
- **Great Expectations integration**: Industry-standard validation framework

### ML Model Serving
- **REST API**: FastAPI with automatic Swagger documentation
- **Single & batch predictions**: Handle individual requests and bulk processing
- **Audit trail**: All predictions stored with features and timestamps
- **Source tracking**: Distinguish webapp vs scheduled predictions

### Automated Workflows
- **Data ingestion**: Processes files every minute with validation
- **Scheduled predictions**: Batch predictions every 2 minutes
- **Smart execution**: Skips runs when no new data available
- **Parallel processing**: Tasks execute concurrently for efficiency

### User Interface
- **Prediction page**: Interactive form for single predictions
- **Multi-prediction**: Upload CSV for batch processing
- **Past predictions**: Query historical predictions with filters
- **Monitoring dashboard**: Real-time data quality metrics

### Real-Time Monitoring
- **Dashboard 1 - Data Quality**: Ingestion stats, success rates, issue trends
- **Dashboard 2 - Model Performance**: Prediction distribution, data drift detection
- **Color-coded thresholds**: Green/Orange/Red visual indicators
- **Auto-refresh**: Updates every 10 seconds

---

## Tech Stack

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Orchestration** | Apache Airflow | Workflow scheduling and management |
| **API** | FastAPI | High-performance REST API |
| **Database** | PostgreSQL | Data persistence and querying |
| **UI** | Streamlit | Interactive web application |
| **Monitoring** | Grafana | Real-time dashboards and alerts |
| **Validation** | Great Expectations | Data quality framework |
| **ORM** | SQLAlchemy | Database abstraction layer |
| **Containerization** | Docker & Docker Compose | Service isolation and deployment |
| **ML Framework** | Scikit-learn | Model training and inference |

---

## Quick Start

### Prerequisites
- Docker Desktop installed and running
- Python 3.10+
- 8GB RAM minimum

### One-Command Deployment

```bash
# Clone repository
git clone https://github.com/AishikDas2104/Heart-Attack-Risk-Prediction-Pipeline.git
cd heart-gym-ml-prod

# Start all services
START_ALL.bat
```

**Wait 60 seconds**, then access:
- **Streamlit UI**: http://localhost:8501
- **API Docs**: http://localhost:8000/docs
- **Airflow**: http://localhost:8080 (user: `airflow`, pass: `airflow`)
- **Grafana**: http://localhost:3000 (user: `admin`, pass: `admin`)

---

## Detailed Setup

### Step 1: Install Dependencies

```bash
pip install -r requirements.txt
```

### Step 2: Initialize Database

```bash
python -c "from src.database import init_db; init_db()"
```

### Step 3: Prepare Demo Data

```bash
python python_script/split_dataset.py -d gym_members_exercise_tracking.csv -o airflow/dags/data/raw_data -n 3
```

### Step 4: Start Services

```bash
# Start Airflow
cd airflow && docker compose up -d && cd ..

# Start Grafana
docker compose -f docker-compose-grafana.yaml up -d

# Start FastAPI (in new terminal)
uvicorn fastapi_service.main:app --reload

# Start Streamlit (in new terminal)
streamlit run streamlit/app.py
```

---

## Project Structure

```
heart-gym-ml-prod/
├── airflow/                    # Airflow configuration
│   ├── dags/
│   │   ├── data-ingest.py     # Data ingestion DAG
│   │   └── dag2.py            # Prediction DAG
│   └── docker-compose.yaml
├── fastapi_service/            # API service
│   └── main.py
├── streamlit/                  # Web UI
│   ├── app.py
│   └── pages/
│       ├── prediction.py
│       ├── past_predictions.py
│       └── monitoring.py
├── src/                        # Core modules
│   ├── database.py            # Database models
│   └── ml_model.py            # ML model
├── expectations/               # Great Expectations
│   └── gym_data_quality_suite.json
├── monitoring/                 # Grafana configs
│   └── grafana_setup.md
├── notebooks/                  # Jupyter notebooks
│   ├── 01_eda.ipynb
│   └── 02_error_generation.ipynb
├── python_script/
│   └── split_dataset.py       # Data splitting utility
├── START_ALL.bat              # One-command startup
├── STOP_ALL.bat               # Shutdown script
└── requirements.txt
```

---

## Usage Examples

### Make a Prediction via API

```bash
curl -X POST http://localhost:8000/predict \
  -H "Content-Type: application/json" \
  -d '{
    "age": 35,
    "gender": "male",
    "duration": 60,
    "heart_rate": 125,
    "body_temp": 98.6
  }'
```

**Response:**
```json
{
  "prediction": "Medium",
  "risk_score": 0.52,
  "timestamp": "2025-11-29T10:30:00"
}
```

### Query Past Predictions

```bash
curl http://localhost:8000/past-predictions?source=webapp&limit=10
```

### Trigger DAG Manually

```bash
# Via Airflow UI
http://localhost:8080 → DAGs → data_ingestion_job → Trigger DAG

# Via CLI
docker exec airflow-airflow-scheduler-1 airflow dags trigger data_ingestion_job
```

---

## Grafana Dashboards

### Dashboard 1: Ingested Data Monitoring
- **Valid vs Invalid Data** (Time series)
- **Success Rate** (Gauge: 0-100%)
- **Data Quality Issues by Type** (Bar chart)
- **Recent Ingestions** (Table)

### Dashboard 2: Model Performance & Data Drift
- **Prediction Distribution** (Pie chart)
- **Average Age Drift** (Time series with baseline)
- **Prediction Activity** (Stacked bars)
- **Feature Drift Detection** (Table)

---

## Running Tests

```bash
# Validate data quality
python utils/ge_validator.py

# Generate HTML validation report
start validation_report.html

# Check database records
docker exec airflow-postgres-1 psql -U airflow -d airflow -c "SELECT * FROM predictions LIMIT 5;"

# Verify file processing
dir airflow\dags\data\good_data
dir airflow\dags\data\bad_data
```

---

## Configuration

### Environment Variables

Create `.env` file:

```env
DATABASE_URL=postgresql://airflow:airflow@localhost:5432/airflow
AIRFLOW_UID=50000
API_HOST=0.0.0.0
API_PORT=8000
```

### Airflow Configuration

- **Scheduler Interval**: Data ingestion every 1 minute, predictions every 2 minutes
- **Executor**: LocalExecutor
- **Database**: PostgreSQL
- **Authentication**: Username/password (airflow/airflow)

### Grafana Configuration

- **Data Source**: PostgreSQL (localhost:5432/airflow)
- **Auto-refresh**: 10 seconds
- **Retention**: 30 days

---

## Monitoring & Alerts

### Grafana Alerts (Configurable)

- **Data Quality Degradation**: When success rate < 80%
- **High Error Rate**: When invalid rows > 20%
- **Prediction Imbalance**: When single class > 90%
- **Data Drift Detected**: When feature averages deviate > 20%
- **Zero Predictions**: When no predictions for 10 minutes

### Airflow Alerts

- **DAG Failures**: Email notifications (configure in airflow.cfg)
- **Task Retries**: Automatic retries with exponential backoff
- **SLA Misses**: Track task duration violations

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

---

## Authors

**Aishik Das**
- GitHub: [@AishikDas2104](https://github.com/AishikDas2104)
- LinkedIn: [Aishik Das](https://www.linkedin.com/in/aishik-das)

---

## Acknowledgments

- Dataset: Gym Members Exercise Tracking Dataset
- MLOps Course: Data Science in Production
- Technologies: Apache Software Foundation, FastAPI, Streamlit, Grafana

---

## Support

For questions and support:
- Email: your.email@example.com
- Issues: [GitHub Issues](https://github.com/AishikDas2104/    Heart-Attack-Risk-Prediction-Pipeline/issues)
- Discussions: [GitHub Discussions](https://github.com/AishikDas2104/Heart-Attack-Risk-Prediction-Pipeline/discussions)

---

## Project Highlights

This project demonstrates:
- **Production-grade architecture** with microservices
- **Automated CI/CD workflow** using Airflow
- **Data quality validation** with Great Expectations
- **Real-time monitoring** with Grafana dashboards
- **API-first design** with FastAPI and Swagger
- **User-friendly interface** with Streamlit
- **Containerized deployment** with Docker
- **Scalable database** with PostgreSQL

**Perfect for demonstrating MLOps skills!** 🚀

---

<div align="center">

**Star this repository if you found it helpful!**

Made with for the MLOps community

</div>
