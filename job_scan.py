import os
from tavily import TavilyClient
from ai_client import ask_ai_json
from db_client import supabase

tavily_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))

TARGET_COMPANIES = [
    "Razorpay", "Swiggy", "PhonePe", "Flipkart", "Meesho", "eBay", "Zomato",
    "Zepto", "CRED", "Groww", "Paytm", "Mastercard", "GitLab"
]

ROLE_KEYWORDS = ["platform engineer", "site reliability engineer", "sre", "devops engineer", "infrastructure engineer"]


def check_readiness() -> dict:
    """
    AI-driven readiness assessment - looks at actual quiz scores and interview
    performance across weeks, not just a rough week-count proxy, to judge
    whether the user is genuinely ready for job scanning to surface results.
    """
    result = supabase.table("scores").select("*").order("created_at").execute()

    if not result.data:
        return {"is_ready": False, "reasoning": "No quiz/interview data yet"}

    summary_lines = []
    for row in result.data:
        summary_lines.append(
            f"Topic: {row.get('topic', 'unknown')}, Gate1: {row.get('gate1_score')}, "
            f"Gate2: {row.get('gate2_score')}, Passed: {row.get('passed')}"
        )
    performance_summary = "\n".join(summary_lines)

    prompt = f"""
You are assessing whether someone is genuinely ready to start applying for Platform Engineer/DevOps/SRE
roles at companies like Razorpay, Swiggy, PhonePe, based on their actual quiz and interview performance
across their study roadmap so far.

Performance so far:
{performance_summary}

The roadmap has 21 weeks total, covering Linux/Bash/Networking through System Design. Job readiness
typically requires solid performance across the majority of foundational and intermediate topics
(roughly through Kubernetes/CI-CD/Terraform level), not just early topics.

Judge genuinely on QUALITY of scores (are Gate1/Gate2 scores consistently strong, not just passing
by a narrow margin), not just quantity of topics attempted.

Return JSON:
{{
  "is_ready": false,
  "reasoning": "brief honest assessment of current readiness level",
  "topics_covered": 5,
  "average_performance": "strong/moderate/weak"
}}
"""
    return ask_ai_json(prompt)


def search_company_jobs(company: str) -> list:
    """Searches for open PE/DevOps/SRE roles at a specific company via Tavily."""
    query = f"{company} careers Platform Engineer OR DevOps Engineer OR SRE job openings India"
    response = tavily_client.search(query=query, max_results=5, search_depth="advanced")
    return response.get("results", [])


def classify_job(title: str, content: str, company: str) -> dict:
    """
    Reads the FULL job description content, not just the title, to determine
    if this is genuinely a PE/DevOps/SRE role - not a DSA-heavy SDE role with
    an ambiguous title.
    """
    prompt = f"""
Evaluate this job posting to determine if it's a genuine Platform Engineer / DevOps / SRE role,
NOT a generic Software Development Engineer (SDE) role, even if the title sounds infrastructure-related.

Company: {company}
Title: {title}
Content: {content[:1500]}

Key signal: does the actual job description mention DSA/algorithms/coding-interview-style requirements
heavily, or does it focus on infrastructure, CI/CD, cloud, monitoring, reliability work?
A title like "Platform Engineer" can still be a DSA-heavy SDE role in disguise - read the actual
responsibilities and requirements, not just the title.

Return JSON:
{{
  "is_genuine_pe_role": true,
  "confidence": 8,
  "reasoning": "brief reason based on actual content, not title alone"
}}
"""
    return ask_ai_json(prompt)


def run_job_scan(force: bool = False):
    """
    Entry point - scans all target companies, saves genuine PE/DevOps matches.
    By default, only SURFACES results once the user is genuinely assessed as
    ready (based on real quiz/interview performance, not just week count).
    Earlier than that, jobs are found and saved but flagged as not surfaced.
    Pass force=True to bypass the gate for testing purposes.
    """
    readiness = check_readiness()
    if not readiness["is_ready"] and not force:
        print(f"[job_scan] Not yet surfacing jobs - {readiness.get('reasoning', 'not ready')}")
        return {"skipped": True, "reason": readiness.get("reasoning"), "readiness_detail": readiness}

    found_jobs = []

    for company in TARGET_COMPANIES:
        try:
            results = search_company_jobs(company)
        except Exception as e:
            print(f"[job_scan] Search failed for {company}: {e}")
            continue

        for result in results:
            title = result.get("title", "")
            content = result.get("content", "")
            url = result.get("url", "")

            if not any(keyword in title.lower() for keyword in ROLE_KEYWORDS):
                continue

            classification = classify_job(title, content, company)

            if classification.get("is_genuine_pe_role") and classification.get("confidence", 0) >= 6:
                supabase.table("jobs").insert({
                    "company": company,
                    "role_title": title,
                    "job_url": url,
                    "is_fit": True,
                    "surfaced": readiness["is_ready"]
                }).execute()
                found_jobs.append({"company": company, "title": title, "url": url})
                print(f"[job_scan] MATCH: {company} - {title}")

    print(f"[job_scan] Scan complete. Found {len(found_jobs)} genuine matches.")
    return found_jobs