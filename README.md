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
- Present the findings in an interactive Power BI dashboard

## Dataset

LinkedIn Job Postings (2023-2024) from Kaggle (`arshkon/linkedin-job-postings`).

`data/raw_jobs.csv` was prepared from the original `postings.csv`:
18 useful columns kept, the industry name merged in, rows without a
description removed, and a random sample of 30,000 postings taken
(`random_state=42`). After cleaning, 8,713 postings with salary information remain.

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

## Results

- **Skill demand:** communication, leadership, sales, customer service and excel
  are the most requested skills. Tech skills such as SQL and Python also appear
  in non-tech industries.
- **Salary prediction:** Random Forest Regressor, R2 about 0.29, MAE about $30,500.
  Salary depends on many factors that are not in job postings (company size,
  negotiation, benefits), so a modest R2 is expected.
- **Job classification:** TF-IDF + Logistic Regression over the 10 most common
  industries, accuracy about 71%.

## Project structure

```
job-market-analytics/
├── app/
├── dashboard/        Power BI file
├── data/             raw, cleaned and dashboard data
├── models/           saved models (.pkl)
├── notebooks/        Jupyter notebooks
├── src/              reusable Python scripts
├── requirements.txt
└── README.md
```

## Setup

```
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

## Usage

Run the pipeline from the project root, in this order:

```
python src/data_cleaning.py
python src/skill_extraction.py
python src/salary_prediction.py
python src/job_classifier.py
python src/skill_gap_analyzer.py
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

- Skills are found by keyword matching against a list of 152 skills. It does not
  understand context, so a generic word can be counted as a skill.
- The Tech / Non-tech tag in the dashboard comes from a list chosen by the authors.
- Only about 29% of postings contain salary information, so salary results
  describe the postings that list a salary.
- The data is a 30,000-posting sample of a larger dataset.
