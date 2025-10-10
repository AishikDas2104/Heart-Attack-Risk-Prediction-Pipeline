
import streamlit as st
import pandas as pd
import numpy as np
import os
import requests
from datetime import datetime

# ---------- Config ----------
PREDICTIONS_STORE = "C:/dsp-alaa-bhakti/heart-gym-ml-prod/streamlit/predictions_store.csv"  # where we save demo predictions
DEFAULT_API_URL = "http://localhost:8000"  # change when your FastAPI is ready

# Features we'll accept (based on your dataset)
FEATURES = [
    "Age", "Gender", "Weight (kg)", "Height (m)", "Max_BPM", "Avg_BPM", "Resting_BPM",
    "Session_Duration (hours)", "Calories_Burned", "Workout_Type", "Fat_Percentage",
    "Water_Intake (liters)", "Workout_Frequency (days/week)", "Experience_Level", "BMI"
]

# ---------- Helper functions ----------
def sigmoid(x):
    return 1 / (1 + np.exp(-x))

def dummy_model_predict(row):
    """
    A simple deterministic 'risk' heuristic for demo purposes.
    Combines Age, Resting_BPM, Max_BPM, BMI and Fat_Percentage into a score and
    passes through a sigmoid to create a pseudo-probability of 'heart attack in gym'.
    """
    # Safely read features with defaults
    age = float(row.get("Age", 40))
    resting = float(row.get("Resting_BPM", 60))
    max_bpm = float(row.get("Max_BPM", 170))
    bmi = float(row.get("BMI", 24))
    fat = float(row.get("Fat_Percentage", 25))

    # center variables around typical values to avoid huge magnitude changes
    score = 0.03*(age - 40) + 0.04*(resting - 60) + 0.02*(max_bpm - 170) + 0.05*(bmi - 24) + 0.03*(fat - 25)
    prob = float(sigmoid(score))
    label = "high_risk" if prob >= 0.5 else "low_risk"
    return prob, label

def predict_records(records, use_api=False, api_url=DEFAULT_API_URL):
    """
    records: list of dicts (rows)
    returns: list of dicts with added 'prediction_prob' and 'prediction_label'
    """
    if use_api:
        try:
            resp = requests.post(f"{api_url.rstrip('/')}/predict", json={"data": records}, timeout=15)
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            st.error(f"API request failed: {e}")
            return None

    # Local dummy predictions
    out = []
    for r in records:
        prob, label = dummy_model_predict(r)
        newr = r.copy()
        newr["prediction_prob"] = prob
        newr["prediction_label"] = label
        out.append(newr)
    return out

def append_predictions_to_store(df_preds, source="webapp"):
    df = df_preds.copy()
    df["timestamp"] = datetime.utcnow().isoformat()
    df["source"] = source
    file_exists = os.path.exists(PREDICTIONS_STORE)
    df.to_csv(PREDICTIONS_STORE, mode="a", header=not file_exists, index=False)

def load_saved_predictions():
    if not os.path.exists(PREDICTIONS_STORE):
        return pd.DataFrame()
    return pd.read_csv(PREDICTIONS_STORE)

# ---------- Streamlit UI ----------
st.set_page_config(page_title="Gym Heart-Attack Risk — Demo", layout="wide")
st.title("Gym Heart-Attack Risk — Streamlit")

# Sidebar controls
st.sidebar.header("Settings")
mode = st.sidebar.selectbox("Prediction mode", ["Use local dummy model (no API)", "Call model API (FastAPI)"])
use_api = mode.startswith("Call")
api_url = st.sidebar.text_input("API base URL (if using API)", value=DEFAULT_API_URL if use_api else "")
st.sidebar.markdown("---")
st.sidebar.markdown("This demo saves predictions locally to `/dsp-alaa-bhakti/heart-gym-ml-prod/streamlit/predictions_store.csv`.")
st.sidebar.markdown("When your FastAPI is ready, switch to 'Call model API' and set the URL.")

page = st.sidebar.radio("Choose page", ["Make Predictions", "View Past Predictions"])

