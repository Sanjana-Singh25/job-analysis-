# Model evaluation (retrained 2026-11-09 on v2.2 `jobs_with_skills.csv`)

## Salary prediction — RandomForestRegressor (100 trees, random_state=42)
Rows after salary filter ($15k–$400k): **7,508** · 334 one-hot columns · 80/20 split
- **MAE: $30,484** · **RMSE: $42,991** · **R²: 0.291**
- Median |error| $21,327 · within ±$25k: **56.3%** · within ±$50k: **81.7%** · signed bias ≈ **+$60** (unbiased)
- Honest limit: company size, negotiation and benefits are not in the postings, so salary is
  only weakly predictable — treat output as ballpark.

## Job classification — TF-IDF (max_features=3000, English stopwords) + LogisticRegression
Top-10 industries only · **3,945** rows · stratified 80/20 split
- **Accuracy: 0.711** · macro P/R/F1 = 0.78/0.64/0.67 · weighted F1 = 0.71
- F1 by class: Hospitals 0.88 · Retail 0.86 · Banking 0.72 · Software Dev 0.69 ·
  Construction 0.68 · Staffing 0.65 · Financial Services 0.62 · Accounting 0.62 ·
  IT Services 0.57 · Manufacturing 0.44 (recall 0.28)
- Confusion matrix: [confusion_matrix.md](confusion_matrix.md). Typical confusions:
  IT Services ↔ Software Development, Staffing & Recruiting absorbs misroutes from all classes.
- If accuracy wants a bump later (not done): class_weight="balanced" or larger max_features.

## Skill-demand refresh (v2.2 top 15, regeneration 2026-11-09)
communication 4,183 · leadership 1,889 · sales 1,789 · customer service 1,753 · excel 1,345 ·
problem solving 1,326 · attention to detail 1,314 · microsoft office 1,227 · marketing 1,167 ·
cross-functional 833 · teamwork 826 · accounting 817 · project management 812 ·
interpersonal skills 728 · auditing 719
(Models above were retrained on the v2.2 regeneration — salary MAE moved from $30,440 (v2.1) to
$30,484; classifier accuracy and the confusion matrix are unchanged. Pre-v2 figures were slightly
higher, e.g. leadership 2,079, excel 1,448 — see `skill_extraction_impact.csv` on Drive.)
