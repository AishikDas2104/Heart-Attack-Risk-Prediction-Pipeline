from fastapi import FastAPI
from pydantic import BaseModel
import pandas as pd
import joblib, json

app = FastAPI(title="Heart Attack Risk Prediction API")

MODEL_PATH = "data/models/heart_attack_risk_model.joblib"
SCALER_PATH = "data/models/scaler.joblib"
FEATURE_PATH = "data/models/feature_columns.json"

model = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
feature_columns = json.load(open(FEATURE_PATH, "r"))

# map-->
class Patient(BaseModel):
       
    Age: float | None = None
    Cholesterol: float | None = None
    Heart_rate: float | None = None
    Diabetes: float | None = None
    Smoking: float | None = None
    Obesity: float | None = None
    Alcohol_Consumption: float | None = None
    Exercise_Hours_Per_Week: float | None = None
    Previous_Heart_Problems: float | None = None
    Medication_Use: float | None = None
    Stress_Level: float | None = None
    Sedentary_Hours_Per_Day: float | None = None
    Income: float | None = None
    BMI: float | None = None
    Triglycerides: float | None = None
    Physical_Activity_Days_Per_Week: float | None = None
    Sleep_Hours_Per_Day: float | None = None
    Blood_sugar: float | None = None
    CK_MB: float | None = None
    Troponin: float | None = None

@app.get("/")
def home():
    return {"message": "Heart Attack Risk Prediction API is running"}

@app.post("/predict")
def predict(p: Patient):
   
    payload = {k: v for k, v in p.dict().items() if v is not None}
    row = pd.DataFrame([payload])
    row = row.reindex(columns=feature_columns, fill_value=0)
    row_scaled = scaler.transform(row)
    pred = model.predict(row_scaled)[0]
    return {"prediction": int(pred), "risk_level": "High Risk" if pred == 1 else "Low Risk"}
