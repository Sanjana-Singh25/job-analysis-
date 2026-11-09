
"""Manual precision check for extracted job skills.

Commands:
    python src/skill_precision_check.py make
    python src/skill_precision_check.py score
"""

import ast
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
DATA_PATH = ROOT / "data" / "jobs_with_skills.csv"
CHECK_PATH = ROOT / "data" / "skill_check.csv"
REPORT_PATH = ROOT / "data" / "skill_precision_report.csv"

SAMPLE_SIZE = 144


def make_sample():
    df = pd.read_csv(DATA_PATH)

    df["extracted_skills"] = df["extracted_skills"].apply(
        lambda x: ast.literal_eval(x) if isinstance(x, str) else []
    )

    rows = []

    for _, row in df.iterrows():
        for skill in row["extracted_skills"]:
            rows.append({
                "job_id": row["job_id"],
                "title": row["title"],
                "skill": skill,
                "description_snippet": str(row["description"])[:500],
                "match": ""
            })

    matches = pd.DataFrame(rows)

    if matches.empty:
        print("No extracted skill matches found.")
        return

    sample = matches.sample(
        n=min(SAMPLE_SIZE, len(matches)),
        random_state=42
    ).reset_index(drop=True)

    sample.to_csv(CHECK_PATH, index=False)

    print(f"Total extracted skill matches: {len(matches)}")
    print(f"Sample created: {len(sample)}")
    print(f"Saved to: {CHECK_PATH}")
    print("\nOpen skill_check.csv and label each match as:")
    print("y = Correct skill match")
    print("n = Incorrect skill match")


def score_sample():
    if not CHECK_PATH.exists():
        print("skill_check.csv not found. Run the make command first.")
        return

    df = pd.read_csv(CHECK_PATH)
    df["match"] = df["match"].fillna("").astype(str).str.strip().str.lower()

    valid = df[df["match"].isin(["y", "n"])].copy()

    if valid.empty:
        print("No labels found. First fill the match column with y/n.")
        return

    correct = (valid["match"] == "y").sum()
    incorrect = (valid["match"] == "n").sum()
    precision = correct / len(valid) * 100

    print("\n--- SKILL EXTRACTION PRECISION ---")
    print(f"Total labelled matches: {len(valid)}")
    print(f"Correct matches: {correct}")
    print(f"Incorrect matches: {incorrect}")
    print(f"Overall precision: {precision:.2f}%")
    print(f"Unlabelled matches: {len(df) - len(valid)}")

    report = (
        valid.groupby("skill")["match"]
        .agg(
            checked="count",
            correct=lambda x: (x == "y").sum()
        )
        .reset_index()
    )

    report["precision_percent"] = (
        report["correct"] / report["checked"] * 100
    ).round(2)

    report.to_csv(REPORT_PATH, index=False)
    print(f"\nSkill-wise report saved to: {REPORT_PATH}")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python src/skill_precision_check.py make|score")
    elif sys.argv[1].lower() == "make":
        make_sample()
    elif sys.argv[1].lower() == "score":
        score_sample()
    else:
        print("Invalid command. Use make or score.")

