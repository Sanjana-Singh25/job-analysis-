"""Module 2: Data cleaning and preprocessing.

Reads data/raw_jobs.csv and writes data/cleaned_jobs.csv.
Run from the project root:  python src/data_cleaning.py
"""
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT / "data" / "raw_jobs.csv"
CLEAN_PATH = ROOT / "data" / "cleaned_jobs.csv"


def clean_jobs(df: pd.DataFrame) -> pd.DataFrame:
    # Columns that are mostly empty and not needed for the project
    df = df.drop(columns=["med_salary", "applies", "remote_allowed"])

    # Fill missing text columns with a meaningful label
    df["experience_level"] = df["experience_level"].fillna("Not Specified")
    df["company_name"] = df["company_name"].fillna("Unknown")
    df["industry_name"] = df["industry_name"].fillna("Unknown")
    df["views"] = df["views"].fillna(0)

    # Keep only rows that have salary information
    df = df.dropna(subset=["normalized_salary"], how="all")

    # Split "City, ST" into two columns
    df[["city", "state"]] = df["location"].str.split(",", n=1, expand=True)
    df["city"] = df["city"].str.strip()
    df["state"] = df["state"].str.strip()

    # Keep USD only (one CAD row in the dataset is negligible)
    df = df[df["currency"] == "USD"]

    # Remove duplicate postings
    df = df.drop_duplicates(subset="job_id")

    # Original location column is no longer needed
    df = df.drop(columns=["location"])
    return df


def main() -> None:
    raw = pd.read_csv(RAW_PATH)
    print("Raw data:", raw.shape)
    cleaned = clean_jobs(raw)
    cleaned.to_csv(CLEAN_PATH, index=False)
    print("Saved cleaned_jobs.csv", cleaned.shape)


if __name__ == "__main__":
    main()
