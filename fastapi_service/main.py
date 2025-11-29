# main.py
from fastapi import FastAPI, Depends, HTTPException
from pydantic import BaseModel
import random
import sys
import os
from typing import List, Optional
from datetime import datetime

# Add the root directory to sys.path to allow importing from src
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database import init_db, get_db, Prediction
from sqlalchemy.orm import Session

app = FastAPI(title="Heart Attack Prediction API", version="1.0")

# Initialize DB on startup
@app.on_event("startup")
def on_startup():
    init_db()

# --- Define Input Schema ---
class HeartInput(BaseModel):
    age: int
    gender: str
    duration: float
    heart_rate: int
    body_temp: float

class PredictionResponse(BaseModel):
    input_data: dict
    prediction: str
    timestamp: datetime

# --- Root Endpoint ---
@app.get("/")
def root():
    return {
        "message": "✅ Heart Attack Prediction API is running!",
        "usage": "Send a POST request to /predict with age, gender, duration, heart_rate, and body_temp."
    }


# --- Predict Endpoint ---
from typing import Union

@app.post("/predict")
def predict(data: Union[HeartInput, List[HeartInput]], source: str = "webapp", db: Session = Depends(get_db)):
    # Normalize to list
    if isinstance(data, HeartInput):
        data_list = [data]
        is_batch = False
    else:
        data_list = data
        is_batch = True

    results = []
    risk_levels = ["Low", "Medium", "High"]
    
    for item in data_list:
        # Dummy prediction logic
        risk = random.choice(risk_levels)
        
        # Save to DB
        db_prediction = Prediction(
            source=source,
            age=item.age,
            gender=item.gender,
            duration=item.duration,
            heart_rate=item.heart_rate,
            body_temp=item.body_temp,
            prediction=risk,
            input_data=item.dict()
        )
        db.add(db_prediction)
        results.append({
            "input_data": item.dict(),
            "prediction": risk,
            "timestamp": datetime.utcnow() # Use current time for response
        })
    
    db.commit()
    
    if not is_batch:
        return results[0]
    return results

# --- Past Predictions Endpoint ---
@app.get("/past-predictions")
def get_past_predictions(
    start_date: Optional[datetime] = None, 
    end_date: Optional[datetime] = None, 
    source: Optional[str] = None,
    db: Session = Depends(get_db)
):
    query = db.query(Prediction)
    
    if start_date:
        query = query.filter(Prediction.timestamp >= start_date)
    if end_date:
        query = query.filter(Prediction.timestamp <= end_date)
    if source and source != "all":
        query = query.filter(Prediction.source == source)
        
    predictions = query.all()
    
    return [
        {
            "id": p.id,
            "timestamp": p.timestamp,
            "source": p.source,
            "prediction": p.prediction,
            "features": p.input_data
        }
        for p in predictions
    ]
