import os
from ai_client import ask_ai_json
from db_client import supabase


def score_resume(resume_text: str, job_description: str) -> dict:
    """
    Scores a resume against a specific job description.
    Explicitly aware that the candidate's background may show a platform
    transition (e.g. Azure DevOps experience, actively training toward AWS) -
    this should be read as relevant transferable experience, not a mismatch.
    """
    prompt = f"""
You are an ATS (Applicant Tracking System) evaluator scoring a resume against a specific job description
for a Platform Engineer / DevOps / SRE role.

IMPORTANT CONTEXT: this candidate's first real project used Azure DevOps, and they are actively training
toward AWS from scratch. Be honest and precise about what actually transfers versus what doesn't:
- CONCEPTUAL transfer (understanding CI/CD principles, IaC philosophy, container orchestration concepts)
  is real and should be credited.
- PRACTICAL, tool-specific transfer (actual hands-on AWS console experience, AWS-specific IAM/networking
  quirks, AWS certification-level depth) is NOT the same as Azure experience and should be scored as a
  genuine gap, not glossed over as "highly transferable."
Do not overstate readiness - if AWS hands-on experience doesn't exist yet, say so plainly in the feedback,
even while crediting the transferable conceptual foundation. The candidate needs honest signal, not
inflated encouragement.

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:2000]}

Evaluate:
- Keyword/skill match (accounting for transferable cloud platform experience, not just exact tool matches)
- Relevant experience depth
- Any genuine gaps worth addressing before applying

Return JSON:
{{
  "score": 65,
  "matched_skills": ["CI/CD", "containerization", "infrastructure as code"],
  "gaps": ["specific AWS service depth", "Terraform hands-on projects"],
  "feedback": "2-3 sentences of honest, specific feedback - not generic encouragement"
}}
"""
    return ask_ai_json(prompt)


def run_resume_ats(resume_text: str, job_description: str, job_title: str = ""):
    """Entry point - scores resume against a JD, saves result."""
    result = score_resume(resume_text, job_description)

    supabase.table("resume_scores").insert({
        "jd_text": job_description[:2000],
        "score": result.get("score", 0),
        "feedback": result.get("feedback", "")
    }).execute()

    print(f"[resume_ats] Score: {result.get('score')}/100")
    print(f"[resume_ats] Matched: {result.get('matched_skills')}")
    print(f"[resume_ats] Gaps: {result.get('gaps')}")
    print(f"[resume_ats] Feedback: {result.get('feedback')}")

    return result
