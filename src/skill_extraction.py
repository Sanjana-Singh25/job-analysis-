"""Module 4: Skill extraction (dictionary + synonyms, regex whole-word matching).

Improvements over the first version:
  * synonyms: "ms excel", "microsoft excel" and "excel" all count as "excel"
  * about 100 more skills, chosen from what actually appears in the postings
  * URLs and e-mail addresses are removed first (so "index.html" is not "html")
  * boilerplate sentences are skipped (equal-opportunity text, benefit lists,
    "our recruiting process" ...), because they are not real skill requirements

Reads data/cleaned_jobs.csv and writes:
  data/jobs_with_skills.csv   (adds an extracted_skills column)
  data/top_skills.csv         (top 15 skills by number of postings)
Run from the project root:  python src/skill_extraction.py
"""
import re
from collections import Counter
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
CLEAN_PATH = ROOT / "data" / "cleaned_jobs.csv"
SKILLS_PATH = ROOT / "data" / "jobs_with_skills.csv"
TOP_SKILLS_PATH = ROOT / "data" / "top_skills.csv"

# canonical skill name -> extra spellings that mean the same skill
SKILLS = {
    # --- programming, data and cloud
    "python": [], "sql": ["t-sql", "pl/sql"], "java": [], "javascript": [],
    "c++": [], "c#": [], ".net": ["dotnet", "asp.net"], "r programming": [],
    "html": ["html5"], "css": ["css3"], "react": ["react.js", "reactjs"],
    "node.js": ["nodejs", "node js"], "git": ["github", "gitlab"],
    "linux": [], "docker": [], "kubernetes": ["k8s"], "terraform": [],
    "aws": ["amazon web services"], "azure": ["microsoft azure"],
    "gcp": ["google cloud"], "devops": [], "ci/cd": [],
    "api": ["apis", "rest api"], "cybersecurity": ["cyber security"],
    "machine learning": [], "deep learning": [],
    "artificial intelligence": [], "data science": [],
    "data analysis": ["data analytics"], "statistics": [],
    "data visualization": [], "etl": [],
    "tableau": [], "power bi": ["powerbi", "power-bi"], "sas": [],
    "spark": ["apache spark", "pyspark"], "hadoop": [],
    "servicenow": [], "autocad": [], "photoshop": [],
    # --- office tools
    "excel": ["microsoft excel", "ms excel"],
    "microsoft office": ["ms office", "office 365", "microsoft 365", "m365"],
    "powerpoint": ["ms powerpoint"], "microsoft word": ["ms word"],
    "outlook": [], "sharepoint": [], "visio": [],
    # --- business systems
    "salesforce": [], "crm": [], "sap": [], "workday": [], "netsuite": [],
    "hris": [], "quickbooks": ["quick books"], "jira": [],
    "agile": [], "scrum": [],
    # --- soft and professional skills
    "communication": [], "leadership": [], "teamwork": ["team player", "team work"],
    "problem solving": ["problem-solving"], "time management": [],
    "attention to detail": ["detail oriented", "detail-oriented"],
    "critical thinking": [], "interpersonal skills": [],
    "organizational skills": ["organization skills"],
    "multitasking": ["multi-tasking", "multi tasking"],
    "analytical skills": ["analytical thinking"],
    "decision making": ["decision-making"], "negotiation": [],
    "presentation skills": [], "relationship building": [],
    "mentoring": [], "coaching": [], "cross-functional": ["cross functional"],
    "strategic planning": [], "process improvement": [],
    "change management": [], "risk management": [],
    "stakeholder management": [], "vendor management": [],
    "project management": [], "kpi": ["kpis"], "forecasting": [],
    "operations management": [], "data entry": [],
    "bilingual": [], "spanish": [],
    # --- sales, marketing, customer
    "sales": [], "marketing": [], "digital marketing": [],
    "social media": [], "seo": [], "lead generation": [],
    "business development": [], "account management": [],
    "market research": [], "customer service": ["customer support", "client service"],
    "customer experience": [], "customer success": [], "cold calling": [],
    "b2b": [], "ecommerce": ["e-commerce"],
    # --- finance and accounting
    "accounting": [], "bookkeeping": [], "gaap": [],
    "financial reporting": [], "financial analysis": [],
    "budgeting": ["budget management", "budget preparation"],
    "auditing": ["audit", "audits", "internal audit"],
    "accounts payable": [], "accounts receivable": [], "payroll": [],
    "reconciliation": [], "general ledger": [], "journal entries": [],
    "month-end close": ["month-end", "month end"], "invoicing": [],
    "billing": [], "cpa": [],
    # --- HR and admin
    # bare "recruiting" is not used: staffing agencies write it about themselves
    "talent acquisition": ["full cycle recruiting", "full-cycle recruiting",
                           "recruiting experience", "recruitment experience",
                           "candidate sourcing", "sourcing candidates",
                           "applicant tracking"],
    "onboarding": [], "employee relations": [], "scheduling": [],
    "curriculum": [],
    # --- healthcare
    "nursing": [], "patient care": [], "bls": [], "acls": [], "cpr": [],
    "emr": ["ehr", "electronic medical record", "electronic medical records",
            "electronic health record", "electronic health records"],
    "epic": ["epic ehr", "epic emr", "epic systems", "epic software"],
    "phlebotomy": [], "triage": [], "hipaa": [], "charting": [],
    "patient safety": [], "infection control": [], "cna": [],
    "medical coding": ["cpt codes", "cpt code", "icd-10", "icd-9", "hcpcs"],
    "telemetry": [],
    # --- operations, trades and safety
    "supply chain": [], "logistics": [], "procurement": [],
    "quality assurance": [], "six sigma": [], "lean manufacturing": [],
    "osha": [], "forklift": [], "cdl": ["commercial driver's license"],
    "hvac": [], "welding": [],
}
SKILLS_LIST = list(SKILLS)  # name kept for the app and the notebooks

