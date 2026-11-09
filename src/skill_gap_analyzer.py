"""Module 7: Skill gap analyzer.

Compares a user's skills with the most demanded skills for a target role.
Run from the project root:  python src/skill_gap_analyzer.py
"""
import ast
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "jobs_with_skills.csv"


def load_data() -> pd.DataFrame:
    df = pd.read_csv(DATA_PATH)
    df["extracted_skills"] = df["extracted_skills"].apply(ast.literal_eval)
    return df


def get_top_skills_for_role(df, role_keyword, top_n=10, min_share=0.05):
    """Return (top skills, number of matching jobs) for a job-title keyword."""
    role_jobs = df[df["title"].str.contains(role_keyword, case=False, na=False)]
    if len(role_jobs) == 0:
        return None, 0

    counts = Counter(role_jobs["extracted_skills"].sum())
    # a skill must appear in at least 5% of the jobs (and at least 2 jobs)
    min_count = max(2, int(len(role_jobs) * min_share))
    top = [s for s, c in counts.most_common(top_n) if c >= min_count]
    if not top:
        return None, len(role_jobs)
    return top, len(role_jobs)


def skill_gap_analysis(df, target_role, my_skills, top_n=10):
    my_skills = [s.strip().lower() for s in my_skills]
    required, num_jobs = get_top_skills_for_role(df, target_role, top_n)

    if required is None:
        print(f"Not enough job postings found for role: {target_role}")
        return None

    matched = [s for s in required if s in my_skills]
    missing = [s for s in required if s not in my_skills]
    match_pct = len(matched) / len(required) * 100

    print(f"Target Role: {target_role} (based on {num_jobs} job postings)")
    print(f"Top skills required: {required}\n")
    print(f"You have: {matched}")
    print(f"You are missing: {missing}")
    print(f"Skill Match: {match_pct:.0f}%")
    return {"matched": matched, "missing": missing, "match_pct": match_pct}


if __name__ == "__main__":
    data = load_data()
    skill_gap_analysis(data, "Data Analyst", ["python", "excel", "communication"])
    print()
    skill_gap_analysis(data, "Nurse", ["nursing", "communication"])
