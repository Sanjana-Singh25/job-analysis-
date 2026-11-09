# Skill extraction — precision verification (2026-11-09)

Full-description verification of every sampled extracted-skill match. Method: locate each
matched skill (and its aliases) inside the **full** description, then re-judge against the
project convention — `y` = the posting requires/expects the skill from the candidate;
`n` = the word appears only as boilerplate/legal text, a department or team name, a product
or brand name the candidate only collaborates with, or the verb form.

The sampled match files themselves live in the `data/` folder (gitignored): `skill_check_full.csv`,
`skill_check_holdout6/7.csv` (with `*_verified.csv` alongside). Scores below are reproducible
from those files + `src/skill_extraction.py`.

## Results

| Set | Sample | Verified precision | Current (v2.1) extractor |
|---|---|---|---|
| skill_check_full (v1 sample, re-verified) | 144 | 126/144 = **87.50%** (2 mislabels fixed: `billing`, `machine learning`) | suppresses all 18 known-FP contexts; 0 verified-y lost |
| holdout2–5 (previously labelled, v2) | 4 × 144 | 134 / 127 / 131 / 132 correct (**93.06 / 88.19 / 90.97 / 91.67%**) | — |
| holdout6 (v1 sample, labelled 2026-11-09) | 144 | **122/144 = 84.72%** (22 FP) | keeps 127/144 at **96.06%** precision; **0** verified-y suppressed |
| holdout7 (v2 sample, labelled 2026-11-09) | 144 | **126/144 = 87.50%** (18 new FP) | v2 does not yet catch these → 87.50% on fresh data |
| **Combined** | **1008** | **898/1008 = 89.09%** | |

## Fixes shipped in v2.1 (`src/skill_extraction.py`)

`billing` — internal-team contexts (`collaboration with billing`, `billing, credentialing`, `teams (billing`).
`machine learning` / `artificial intelligence` — employer EEO/legal boilerplate
(`…machine learning technologies in connection with applications…`).

Effect on the full 8,713 postings: `machine learning` 160→143, `artificial intelligence` 104→85,
`billing` 303→302; top-15 unchanged (communication 4,184 · leadership 1,906 · sales 1,796 ·
customer service 1,766 · excel 1,345 …). Zero verified-correct matches suppressed.

## Known, not yet suppressed (proposed, pending review)

18 false positives found in holdout7: `workday` as a noun; function/department mentions
(`Employee Relations` ×2, `Talent Acquisition` ×2 partnering contexts, `Procurement`,
`sales team`, `post-sales`); culture/recruiting prose (`teamwork` ×2, `leadership` ×2 incl.
finance-leadership audience and "we'll give you the coaching" offer copy, `customer service`
BAE descriptor, `customer experience` Con Edison mission, `e-commerce space`,
`communication` "documentation systems"). Not auto-suppressed — e.g. Employee Relations is a
real skill for HR generalists. Over-suppression is the bigger risk; expand deliberately.

## Lessons / process notes

- The 500-char `description_snippet` in the original `skill_check.csv` made labels unverifiable;
  all samples now carry the full description.
- Every round of holdout labelling found NEW FP types — expect diminishing returns, target
  the highest-frequency ones only.
- 36 MB `jobs_with_skills.csv` was removed from git tracking (stale pre-v2 copy; regenerated
  locally via `python src/skill_extraction.py`). Dataset now lives in the gitignored `data/`
  (regenerable) and Google Drive.