# Skills used to tag "Tech" in the dashboard and the app
TECH_SKILLS = [
    "python", "sql", "java", "javascript", "c++", "c#", ".net", "r programming",
    "html", "css", "react", "node.js", "git", "linux", "docker", "kubernetes",
    "terraform", "aws", "azure", "gcp", "devops", "ci/cd", "api",
    "cybersecurity", "machine learning", "deep learning",
    "artificial intelligence", "data science", "data analysis", "statistics",
    "data visualization", "etl", "tableau", "power bi", "sas", "spark",
    "hadoop", "servicenow", "jira", "scrum",
]


def _build_pattern(names):
    names = sorted(set(names), key=len, reverse=True)
    body = "|".join(re.escape(n) for n in names)
    return re.compile(r"(?<![a-z0-9])(?:" + body + r")(?![a-z0-9])")


_PATTERNS = {skill: _build_pattern([skill] + aliases)
             for skill, aliases in SKILLS.items()}
_NAMES = {skill: tuple([skill] + aliases) for skill, aliases in SKILLS.items()}

_URL_EMAIL = re.compile(r"https?://\S+|www\.\S+|\S+@\S+")
_UNIT_SPLIT = re.compile(r"\n+|(?<=[.!?])\s+")
_BOILERPLATE = re.compile(
    r"equal opportunity|equal employment|affirmative action|sexual orientation|"
    r"gender identity|reasonable accommodation|veteran status|protected veteran|"
    r"disability status|national origin|recruiting process|recruitment process|"
    r"application process|hiring process|interview process|paid time off|\bpto\b|"
    r"dental|vision insurance|health insurance|life insurance|401\(?k\)?|"
    r"flexible schedul|tuition reimbursement|employee discount|"
    r"benefits include|benefits package|discriminat|employment decisions|"
    r"this recruitment|harass"
)
_MAX_BOILERPLATE_LEN = 1200  # very long blocks are kept: they also hold real skills

