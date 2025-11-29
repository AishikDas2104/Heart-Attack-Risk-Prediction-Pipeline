# app.py
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, time

# FastAPI endpoint URL (running locally)
API_URL = "http://127.0.0.1:8000"

# --- Page Config ---
st.set_page_config(page_title="Heart Attack Prediction", page_icon="❤️", layout="wide")

# --- Sidebar Navigation ---
page = st.sidebar.selectbox("Navigation", ["Prediction", "Past Predictions"])

if page == "Prediction":
    # --- Title & Description ---
    st.title("🏋️‍♂️ Heart Attack Risk Predictor")
    st.markdown("""
    Predict the **risk of a heart attack** based on key health parameters.  
    You can make a single prediction or upload a CSV for multiple predictions.
    """)

    tab1, tab2 = st.tabs(["Single Prediction", "Multi Prediction"])

    with tab1:
        st.header("🧠 Single Prediction")
        with st.form(key="prediction_form"):
            age = st.number_input("Age", min_value=10, max_value=100, step=1)
            gender = st.selectbox("Gender", ["male", "female"])
            duration = st.number_input("Duration of Exercise (minutes)", min_value=1.0, max_value=300.0)
            heart_rate = st.number_input("Heart Rate (bpm)", min_value=40, max_value=220)
            body_temp = st.number_input("Body Temperature (°F)", min_value=95.0, max_value=110.0)
            
            submit_button = st.form_submit_button(label="Predict")

        if submit_button:
            payload = {
                "age": int(age),
                "gender": gender,
                "duration": float(duration),
                "heart_rate": int(heart_rate),
                "body_temp": float(body_temp)
            }

            with st.spinner("Predicting..."):
                try:
                    response = requests.post(f"{API_URL}/predict", params={"source": "webapp"}, json=payload)
                    response.raise_for_status()
                    result = response.json()
                    risk = result.get("prediction", "Unknown")
                    
                    st.success(f"### 🩺 Predicted Risk: **{risk}**")
                    with st.expander("See input details"):
                        st.json(result["input_data"])

                except requests.exceptions.RequestException as e:
                    st.error(f"🚨 API request failed: {e}")

    with tab2:
        st.header("📂 Multi Prediction (CSV Upload)")
        uploaded_file = st.file_uploader("Upload a CSV file (must contain required columns)", type=["csv"])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.write("Preview of uploaded data:", df.head())
                
                if st.button("Predict All"):
                    # Prepare batch payload
                    payload_list = []
                    for i, row in df.iterrows():
                         payload_list.append({
                            "age": int(row.get("Age", row.get("age", 0))),
                            "gender": str(row.get("Gender", row.get("gender", "male"))).lower(),
                            "duration": float(row.get("Duration", row.get("duration", 0))),
                            "heart_rate": int(row.get("Heart_Rate", row.get("heart_rate", 0))),
                            "body_temp": float(row.get("Body_Temp", row.get("body_temp", 98.6)))
                        })
                    
                    with st.spinner("Sending batch prediction request..."):
                        try:
                            resp = requests.post(f"{API_URL}/predict", params={"source": "webapp"}, json=payload_list)
                            resp.raise_for_status()
                            results = resp.json()
                            
                            # Extract predictions
                            predictions = [r["prediction"] for r in results]
                            df["Prediction"] = predictions
                            
                            st.success("✅ Predictions Complete!")
                            st.dataframe(df)
                            
                        except requests.exceptions.RequestException as e:
                            st.error(f"🚨 API request failed: {e}")
                        except Exception as e:
                            st.error(f"🚨 Error processing response: {e}")
                    
            except Exception as e:
                st.error(f"Error reading file: {e}")

elif page == "Past Predictions":
    st.title("📜 Past Predictions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        start_date = st.date_input("Start Date", value=datetime.now())
    with col2:
        end_date = st.date_input("End Date", value=datetime.now())
    with col3:
        source = st.selectbox("Source", ["all", "webapp", "scheduled"])
        
    if st.button("Fetch Predictions"):
        params = {
            "start_date": datetime.combine(start_date, time.min).isoformat(),
            "end_date": datetime.combine(end_date, time.max).isoformat(),
            "source": source
        }
        
        with st.spinner("Fetching..."):
            try:
                response = requests.get(f"{API_URL}/past-predictions", params=params)
                response.raise_for_status()
                data = response.json()
                
                if data:
                    df = pd.DataFrame(data)
                    # Flatten features
                    features_df = pd.json_normalize(df['features'])
                    df = pd.concat([df.drop(['features'], axis=1), features_df], axis=1)
                    st.dataframe(df)
                else:
                    st.info("No predictions found for the selected criteria.")
                    
            except requests.exceptions.RequestException as e:
                st.error(f"🚨 API request failed: {e}")
