import os
from ai_client import ask_ai_json
from db_client import supabase


def score_resume(resume_text: str, job_description: str) -> dict:
    """
    Scores a resume against a specific job description.
    Explicitly aware that the candidate's Azure DevOps experience is roughly
    2 years old (not recent/ongoing), and they are actively training toward
    AWS from scratch - the score must genuinely reflect real hiring risk,
    not just describe gaps in the feedback text while scoring generously.
    """
    prompt = f"""
You are an ATS (Applicant Tracking System) evaluator scoring a resume against a specific job description
for a Platform Engineer / DevOps / SRE role.

IMPORTANT CONTEXT: this candidate's Azure DevOps experience was from roughly 2 years ago, not recent or
ongoing - they are now actively training toward AWS from scratch. Be honest and precise about what
actually transfers versus what doesn't, accounting for this recency gap:
- Even CONCEPTUAL knowledge from 2 years ago should be treated as somewhat rusty, not fresh - credit it,
  but don't treat it as equivalent to active, current experience.
- PRACTICAL, tool-specific transfer (actual hands-on AWS console experience, AWS-specific IAM/networking
  quirks, AWS certification-level depth) is NOT the same as old Azure experience and should be scored as
  a genuine gap, not glossed over.

Resume:
{resume_text[:3000]}

Job Description:
{job_description[:2000]}

Evaluate:
- Keyword/skill match (accounting for transferable but aged cloud platform experience, not just exact
  tool matches)
- Relevant experience depth and recency
- Any genuine gaps worth addressing before applying

Do not overstate readiness - if AWS hands-on experience doesn't exist yet, say so plainly in the feedback,
even while crediting the transferable conceptual foundation. The candidate needs honest signal, not
inflated encouragement.

IMPORTANT - the numeric score must genuinely reflect these gaps, not just the feedback text. If experience
is 2+ years old and not recent, and hands-on experience with the job's core required tools doesn't exist,
the score should be meaningfully lower (reflect real hiring risk) - do not give a moderate/passing-sounding
score (60-70 range) if the actual gaps are this significant. Score honestly low if the gaps are real.

Return JSON:
{{
  "score": 40,
  "matched_skills": ["CI/CD concepts", "IaC concepts (aged)"],
  "gaps": ["specific AWS service depth", "Terraform hands-on projects", "recent hands-on experience"],
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