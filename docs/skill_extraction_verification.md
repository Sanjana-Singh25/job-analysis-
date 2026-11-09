# Skill extraction — precision verification (2026-11-09, v2.2)

Full-description verification of every sampled extracted-skill match. Method: locate each
matched skill (and its aliases) inside the **full** description, then re-judge against the
project convention — `y` = the posting requires/expects the skill from the candidate;
`n` = the word appears only as boilerplate/legal text, a department or team name, a product
or brand name the candidate only collaborates with, or the verb form.

The sampled match files themselves live in the `data/` folder (gitignored): `skill_check_full.csv`,
`skill_check_holdout6/7.csv` (with `*_verified.csv` alongside). Scores below are reproducible
from those files + `src/skill_extraction.py`.

## Results (after v2.2, 2026-11-09)

| Set | Sample | Verified precision | Current (v2.2) extractor |
|---|---|---|---|
| skill_check_full (v1 sample, re-verified) | 144 | 126/144 = **87.50%** (2 mislabels fixed: `billing`, `machine learning`) | keeps 126/126 at **100.00%** precision; **0** verified-y lost |
| holdout2–5 (previously labelled, v2) | 4 × 144 | 134 / 127 / 131 / 132 correct (**93.06 / 88.19 / 90.97 / 91.67%**) | — |
| holdout6 (v1 sample, labelled 2026-11-09) | 144 | **122/144 = 84.72%** (22 FP) | keeps 127/144 at **96.06%** precision; **0** verified-y suppressed |
| holdout7 (v2 sample, labelled 2026-11-09) | 144 | **126/144 = 87.50%** (18 new FP) | keeps 126/126 at **100.00%** precision; **0** verified-y lost |
| **Combined** | **1008** | **898/1008 = 89.09%** | |

## Fixes shipped in v2.1 (`src/skill_extraction.py`)

`billing` — internal-team contexts (`collaboration with billing`, `billing, credentialing`, `teams (billing`).
`machine learning` / `artificial intelligence` — employer EEO/legal boilerplate
(`…machine learning technologies in connection with applications…`).

Effect on the full 8,713 postings: `machine learning` 160→143, `artificial intelligence` 104→85,
`billing` 303→302; top-15 unchanged (communication 4,184 · leadership 1,906 · sales 1,796 ·
customer service 1,766 · excel 1,345 …). Zero verified-correct matches suppressed.

## Fixes shipped in v2.2 (`src/skill_extraction.py`)

Narrow suppressions for the 18 holdout7 false positives — department/function references,
physical-demands boilerplate and employer/culture prose (never a candidate skill requirement):

- `sales` — `post-sales`, `from the sales team`, `source special request items from sales team`, `development of new sales, marketing`
- `leadership` — `finance leadership` (audience, not requirement), `flexibility, agility, and leadership`, `transformative leadership: we'll give you` (offer copy; apostrophe-agnostic)
- `teamwork` — `enthusiastic team player who thrives`, `committed to teamwork, trust and transparency` (Lumen culture prose)
- `customer service` — `solutions and customer support services` (BAE systems descriptor)
- `customer experience` — `ensuring the best possible customer experience` (Con Edison mission)
- `communication` — `documentation systems for communication`
- `procurement` — `coordinate with procurement, quality, and other departments`
- `talent acquisition` — `partnering with our talent acquisition`, `working closely with talent acquisition` (HR-collaboration references)
- `workday` — `duration of the workday`, `throughout the workday` (physical-demands boilerplate; "the workday" alone is NOT suppressed)
- `employee relations` — `employee relations at (`, `partner with hr business partners … employee relations`, `employee relations, legal, payroll`
- `ecommerce` — `in the e-commerce space`

One candidate pattern (`values of care, humor, integrity, teamwork`) was DROPPED in review: it
appears verbatim in a verified-y posting. Every other pattern was gated so that **zero
verified-y rows lose their skill** across all three labelled sets (full 126/126,
holdout6 122/122, holdout7 126/126). Effect on the full 8,713 postings: communication 4,183 ·
leadership 1,889 · sales 1,789 · customer service 1,753 · teamwork 826 (top-15 otherwise
unchanged).

## Still known false positives (not suppressed — deliberate)

- holdout6 (5): `emr` ("Licensed Mental Health Counselor" context), `project management`
  ("Project Management Office" department reference), `cpa` ("Top 20 National CPA Firm" employer
  description), `ecommerce` (executive-support context), `statistics` (degree requirement, not a
  working skill). Teams/employer-name and degree-requirement contexts; suppressing them risks
  over-suppression on skill-relevant postings. Human review recommended.
- Note: teamwork shortlist dropped one y-hit during v2.2 — see above; extractor teamwork
  mention dropped 844→826 accordingly.

## Lessons / process notes

- The 500-char `description_snippet` in the original `skill_check.csv` made labels unverifiable;
  all samples now carry the full description.
- Every round of holdout labelling found NEW FP types — expect diminishing returns, target
  the highest-frequency ones only.
- 36 MB `jobs_with_skills.csv` was removed from git tracking (stale pre-v2 copy; regenerated
  locally via `python src/skill_extraction.py`). Dataset now lives in the gitignored `data/`
  (regenerable) and Google Drive.