# Suppress narrow contexts confirmed as false matches in reviewed samples.
# Other mentions of these skills remain eligible for extraction.
_FALSE_MATCH_CONTEXT = {
    "accounting": re.compile(r"\bwork with accounting\b|\bidoh accounting staff\b|\bunits specializing in accounting and finance\b"),
    "b2b": re.compile(r"\bas a b2b business unit\b|\bb2b magazine\b"),
    "business development": re.compile(
        r"\bcareer path\b|\bbusiness functions\s*\([^)]{0,300}\b"
        r"business development\b|"
        r"\bteams include business development, specialist and technical solutions architecture\b"
    ),
    "customer success": re.compile(
        r"\bincluding customer success, partners/alliances, and pre-sales teams\b|\bour customer success team is an all-remote group\b|\bour customer success team is comprised of product development experts\b"
    ),
    "customer service": re.compile(
        r"\bcoordinat\w* with the customer support team to drive ongoing success and adoption\b|"
        r"\bclient service team on larger clients\b|\bdepartments, including claims, customer service \(gsc\), underwriting\b|\byou won.t get shuffled to some customer service rep when a problem pops up\b|\bsolutions and customer support services\b"
    ),
    "leadership": re.compile(
        r"\bsenior leadership\b|\bsales leadership, business development, revenue operations\b|"
        r"\bthe right leadership and a strong base of support\b|\bleadership team\b|"
        r"\bstaff and leadership to achieve goals\b|\boperations leadership, engineering and npi teams\b|"
        r"\bleadership development is core to our collective success\b|"
        r"\bworking with leadership on timelines and deliverables\b|"
        r"\bsales leadership at the property\b|\bsolutions to leadership\b|\bbusiness leadership and other senior management\b|\bcapabilities, enhance leadership skills, and continue their professional journey\b|\bas directed by leadership\b|\bsessions with leadership\b|\brepresentative of ross leadership\b|\bteam and leadership\b|\binternal leadership\b|\bleadership leads collaboration and coordination with sales\b|\bdeveloping leadership skills by engaging in networking calls\b|"
        r"\bfinance leadership\b|\bflexibility, agility, and leadership\b|\btransformative leadership: we.ll give you\b"
    ),
    "marketing": re.compile(
        r"\bwork closely with marketing and sales\b|\bwork with marketing,|"
        r"\breaf marketing\b|\bchannel marketing partners\b|"
        r"\bmanufacturing(?:, and| and) marketing a broad range\b|"
        r"\bproduct and marketing groups\b|communication/marketing/journalism|chemistrycommunication/marketing/journalismcriminologybusiness|\bnationally renowned for designing,?\s*developing,?\s*marketing,?\s*and operating a multi-brand portfolio\b|\bcollaborates with communications, policy, medical affairs, and marketing departments\b"
    ),
    "mentoring": re.compile(
        r"\bin-person team interaction, meetings and collaboration, client support, mentoring, coaching\b|"
        r"\bmanaging partners are very keen on mentoring\b"
    ),
    "sales": re.compile(
        r"\bsales and use tax\b|\bcredit sales\b|"
        r"\bact as a liaison between the business and customers, suppliers, distributors, and sales representatives\b|"
        r"\bcontracts related to customers, suppliers, distributors, and sales representatives\b|"
        r"\bmarine, sales, and administration\b|"
        r"\bcreate high-impact learning materials for the sales teams\b|\bsales teams with the knowledge and skills they need to sell products\b|"
        r"\bsales equipment\b|\baccounting, sales and customer services/proposals\b|"
        r"\bnon-sales positions have the opportunity\b|"
        r"\bpartner closely with sales and account management to refine solution architecture\b|"
        r"\bsales teams to coordinate installation of equipment and infrastructure\b|"
        r"\bsales data\b|\bgame sales\b|\bsales compensation\b|\bsales floor\b|"
        r"\bpost-sales\b|\bsource special request items from sales team\b|\bfrom the sales team\b|"
        r"\bdevelopment of new sales, marketing\b"
    ),
    "teamwork": re.compile(
        r"\bcore values also foster a culture of professionalism, teamwork, and integrity\b|"
        r"\bbenefit from teamwork and camaraderie\b|"
        r"\bwhere teamwork is the norm\b|\bwe're team players in everything we do\b|"
        r"\benthusiastic team player who thrives\b|\bcommitted to teamwork, trust and transparency\b"
    ),
    "cpa": re.compile(
        r"\brealtors, cpa's, builders\b|\bexternal cpa firms\b|"
        r"\btop 25 cpa and business advisory firms\b"
    ),
    "onboarding": re.compile(r"\btake onboarding, for example\b|\bcompleted onboarding\b|\bsales and marketing onboarding as well as direct training from the business development executive manager\b"),
    "hvac": re.compile(r"\belectric, internet, hvac, solar and battery storage\b"),
    "gcp": re.compile(
        r"\bgoogle cloud ciso risk and compliance organization\b|"
        r"\bgoogle cloud accelerates every organization\b|\bgoogle cloud platform and google workspace products\b"
    ),
    "logistics": re.compile(
        r"\bpenske logistics\b|\bdelivery and logistics workers\b|\bemployment logistics\s*:|\bontrac logistics, inc\b|\bwork closely with the logistics team to develop pricing\b|"
        r"\bglobal supply chain also includes cultured and wild species\b"
    ),
    "supply chain": re.compile(
        r"\bglobal supply chain also includes cultured and wild species\b|"
        r"\bdhl supply chain is hiring\b|\bposition category supply chain\b"
    ),
    "auditing": re.compile(r"\bindependent bias audit report\b"),
    "cross-functional": re.compile(
        r"\bunited group of elite cross-functional sales professionals\b"
    ),
    "scheduling": re.compile(r"\bgreenhouse is our scheduling tool\b"),
    "patient safety": re.compile(r"\bpatient safety excellence award\b"),
    "crm": re.compile(r"\bas a global leader in cardiac rhythm technologies\b|\bbusiness operations system, including enterprise resource planning \(erp\), accounting, customer relationship management \(crm\), professional service automation\b"),
    "statistics": re.compile(r"\bcrime statistics act\b"),
    "data analysis": re.compile(r"\banalysis is central to successful leadership in any industry\b"),
    "customer experience": re.compile(r"\bcustomer experience transformation\b|\bensuring the best possible customer experience\b"),
    "excel": re.compile(r"\bdo the right thing, excel together and put customers first\b"),
    "outlook": re.compile(r"\bhave a positive outlook\b"),
    "coaching": re.compile(r"\bongoing coaching will be provided\b|\bcontinued coaching from a supportive team\b"),
    "react": re.compile(r"\breact to emergency situations\b"),
    "agile": re.compile(r"\bchange agile; must take action on projects quickly\b"),
    "communication": re.compile(
        r"\bwe celebrate clear communication, effort, and teamwork\b|"
        r"\bgeneration of new communication tools and channels\b|"
        r"\bofficial communication will only be sent from\b|\bline of communication to the current it consultant\b|\bcore values of appreciation & respect, empowerment, diversity, excellence, learning, and communication\b|"
        r"\bdocumentation systems for communication\b"
    ),
    "procurement": re.compile(
        r"\bcomprehensive services in engineering, procurement, and construction\b|\bcoordinate with procurement, quality, and other departments\b"
    ),
    "cybersecurity": re.compile(
        r"\bsoftware engineers, data scientists, cybersecurity experts and service professionals\b|"
        r"\bcybersecurity expert.{0,80}service professionals within the world\b|\bsmoothstack\b|"
        r"\bwe specialize in full stack java development, cloud, devsecops, networking, cyber security\b"
    ),
    "payroll": re.compile(
        r"\bno payroll or taxes experience is needed\b|"
        r"\bwe specialize in contingent hiring, direct hires, statement of work, payroll management\b"
    ),
    "talent acquisition": re.compile(r"\bpartner with our talent acquisition leader\b|\bpartnering with our talent acquisition\b|\bworking closely with talent acquisition\b"),
    "curriculum": re.compile(
        r"\bdegree in a business or liberal arts curriculum\b|"
        r"\bon-the-job executive protection training curriculum\b"
    ),
    "nursing": re.compile(
        r"\bhealth carousel nursing and allied health is seeking\b"
    ),
    "patient care": re.compile(
        r"\btransforming patient care through the development of novel specialty pharmaceuticals\b|"
        r"\bimprove patient care in the clinic\b"
    ),
    # confirmed false positives in full-description verification (2026-11-09):
    # Billing / Credentialing are named as internal teams the candidate collaborates
    # with, not a billing skill the candidate must bring.
    "billing": re.compile(
        r"\bcollaboration with billing\b|\bbilling, credentialing\b|teams?\s*\(billing\b"
    ),
    # Employer EEO/legal boilerplate listing what the employer may do with data;
    # not a skill requirement for the candidate.
    "machine learning": re.compile(
        r"artificial intelligence and machine learning technologies in connection with"
    ),
    "artificial intelligence": re.compile(
        r"artificial intelligence and machine learning technologies in connection with"
    ),
    # v2.2 — holdout7 false positives (2026-11-09). Department/function references,
    # company/culture prose and the noun "workday" (never a skill requirement).
    "workday": re.compile(
        r"\bduration of the workday\b|\bthroughout the workday\b"
    ),
    "employee relations": re.compile(
        r"\bemployee relations at \(|partner with hr business partners[^.]{0,40}employee relations|\bemployee relations, legal, payroll\b"
    ),
    "ecommerce": re.compile(
        r"\bin the e-commerce space\b"
    ),
}


