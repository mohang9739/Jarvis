import os
from ai_client import ask_ai, ask_ai_json
from db_client import supabase

CANDIDATE_PROFILE = """
Name: Mohan G
Experience: 4.6 years Azure Cloud Infrastructure at Accenture
Certifications: AZ-140 Azure Virtual Desktop Specialty, AI-102 Azure AI Engineer, AZ-900
Location: Bengaluru, Karnataka
Available: October 1, 2026
Notice Period: Available October 1 naturally (project ends September 30)
Salary expectation: 14-15 LPA

Skills:
- Azure Virtual Desktop (AVD) - 4.6 years hands-on
- FSLogix profile management and troubleshooting
- Entra ID / Azure AD - user management, RBAC
- Azure Monitor and Log Analytics
- Hub-Spoke VNet architecture
- Private Endpoints and Managed Identity
- Azure Key Vault secrets management
- Terraform IaC (learning + building project)
- PowerShell scripting for Azure automation
- GitHub Actions CI/CD pipeline
- KQL queries for Azure Monitor
- BMC Helix ITSM incident management

Project: Azure Infrastructure Automation Suite
- Reduced AVD provisioning from 4+ hours to 18 minutes using Terraform
- PowerShell health monitor auto-drains unhealthy AVD hosts proactively
- Azure OpenAI with Private Endpoint - zero public exposure
- Hub-Spoke network topology with complete spoke isolation
- Azure Key Vault + Managed Identity - zero credentials in code
- GitHub Actions CI/CD - no manual deployments
- GitHub: github.com/mohang9739/azure-infra-automation

Signature line:
Reduced AVD provisioning from 4+ hours to 18 minutes using Terraform automation
"""

def score_resume(resume_text: str, job_description: str) -> dict:
    prompt = f"""You are an ATS evaluator scoring an Azure Cloud Engineer resume.

CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

RESUME:
{resume_text[:2000]}

JOB DESCRIPTION:
{job_description[:2000]}

Return ONLY valid JSON in this exact format:
{{
  "ats_score": 85,
  "matched_keywords": ["keyword1", "keyword2"],
  "missing_keywords": ["keyword1", "keyword2"],
  "tailored_bullets": ["bullet1", "bullet2"],
  "summary_line": "one line summary tailored to this job",
  "cover_letter": "80 word cover letter",
  "why_join": "50 word why join answer",
  "interview_questions": [
    {{"question": "Q1", "answer": "A1 using candidate project"}},
    {{"question": "Q2", "answer": "A2 using candidate project"}},
    {{"question": "Q3", "answer": "A3 using candidate project"}}
  ],
  "missing_skills_response": "how to address missing skills",
  "recommendation": "apply or skip"
}}"""

    result = ask_ai_json(prompt)
    return result

def format_discord_message(score_data: dict, company: str = '', role: str = '') -> str:
    if not score_data:
        return "Error analyzing job description"

    score = score_data.get('ats_score', 0)
    
    if score >= 85:
        tier = '🔥 TIER 1 — Apply immediately'
    elif score >= 70:
        tier = '⚡ TIER 2 — Apply today'
    else:
        tier = '⏳ TIER 3 — Consider skipping'

    matched = score_data.get('matched_keywords', [])
    missing = score_data.get('missing_keywords', [])
    bullets = score_data.get('tailored_bullets', [])
    cover = score_data.get('cover_letter', '')
    why = score_data.get('why_join', '')
    questions = score_data.get('interview_questions', [])
    missing_response = score_data.get('missing_skills_response', '')
    recommendation = score_data.get('recommendation', '')

    message = f"""━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 ATS ANALYSIS {f'— {role} at {company}' if company else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━

📊 **ATS SCORE: {score}%**
{tier}

✅ **MATCHED KEYWORDS:**
{chr(10).join(f'• {k}' for k in matched[:8])}

⚠️ **MISSING KEYWORDS:**
{chr(10).join(f'• {k}' for k in missing[:5])}

📝 **TAILORED RESUME BULLETS:**
{chr(10).join(f'• {b}' for b in bullets)}

✉️ **COVER LETTER (80 words):**
{cover}

💬 **WHY JOIN (50 words):**
{why}

❓ **TOP 3 INTERVIEW QUESTIONS:**
{chr(10).join(f'{i+1}. Q: {q.get("question", "")}' + chr(10) + f'   A: {q.get("answer", "")}' for i, q in enumerate(questions[:3]))}

🔧 **MISSING SKILLS RESPONSE:**
{missing_response}

🔥 **SIGNATURE LINE (always include):**
"Reduced AVD provisioning from 4+ hours
to 18 minutes using Terraform automation"

✅ **RECOMMENDATION:** {recommendation}
━━━━━━━━━━━━━━━━━━━━━━━━━"""

    return message

def run_ats_check(resume_text: str, job_description: str, company: str = '', role: str = ''):
    print('[ats] Analyzing job description...')
    score_data = score_resume(resume_text, job_description)
    message = format_discord_message(score_data, company, role)
    print(message)
    return score_data

if __name__ == '__main__':
    # Test
    test_resume = """
    Mohan G - Azure Cloud Infrastructure Engineer
    4.6 years Accenture
    AZ-140, AI-102, AZ-900 certified
    Azure Virtual Desktop, FSLogix, Terraform, PowerShell
    """
    
    test_jd = """
    Azure Cloud Engineer - Bengaluru
    4-6 years Azure infrastructure
    Terraform or ARM templates
    AVD experience preferred
    PowerShell scripting
    Azure networking - VNet NSG Private Endpoints
    Azure Monitor KQL
    AZ-104 or AZ-140 preferred
    """
    
    run_ats_check(test_resume, test_jd, 'Wipro', 'Azure Cloud Engineer')
