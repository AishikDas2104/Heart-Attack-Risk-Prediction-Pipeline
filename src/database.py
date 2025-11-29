from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSON as PostgresJSON
from sqlalchemy import JSON as GenericJSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# Use PostgreSQL from Airflow's Docker (port now exposed!)
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://airflow:airflow@localhost:5432/airflow"
)

# Use appropriate JSON type based on database
JSON = PostgresJSON if "postgresql" in DATABASE_URL else GenericJSON

Base = declarative_base()

class Prediction(Base):
    __tablename__ = "predictions"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    source = Column(String)  # 'webapp' or 'scheduled'
    
    # Features
    age = Column(Integer)
    gender = Column(String)
    duration = Column(Float)
    heart_rate = Column(Integer)
    body_temp = Column(Float)
    
    # Prediction
    prediction = Column(String)  # 'Low', 'Medium', 'High'
    
    # Store full input as JSON
    input_data = Column(JSON)

class IngestionStats(Base):
    __tablename__ = "ingestion_stats"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    filename = Column(String)
    total_rows = Column(Integer)
    valid_rows = Column(Integer)
    invalid_rows = Column(Integer)
    
    # Relationship to issues
    issues = relationship("DataQualityIssue", back_populates="ingestion_stat")

class DataQualityIssue(Base):
    __tablename__ = "data_quality_issues"

    id = Column(Integer, primary_key=True, index=True)
    ingestion_stat_id = Column(Integer, ForeignKey("ingestion_stats.id"))
    issue_type = Column(String)  # e.g., 'Missing Values', 'Out of Range'
    column_name = Column(String)
    criticality = Column(String) # 'High', 'Medium', 'Low'
    count = Column(Integer) # Number of rows with this issue
    
    ingestion_stat = relationship("IngestionStats", back_populates="issues")

# Database Connection
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}
)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def init_db():
    """Initialize database tables"""
    Base.metadata.create_all(bind=engine)
    print(f"✅ Database initialized at {DATABASE_URL}")

def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