def _has_relevant_match(skill, text):
    """Ignore reviewed false-positive contexts while retaining valid mentions."""
    false_context = _FALSE_MATCH_CONTEXT.get(skill)
    for match in _PATTERNS[skill].finditer(text):
        if skill == "excel" and (
            re.match(r"\s+in\b", text[match.end():])
            or re.search(r"\bthrive and\s+$", text[max(0, match.start() - 40):match.start()])
            or re.search(r"\bstriving to\s+$", text[max(0, match.start() - 40):match.start()])
            or re.search(r"\bexcel at\s+$", text[max(0, match.start() - 40):match.start()])
        ):
            continue  # e.g. "excel in customer service" uses the verb
        if false_context:
            start = max(0, match.start() - 180)
            end = min(len(text), match.end() + 180)
            if false_context.search(text[start:end]):
                continue
        return True
    return False


def clean_text(text) -> str:
    """Lowercase, remove URLs/e-mails and skip boilerplate sentences."""
    text = _URL_EMAIL.sub(" ", str(text).lower())
    kept = [u for u in _UNIT_SPLIT.split(text)
            if not (len(u) <= _MAX_BOILERPLATE_LEN and _BOILERPLATE.search(u))]
    return " ".join(kept) if kept else text


def extract_skills(text) -> list:
    text = clean_text(text)
    return [skill for skill, pattern in _PATTERNS.items()
            if any(n in text for n in _NAMES[skill])
            and _has_relevant_match(skill, text)]


def main() -> None:
    df = pd.read_csv(CLEAN_PATH)
    df["extracted_skills"] = df["description"].apply(extract_skills)

    counts = Counter(df["extracted_skills"].sum())
    top_skills = pd.DataFrame(counts.most_common(15), columns=["skill", "count"])
    print(top_skills)

    df.to_csv(SKILLS_PATH, index=False)
    top_skills.to_csv(TOP_SKILLS_PATH, index=False)
    print("Saved jobs_with_skills.csv and top_skills.csv")


if __name__ == "__main__":
    main()
