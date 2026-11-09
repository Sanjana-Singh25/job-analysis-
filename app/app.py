"""Job Market Intelligence - interactive dashboard (Streamlit).

One app that combines the whole project:
  Market Overview, Skill Demand, Salary Predictor, Job Classifier,
  Skill Gap Analyzer.

Run from the project root:
    streamlit run app/app.py

Before the first run, create the data and models:
    python src/data_cleaning.py
    python src/skill_extraction.py
    python src/salary_prediction.py
    python src/job_classifier.py
"""
import ast
import sys
from collections import Counter
from itertools import chain
from pathlib import Path

import altair as alt
import pandas as pd
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from job_classifier import load_classifier, predict_industry_top  # noqa: E402
from salary_prediction import load_model, predict_salary  # noqa: E402
from skill_extraction import SKILLS_LIST, TECH_SKILLS  # noqa: E402
from skill_gap_analyzer import get_top_skills_for_role  # noqa: E402

DATA_PATH = ROOT / "data" / "jobs_with_skills.csv"

# Tech skills come from src/skill_extraction.py (shared with the dashboard data)
TECH_INDUSTRY_WORDS = ["software", "it services", "technology", "computer",
                       "data infrastructure", "internet"]

st.set_page_config(page_title="Job Market Intelligence", layout="wide")


# ---------------------------------------------------------------- data
@st.cache_data
def load_data() -> pd.DataFrame:
    cols = ["job_id", "title", "company_name", "experience_level", "work_type",
            "views", "normalized_salary", "industry_name", "state",
            "extracted_skills"]
    df = pd.read_csv(DATA_PATH, usecols=cols)
    df["extracted_skills"] = df["extracted_skills"].apply(ast.literal_eval)
    # Same realistic salary range used for the salary model
    df["salary_clean"] = df["normalized_salary"].where(
        df["normalized_salary"].between(15000, 400000)
    )
    return df


@st.cache_resource
def get_salary_model():
    return load_model()


@st.cache_resource
def get_classifier():
    return load_classifier()


# ------------------------------------------------------------- helpers
def bar_chart(data: pd.DataFrame, label: str, value: str,
              value_title: str = "Number of postings", height: int = 350):
    """Horizontal bar chart, longest bar on top."""
    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(f"{value}:Q", title=value_title),
            y=alt.Y(f"{label}:N", sort="-x", title=None),
            tooltip=[label, value],
        )
        .properties(height=height)
    )
    st.altair_chart(chart)


def count_table(series: pd.Series, name: str, top: int = 10) -> pd.DataFrame:
    counts = series.value_counts().head(top)
    return pd.DataFrame({name: counts.index, "postings": counts.values})


def skill_counts(df: pd.DataFrame, only=None) -> Counter:
    skills = chain.from_iterable(df["extracted_skills"])
    if only is not None:
        skills = (s for s in skills if s in only)
    return Counter(skills)


def apply_filters(df: pd.DataFrame) -> pd.DataFrame:
    st.sidebar.subheader("Filters")
    states = st.sidebar.multiselect(
        "State", sorted(s for s in df["state"].dropna().unique()
                        if s != "United States"))
    industries = st.sidebar.multiselect(
        "Industry", sorted(i for i in df["industry_name"].dropna().unique()
                           if i != "Unknown"))
    levels = st.sidebar.multiselect(
        "Experience level", sorted(df["experience_level"].dropna().unique()))
    if states:
        df = df[df["state"].isin(states)]
    if industries:
        df = df[df["industry_name"].isin(industries)]
    if levels:
        df = df[df["experience_level"].isin(levels)]
    return df


