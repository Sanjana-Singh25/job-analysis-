"""Module 5: Salary prediction (Random Forest Regressor).

Reads data/jobs_with_skills.csv, trains the model and saves:
  models/salary_model.pkl
  models/salary_model_columns.pkl
Run from the project root:  python src/salary_prediction.py
"""
import ast
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "jobs_with_skills.csv"
MODEL_PATH = ROOT / "models" / "salary_model.pkl"
COLUMNS_PATH = ROOT / "models" / "salary_model_columns.pkl"

CATEGORICAL = ["experience_level", "work_type", "state", "industry_name"]
MIN_SALARY, MAX_SALARY = 15000, 400000  # drop unrealistic outliers


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["num_skills"] = df["extracted_skills"].apply(
        lambda x: len(ast.literal_eval(x)) if isinstance(x, str) else len(x)
    )
    df = df[df["normalized_salary"].between(MIN_SALARY, MAX_SALARY)]
    cols = CATEGORICAL + ["views", "num_skills", "normalized_salary"]
    df = df[cols].dropna(subset=["state", "industry_name"])
    return pd.get_dummies(df, columns=CATEGORICAL, drop_first=True)


def train() -> None:
    df = pd.read_csv(DATA_PATH)
    model_df = build_features(df)
    print("Rows:", model_df.shape[0], "| Columns:", model_df.shape[1])

    X = model_df.drop(columns=["normalized_salary"])
    y = model_df["normalized_salary"]
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    pred = model.predict(X_test)

    print(f"Mean Absolute Error: ${mean_absolute_error(y_test, pred):,.2f}")
    print(f"Root Mean Squared Error: ${np.sqrt(mean_squared_error(y_test, pred)):,.2f}")
    print(f"R2 Score: {r2_score(y_test, pred):.3f}")

    MODEL_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(X.columns.tolist(), COLUMNS_PATH)
    print("Model saved")


def load_model():
    """Load the saved model and its column list. Returns (model, columns)."""
    return joblib.load(MODEL_PATH), joblib.load(COLUMNS_PATH)


def predict_salary(experience_level, work_type, state, industry_name,
                   views=0, num_skills=0, model=None, columns=None) -> float:
    """Predict annual salary (USD) for one job using the saved model.

    Pass model and columns (from load_model) to avoid reloading from disk
    on every call.
    """
    if model is None or columns is None:
        model, columns = load_model()
    row = pd.DataFrame(0, index=[0], columns=columns)
    row["views"] = views
    row["num_skills"] = num_skills
    for prefix, value in [("experience_level", experience_level),
                          ("work_type", work_type),
                          ("state", state),
                          ("industry_name", industry_name)]:
        col = f"{prefix}_{value}"
        if col in row.columns:  # the baseline category stays all zeros
            row[col] = 1
    return float(model.predict(row)[0])


if __name__ == "__main__":
    train()
