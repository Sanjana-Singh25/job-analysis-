# Job Market Intelligence and Skill Demand Analytics

A data analytics and machine learning project that studies the job market using
LinkedIn job postings: which roles and skills are in demand, how salaries vary,
and what a job seeker is missing for a target role.

## Objectives

- Analyze job demand by role, location, industry and experience level
- Extract skills from job descriptions and measure skill demand
- Predict salary from job attributes (regression)
- Classify a job description into an industry (text classification)
- Compare a user's skills against a target role (skill gap analysis)
- Present the findings in an interactive dashboard (Power BI and Streamlit)

## Dataset

LinkedIn Job Postings (2023-2024) from Kaggle (`arshkon/linkedin-job-postings`).

`data/raw_jobs.csv` was prepared from the original `postings.csv`:
18 useful columns kept, the industry name merged in, rows without a
description removed, and a random sample of 30,000 postings taken
(`random_state=42`). About 29% of the sample had salary information; after
keeping USD rows with salary, splitting `City, ST` and removing duplicate
postings, **8,713 postings with salary information** remain
(`data/cleaned_jobs.csv`, 16 columns).

> Data and models are **not tracked in git** (too large / redistributable
> constraints): `data/` and `models/` are gitignored and regenerable by
> running the pipeline. You need `data/cleaned_jobs.csv` to reproduce the
> downstream steps (see Usage).

## Workflow

| Step | Notebook | Script | Output |
|---|---|---|---|
| 1. Cleaning | `01_job_market.ipynb` | `src/data_cleaning.py` | `data/cleaned_jobs.csv` |
| 2. EDA | `01_job_market.ipynb` | notebook only | charts |
| 3. Skill extraction | `03_skill_extraction.ipynb` | `src/skill_extraction.py` | `data/jobs_with_skills.csv`, `data/top_skills.csv` |
| 4. Salary model | `04_salary_prediction.ipynb` | `src/salary_prediction.py` | `models/salary_model.pkl` |
| 5. Job classifier | `05_job_classification.ipynb` | `src/job_classifier.py` | `models/job_classifier.pkl` |
| 6. Skill gap analyzer | `06_skill_gap_analyzer.ipynb` | `src/skill_gap_analyzer.py` | console output |
| 7. Dashboard prep | `07_dashboard_prep.ipynb` | notebook only | `data/dashboard_jobs.csv`, `data/dashboard_skills.csv` |
| 8. Dashboard | Power BI | none | `dashboard/job_market_dashboard.pbix` |
| 9. Dashboard | Streamlit | `app/app.py` | interactive web app |

## Results

- **Skill demand (v2.2 extractor):** communication (4,183), leadership (1,889),
  sales (1,789), customer service (1,753) and excel (1,345) are the most
  requested skills. Tech skills such as SQL and Python also appear in
  non-tech industries.
- **Salary prediction:** Random Forest Regressor, R² ≈ 0.29, MAE ≈ $30,440
  (median absolute error $21,509; within ±$50k: 82.0%; unbiased on average).
  Salary depends on many factors that are not in job postings (company size,
  negotiation, benefits), so a modest R² is expected.
- **Job classification:** TF-IDF + Logistic Regression over the 10 most common
  industries, accuracy ≈ 71.1% (macro F1 0.67).

## Quality assurance & evaluation

Detailed, reproducible evaluation write-ups live in [`docs/`](docs/):

- [docs/skill_extraction_verification.md](docs/skill_extraction_verification.md) —
  full-description verification of sampled extracted matches (7 labelled sets,
  1,008 matches, combined precision **89.09%**). The v2.2 extractor suppresses
  known department-name / boilerplate / culture-prose contexts; verified
  data: full 100%, holdout7 100%, holdout6 96.06% kept-set precision with
  **zero verified-correct matches suppressed**.
- [docs/model_evaluation.md](docs/model_evaluation.md) — salary model error
  breakdown and classifier F1 by class, plus the skill-demand refresh.
- [docs/confusion_matrix.md](docs/confusion_matrix.md) — 10×10 confusion
  matrix for the industry classifier.

## Project structure

```
job-market-analytics/
├── app/              Streamlit dashboard (app/app.py)
├── dashboard/        Power BI file, PDF export and presentation
├── data/             gitignored — raw, cleaned and derived data (regenerable)
├── docs/             verification and evaluation reports (tracked)
├── models/           gitignored — trained model pickles (regenerable)
├── notebooks/        Jupyter notebooks (EDA and modelling)
├── src/              reusable Python scripts
├── requirements.txt
└── README.md
```

## Setup

```
python -m venv .venv
.venv\Scripts\activate        # Windows
source .venv/bin/activate     # macOS/Linux
pip install -r requirements.txt
```

## Usage

Data and models are not in the repo — generate them first (you need
`data/cleaned_jobs.csv` in place):

```
python src/skill_extraction.py
python src/salary_prediction.py

python src/job_classifier.py
```

Then try the command-line entry points:

```
python src/skill_gap_analyzer.py
```

And launch the interactive dashboard (Streamlit):

```
streamlit run app/app.py
```

Use the trained models from Python:

```python
import sys
sys.path.append("src")
from salary_prediction import predict_salary
from job_classifier import predict_industry

predict_salary("Entry level", "Full-time", "CA", "Software Development",
               views=20, num_skills=4)
predict_industry("We are hiring a registered nurse to provide patient care.")
```

## Limitations

- Skills are found by keyword matching against a list of 152 skills with a
  set of reviewed false-positive context suppressions. It still does not
  understand context in general, so the skill list is a proxy for capability,
  not a perfect reading of each posting. See
  [docs/skill_extraction_verification.md](docs/skill_extraction_verification.md).
- The Tech / Non-tech tag in the dashboard comes from a list chosen by the authors.
- Salary results describe the postings that list a salary (all 8,713 kept
  postings do; the 30,000-posting sample was about 29% salary-bearing).
- The data is a 30,000-posting sample of a larger dataset, and only 10
  industries are covered by the classifier.