# ---------------------------------------------------------------- pages
def page_overview(df: pd.DataFrame):
    st.title("Market Overview")
    if df.empty:
        st.warning("No job postings match the selected filters.")
        return

    median = df["salary_clean"].median()
    cols = st.columns(4)
    cols[0].metric("Job postings", f"{len(df):,}")
    cols[1].metric("Median salary",
                   f"${median:,.0f}" if pd.notna(median) else "n/a")
    cols[2].metric("Companies", f"{df['company_name'].nunique():,}")
    cols[3].metric("Industries", f"{df['industry_name'].nunique():,}")

    left, right = st.columns(2)
    with left:
        st.subheader("Top 10 states")
        states = df[df["state"].notna() & (df["state"] != "United States")]
        bar_chart(count_table(states["state"], "state"), "state", "postings")
    with right:
        st.subheader("Top 10 industries")
        inds = df[df["industry_name"] != "Unknown"]
        bar_chart(count_table(inds["industry_name"], "industry"),
                  "industry", "postings")

    left, right = st.columns(2)
    with left:
        st.subheader("Median salary by experience level")
        sal = df.dropna(subset=["salary_clean"])
        med = (sal.groupby("experience_level")["salary_clean"].median()
               .reset_index(name="median_salary"))
        bar_chart(med, "experience_level", "median_salary",
                  value_title="Median annual salary (USD)")
    with right:
        st.subheader("Postings by work type")
        bar_chart(count_table(df["work_type"], "work_type"),
                  "work_type", "postings")

    st.subheader("Salary distribution")
    sal = df.dropna(subset=["salary_clean"])[["salary_clean"]]
    hist = (
        alt.Chart(sal)
        .mark_bar()
        .encode(
            x=alt.X("salary_clean:Q", bin=alt.Bin(step=20000),
                    title="Annual salary (USD), bins of $20,000"),
            y=alt.Y("count()", title="Postings"),
        )
        .properties(height=300)
    )
    st.altair_chart(hist)
    st.caption("Only postings with a salary between $15,000 and $400,000 "
               "are shown here. Many postings do not list a salary.")


def page_skills(df: pd.DataFrame):
    st.title("Skill Demand")
    if df.empty:
        st.warning("No job postings match the selected filters.")
        return

    tab_all, tab_role, tab_tech = st.tabs(
        ["Top skills", "Skills for a role", "Tech skills in non-tech jobs"])

    with tab_all:
        top = skill_counts(df).most_common(15)
        bar_chart(pd.DataFrame(top, columns=["skill", "postings"]),
                  "skill", "postings", height=450)

    with tab_role:
        role = st.text_input("Job title keyword", value="Data Analyst")
        jobs = df[df["title"].str.contains(role, case=False, na=False,
                                           regex=False)]
        if role.strip() == "" or jobs.empty:
            st.info("No postings found for that keyword.")
        else:
            st.write(f"{len(jobs):,} postings match '{role}'.")
            top = skill_counts(jobs).most_common(10)
            if top:
                bar_chart(pd.DataFrame(top, columns=["skill", "postings"]),
                          "skill", "postings")
            else:
                st.info("None of the tracked skills appear in these postings.")

    with tab_tech:
        words = "|".join(TECH_INDUSTRY_WORDS)
        is_tech = df["industry_name"].str.lower().str.contains(words, na=False)
        non_tech = df[~is_tech & (df["industry_name"] != "Unknown")]
        top = skill_counts(non_tech, only=set(TECH_SKILLS)).most_common(10)
        st.write(f"Based on {len(non_tech):,} postings from industries that "
                 "are not software or IT.")
        if top:
            bar_chart(pd.DataFrame(top, columns=["skill", "postings"]),
                      "skill", "postings")
        else:
            st.info("No tech skills found in the selected postings.")
        st.caption("The tech skill list and the tech-industry keywords are "
                   "chosen by the project authors.")


