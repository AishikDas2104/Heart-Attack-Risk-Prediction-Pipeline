# Grafana Monitoring Setup

This guide explains how to set up the monitoring dashboards for the Data Science in Production project.

## Prerequisites
- Grafana installed and running (e.g., via Docker or local install).
- PostgreSQL/SQLite database connected to Grafana.

## Database Connection
1. Open Grafana (usually `http://localhost:3000`).
2. Go to **Configuration** > **Data Sources**.
3. Add a new data source:
   - **Type**: PostgreSQL (or SQLite if using a plugin, but Postgres is recommended for production).
   - **Host**: `localhost:5432` (or your DB host).
   - **Database**: `predictions_db`.
   - **User/Password**: Your DB credentials.
4. Click **Save & Test**.

## Dashboard 1: Ingested Data Monitoring
**Target Audience**: Data Operations Team
**Goal**: Monitor data quality issues.

### Panels

#### 1. Data Quality Overview (Last 10 min)
- **Type**: Stat / Gauge
- **Query**:
  ```sql
  SELECT 
    sum(valid_rows) as valid, 
    sum(invalid_rows) as invalid 
  FROM ingestion_stats 
  WHERE timestamp > now() - interval '10 minutes'
  ```
- **Visualization**: Show % of invalid rows.

#### 2. Invalid Data Trend
- **Type**: Time Series
- **Query**:
  ```sql
  SELECT 
    timestamp, 
    (invalid_rows::float / total_rows) * 100 as invalid_percentage 
  FROM ingestion_stats
  WHERE timestamp > $__timeFrom()
  ```
- **Thresholds**: Green < 5%, Orange < 20%, Red > 20%.

#### 3. Data Issues by Type
- **Type**: Bar Chart
- **Query**:
  ```sql
  SELECT 
    issue_type, 
    sum(count) as total_issues 
  FROM data_quality_issues 
  JOIN ingestion_stats ON data_quality_issues.ingestion_stat_id = ingestion_stats.id
  WHERE timestamp > $__timeFrom()
  GROUP BY issue_type
  ```

#### 4. Missing Values Over Time
- **Type**: Time Series
- **Query**:
  ```sql
  SELECT 
    timestamp, 
    count 
  FROM data_quality_issues 
  JOIN ingestion_stats ON data_quality_issues.ingestion_stat_id = ingestion_stats.id
  WHERE issue_type = 'Missing Values' AND timestamp > $__timeFrom()
  ```

---

## Dashboard 2: Model Monitoring
**Target Audience**: ML Engineers / Data Scientists
**Goal**: Detect drift and model issues.

### Panels

#### 1. Prediction Distribution (Last 30 min)
- **Type**: Histogram / Bar Chart
- **Query**:
  ```sql
  SELECT 
    prediction, 
    count(*) 
  FROM predictions 
  WHERE timestamp > now() - interval '30 minutes'
  GROUP BY prediction
  ```

#### 2. Average Predicted Risk (if numerical) or Risk Level Counts
- **Type**: Time Series
- **Query**:
  ```sql
  SELECT 
    timestamp,
    CASE 
      WHEN prediction = 'Low' THEN 1 
      WHEN prediction = 'Medium' THEN 2 
      WHEN prediction = 'High' THEN 3 
    END as risk_score
  FROM predictions
  WHERE timestamp > $__timeFrom()
  ```

#### 3. Training vs Serving Drift (Age)
- **Type**: Time Series / Stat
- **Query**:
  ```sql
  SELECT 
    timestamp, 
    avg(age) as serving_avg_age 
  FROM predictions 
  WHERE timestamp > $__timeFrom()
  GROUP BY timestamp
  ```
- **Comparison**: Add a constant line for Training Avg Age (e.g., 45).

#### 4. Model Alerts
- **Type**: Alert List
- **Condition**: Trigger if `High` risk predictions > 80% of total predictions in last 5 minutes (Anomaly).

## Alerts
Set up Grafana alerts for:
1. **High Invalid Data**: If invalid rows > 50% in last 5 mins.
2. **Model Anomaly**: If model predicts same class 100% of time in last 10 mins.
