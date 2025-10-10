import os, json, joblib
import pandas as pd, numpy as np
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import accuracy_score

RAW_DATA_PATH = "data/raw/heart.csv"
MODEL_DIR = "data/models"
os.makedirs(MODEL_DIR, exist_ok=True)

print("Loading:", RAW_DATA_PATH)
df = pd.read_csv(RAW_DATA_PATH)
# normalizeinng----<>
df.columns = df.columns.str.strip().str.replace(" ", "_")

TARGET = "Heart_Attack_Risk"
if "Heart_Attack_Risk_(Binary)" in df.columns:
    df = df.rename(columns={"Heart_Attack_Risk_(Binary)": TARGET})
# drop text label if present
df = df.drop(columns=["Heart_Attack_Risk_(Text)"], errors="ignore")

if TARGET not in df.columns:
    raise ValueError(f"Target column '{TARGET}' not found. Available: {list(df.columns)}")


drop_cats = {"Gender", "Family_History", "Diet", "Gender_", "Family History", "Diet "}
to_drop = [c for c in df.columns if any(c.startswith(x) for x in drop_cats)]
df = df.drop(columns=to_drop, errors="ignore")


num_cols = df.select_dtypes(include=np.number).columns
df[num_cols] = df[num_cols].fillna(df[num_cols].median())

X = df.drop(columns=[TARGET])
y = df[TARGET]

scaler = StandardScaler()
num_cols = X.select_dtypes(include=np.number).columns
X[num_cols] = scaler.fit_transform(X[num_cols])


X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)
model = RandomForestClassifier(n_estimators=120, random_state=42)
model.fit(X_tr, y_tr)

acc = accuracy_score(y_te, model.predict(X_te))
print("Accuracy:", round(acc, 3))

joblib.dump(model, f"{MODEL_DIR}/heart_attack_risk_model.joblib")
joblib.dump(scaler, f"{MODEL_DIR}/scaler.joblib")
with open(f"{MODEL_DIR}/feature_columns.json", "w") as f:
    json.dump(list(X.columns), f, indent=2)

print("Saved model artifacts to:", MODEL_DIR)