def page_salary(df: pd.DataFrame):
    st.title("Salary Predictor")
    try:
        model, columns = get_salary_model()
    except FileNotFoundError:
        st.error("Salary model not found. Run: python src/salary_prediction.py")
        return

    left, right = st.columns(2)
    with left:
        exp = st.selectbox("Experience level",
                           sorted(df["experience_level"].dropna().unique()))
        work = st.selectbox("Work type",
                            sorted(df["work_type"].dropna().unique()))
        state = st.selectbox("State", sorted(
            s for s in df["state"].dropna().unique() if s != "United States"))
    with right:
        industry = st.selectbox("Industry", sorted(
            i for i in df["industry_name"].dropna().unique() if i != "Unknown"))
        n_skills = st.slider("Number of tracked skills in the job", 0, 15, 3)
        views = st.number_input("Posting views", min_value=0, value=10)

    if st.button("Predict salary"):
        value = predict_salary(exp, work, state, industry, views=views,
                               num_skills=n_skills, model=model,
                               columns=columns)
        st.metric("Estimated annual salary", f"${value:,.0f}")

        similar = df[(df["experience_level"] == exp)
                     & (df["industry_name"] == industry)]["salary_clean"].dropna()
        if len(similar) >= 5:
            st.write(f"For comparison, {len(similar)} postings with the same "
                     f"experience level and industry have a median salary of "
                     f"${similar.median():,.0f}.")
        st.caption("Random Forest model, R2 about 0.29 and mean absolute "
                   "error about $30,500 on test data. Treat the result as a "
                   "rough estimate, not an exact salary.")


def page_classifier(df: pd.DataFrame):
    st.title("Job Classifier")
    try:
        clf, tfidf = get_classifier()
    except FileNotFoundError:
        st.error("Classifier not found. Run: python src/job_classifier.py")
        return

    text = st.text_area(
        "Paste a job description",
        value="We are hiring a registered nurse to provide patient care "
              "in our hospital ward.",
        height=180)
    if st.button("Predict industry"):
        if not text.strip():
            st.warning("Please enter a job description.")
            return
        top = predict_industry_top(text, k=3, clf=clf, tfidf=tfidf)
        st.success(f"Predicted industry: {top[0][0]}")
        table = pd.DataFrame({"industry": [t[0] for t in top],
                              "probability_pct": [round(t[1] * 100, 1)
                                                  for t in top]})
        bar_chart(table, "industry", "probability_pct",
                  value_title="Probability (%)", height=180)
    st.caption("The model knows these industries: "
               + ", ".join(sorted(clf.classes_)))


def page_gap(df: pd.DataFrame):
    st.title("Skill Gap Analyzer")
    role = st.text_input("Target job role", value="Data Analyst")
    mine = st.multiselect("Your current skills", sorted(SKILLS_LIST),
                          default=["excel", "communication"])

    required, n_jobs = get_top_skills_for_role(df, role, top_n=10)
    if required is None:
        st.warning(f"Not enough job postings found for '{role}'. "
                   "Try a more common title keyword.")
        return

    matched = [s for s in required if s in mine]
    missing = [s for s in required if s not in mine]
    pct = len(matched) / len(required) * 100

    st.write(f"Based on {n_jobs} job postings for '{role}'.")
    st.metric("Skill match", f"{pct:.0f}%")
    st.progress(int(pct))

    left, right = st.columns(2)
    with left:
        st.subheader("You have")
        st.write(", ".join(matched) if matched else "None of the top skills yet")
    with right:
        st.subheader("You should learn")
        st.write(", ".join(missing) if missing else "Nothing, you cover them all")
    st.caption("Required skills are the most common skills in postings for "
               "this role, using the project's skill list.")


PAGES = {
    "Market Overview": page_overview,
    "Skill Demand": page_skills,
    "Salary Predictor": page_salary,
    "Job Classifier": page_classifier,
    "Skill Gap Analyzer": page_gap,
}

# ----------------------------------------------------------------- main
if not DATA_PATH.exists():
    st.error("data/jobs_with_skills.csv not found. "
             "Run: python src/skill_extraction.py")
    st.stop()

data = load_data()
st.sidebar.title("Job Market Intelligence")
page = st.sidebar.radio("Go to", list(PAGES))

if page in ("Market Overview", "Skill Demand"):
    view = apply_filters(data)
else:
    view = data
PAGES[page](view)
