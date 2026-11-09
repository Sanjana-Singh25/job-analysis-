"""Module 6: Job classification (TF-IDF + Logistic Regression).

Predicts the industry of a job from its description (top 10 industries).
Saves:
  models/job_classifier.pkl
  models/tfidf_vectorizer.pkl
Run from the project root:  python src/job_classifier.py
"""
from pathlib import Path

import joblib
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report
from sklearn.model_selection import train_test_split

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "jobs_with_skills.csv"
CLF_PATH = ROOT / "models" / "job_classifier.pkl"
TFIDF_PATH = ROOT / "models" / "tfidf_vectorizer.pkl"


def train() -> None:
    df = pd.read_csv(DATA_PATH)

    top_industries = df["industry_name"].value_counts().head(10).index.tolist()
    print("Industries:", top_industries)
    df = df[df["industry_name"].isin(top_industries)]
    df = df.dropna(subset=["description", "industry_name"])
    print("Rows for classification:", df.shape[0])

    tfidf = TfidfVectorizer(max_features=3000, stop_words="english", min_df=2)
    X = tfidf.fit_transform(df["description"])
    y = df["industry_name"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    clf = LogisticRegression(max_iter=1000)
    clf.fit(X_train, y_train)
    pred = clf.predict(X_test)

    print(f"Accuracy: {accuracy_score(y_test, pred):.3f}")
    print(classification_report(y_test, pred))

    CLF_PATH.parent.mkdir(exist_ok=True)
    joblib.dump(clf, CLF_PATH)
    joblib.dump(tfidf, TFIDF_PATH)
    print("Job classifier saved")


def load_classifier():
    """Load the saved classifier and TF-IDF vectorizer. Returns (clf, tfidf)."""
    return joblib.load(CLF_PATH), joblib.load(TFIDF_PATH)


def predict_industry(description: str) -> str:
    """Predict the industry for one job description."""
    clf, tfidf = load_classifier()
    return clf.predict(tfidf.transform([description]))[0]


def predict_industry_top(description: str, k: int = 3, clf=None, tfidf=None):
    """Return the k most likely industries as a list of (industry, probability)."""
    if clf is None or tfidf is None:
        clf, tfidf = load_classifier()
    probs = clf.predict_proba(tfidf.transform([description]))[0]
    order = probs.argsort()[::-1][:k]
    return [(clf.classes_[i], float(probs[i])) for i in order]


if __name__ == "__main__":
    train()