if page == "Make Predictions":
    st.header("Single-sample prediction (fill the form below)")
    with st.form("single_pred_form"):
        col1, col2, col3 = st.columns(3)
        with col1:
            Age = st.number_input("Age", min_value=10, max_value=100, value=40)
            Gender = st.selectbox("Gender", ["male", "female", "other"])
            Weight = st.number_input("Weight (kg)", min_value=30.0, max_value=200.0, value=75.0)
            Height = st.number_input("Height (m)", min_value=1.2, max_value=2.5, value=1.75)
            BMI = st.number_input("BMI (you can edit)", min_value=10.0, max_value=60.0, value=24.5)
        with col2:
            Max_BPM = st.number_input("Max_BPM", min_value=120, max_value=220, value=180)
            Avg_BPM = st.number_input("Avg_BPM", min_value=60, max_value=200, value=140)
            Resting_BPM = st.number_input("Resting_BPM", min_value=30, max_value=120, value=62)
            Session_Duration = st.number_input("Session_Duration (hours)", min_value=0.1, max_value=4.0, value=1.25, step=0.05)
        with col3:
            Calories = st.number_input("Calories_Burned", min_value=0, max_value=5000, value=900)
            Workout_Type = st.selectbox("Workout_Type", ["cardio", "strength", "mixed", "yoga", "other"])
            Fat_Percentage = st.slider("Fat_Percentage", min_value=5, max_value=50, value=26)
            Water_Intake = st.number_input("Water_Intake (liters)", min_value=0.0, max_value=10.0, value=2.6, step=0.1)
            Workout_Frequency = st.number_input("Workout_Frequency (days/week)", min_value=0, max_value=7, value=3)
            Experience_Level = st.selectbox("Experience_Level (1=beginner, 3=expert)", [1,2,3], index=1)

        submitted = st.form_submit_button("Predict single sample")
    if submitted:
        record = {
            "Age": Age, "Gender": Gender, "Weight (kg)": Weight, "Height (m)": Height,
            "Max_BPM": Max_BPM, "Avg_BPM": Avg_BPM, "Resting_BPM": Resting_BPM,
            "Session_Duration (hours)": Session_Duration, "Calories_Burned": Calories,
            "Workout_Type": Workout_Type, "Fat_Percentage": Fat_Percentage,
            "Water_Intake (liters)": Water_Intake, "Workout_Frequency (days/week)": Workout_Frequency,
            "Experience_Level": Experience_Level, "BMI": BMI
        }
        with st.spinner("Getting prediction..."):
            preds = predict_records([record], use_api=use_api, api_url=api_url if use_api else "")
        if preds is None:
            st.warning("Prediction failed — see messages above.")
        else:
            df_out = pd.DataFrame(preds)
            st.success("Prediction ready")
            st.dataframe(df_out.T)  # show transposed for single sample readability
            # Save prediction locally (demo)
            append_predictions_to_store(df_out, source="webapp")

    st.markdown("---")
    st.header("Batch prediction (upload CSV)")
    st.markdown("Upload a CSV with **columns matching** the feature names used in the form. "
                "If some columns are missing, the demo will fill sensible defaults.")
    uploaded = st.file_uploader("Upload CSV", type=["csv"])
    if uploaded is not None:
        try:
            df_in = pd.read_csv(uploaded)
            st.write("First rows of uploaded file:")
            st.dataframe(df_in.head())
            if st.button("Run batch prediction on uploaded file"):
                records = df_in.to_dict(orient="records")
                # fill missing features with defaults to avoid errors
                for r in records:
                    for feat in FEATURES:
                        if feat not in r:
                            # common defaults
                            defaults = {
                                "Age": 40, "Gender": "male", "Weight (kg)": 75, "Height (m)": 1.75,
                                "Max_BPM": 180, "Avg_BPM": 140, "Resting_BPM": 62,
                                "Session_Duration (hours)": 1.25, "Calories_Burned": 900, "Workout_Type": "mixed",
                                "Fat_Percentage": 26, "Water_Intake (liters)": 2.6,
                                "Workout_Frequency (days/week)": 3, "Experience_Level": 2, "BMI": 24.5
                            }
                            r[feat] = defaults.get(feat, None)
                with st.spinner("Getting batch predictions..."):
                    preds = predict_records(records, use_api=use_api, api_url=api_url if use_api else "")
                if preds is None:
                    st.warning("Batch prediction failed")
                else:
                    df_preds = pd.DataFrame(preds)
                    st.success("Batch predictions complete")
                    st.dataframe(df_preds.head(50))
                    append_predictions_to_store(df_preds, source="webapp")
        except Exception as e:
            st.error(f"Could not read uploaded file: {e}")

elif page == "View Past Predictions":
    st.header("Saved past predictions (demo store)")
    df_saved = load_saved_predictions()
    if df_saved.empty:
        st.info("No saved predictions yet. Make a prediction in the 'Make Predictions' page to populate demo store.")
    else:
        # allow filtering by date and source
        try:
            df_saved["timestamp"] = pd.to_datetime(df_saved["timestamp"])
        except Exception:
            pass
        col1, col2 = st.columns(2)
        with col1:
            min_date = df_saved["timestamp"].min().date() if not df_saved.empty else None
            max_date = df_saved["timestamp"].max().date() if not df_saved.empty else None
            start_date = st.date_input("Start date", min_value=min_date, value=min_date)
            end_date = st.date_input("End date", min_value=min_date, value=max_date)
        with col2:
            src = st.selectbox("Source", ["all"] + sorted(df_saved["source"].unique().tolist()))
            if st.button("Apply filters"):
                pass
        # apply filters
        df_filtered = df_saved.copy()
        if start_date:
            df_filtered = df_filtered[df_filtered["timestamp"].dt.date >= start_date]
        if end_date:
            df_filtered = df_filtered[df_filtered["timestamp"].dt.date <= end_date]
        if src and src != "all":
            df_filtered = df_filtered[df_filtered["source"] == src]
        st.write(f"Showing {len(df_filtered)} rows")
        st.dataframe(df_filtered.sort_values("timestamp", ascending=False).reset_index(drop=True))

    st.markdown("You can find the demo saved file at: `/dsp-alaa-bhakti/heart-gym-ml-prod/streamlit/predictions_store.csv` on the machine running this app.")

st.markdown("---")
st.markdown("**Notes:** This app uses a fake deterministic heuristic model for demonstration. When your FastAPI `/predict` endpoint is ready, switch to 'Call model API' in the sidebar and provide the API base URL. The app expects the API to accept POST `/predict` with JSON `{\"data\": [<rows>]}` and to return a list of records with `prediction_prob` and `prediction_label` added.")
