from ai_client import ask_ai

BASE_PROFILE = """
NAME: Mohan G
ROLE TARGET: Azure Cloud Infrastructure Engineer
LOCATION: Bengaluru, Karnataka
EMAIL: mohang3011@gmail.com
PHONE: +91 9739314459
LINKEDIN: linkedin.com/in/mohang-13460a1b3
GITHUB: github.com/mohang9739/azure-infra-automation
NOTICE: Available October 1, 2026 (project ending Sept 30)

EXPERIENCE: 4.6 years at Accenture Technology
CURRENT ROLE: Senior Analyst - Azure L2 Support
REAL WORK: AVD profile resets, FSLogix troubleshooting, incident logging BMC Helix

CERTIFICATIONS:
- AZ-140 Azure Virtual Desktop Specialty
- AI-102 Azure AI Engineer Associate  
- AZ-900 Azure Fundamentals

REAL SKILLS (hands-on):
- Azure Virtual Desktop (AVD) - 4.6 years
- FSLogix profile management
- Entra ID basic user management
- Azure portal navigation
- BMC Helix ITSM

BUILDING SKILLS (project):
- Terraform IaC
- PowerShell scripting
- Hub-Spoke VNet design
- Private Endpoints
- Key Vault + Managed Identity
- GitHub Actions CI/CD
- KQL queries

PROJECT: Azure Infrastructure Automation Suite
github.com/mohang9739/azure-infra-automation
METRICS:
- AVD provisioning: 4+ hours → 18 minutes (Terraform)
- Compute cost: 40% reduction (scaling plan)
- Public exposure: Zero (Private Endpoints)
- Credentials in code: Zero (Key Vault + Managed Identity)
- Team conflicts: Zero (Blob lease state locking)

EDUCATION: BE Computer Science, Vemana Institute, 2021, CGPA 7.67
"""

def generate_full_resume(job_title: str, company: str, jd: str, salary: str) -> str:
    prompt = f"""You are an expert resume writer for Azure Cloud Engineer roles in India.

CANDIDATE FACTS (use only these - do not invent):
{BASE_PROFILE}

TARGET JOB: {job_title} at {company}
EXPECTED SALARY: {salary}

JOB DESCRIPTION:
{jd[:2000]}

Write a COMPLETE ATS-optimized resume using the candidate facts above.
Tailor every section to match keywords from this specific JD.
CRITICAL RULE: Every single keyword from the JD MUST appear somewhere in the resume.
Step 1: Find ALL keywords in JD
Step 2: Check which ones are missing
Step 3: Add missing ones to Technical Skills section
Step 4: Add missing ones to Project Technologies line
Step 5: Use missing keywords naturally in project bullet descriptions
Goal: ATS SCORE must be 90%+
Do NOT invent experience but USE exact JD terminology everywhere possible.

Use EXACTLY this format:

MOHAN G
{job_title.upper()} | BENGALURU, KARNATAKA
mohang3011@gmail.com | +91 9739314459
linkedin.com/in/mohang-13460a1b3 | github.com/mohang9739/azure-infra-automation
Available: October 1, 2026 | Expected CTC: {salary}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROFESSIONAL SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[3 sentences tailored to {job_title} at {company}.
Use top 3 keywords from JD. Mention AZ-140 + project metric.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
CERTIFICATIONS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
- Microsoft Certified: Azure Virtual Desktop Specialty (AZ-140)
- Microsoft Certified: Azure AI Engineer Associate (AI-102)
- Microsoft Certified: Azure Fundamentals (AZ-900)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
TECHNICAL SKILLS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
[List skills matching JD keywords first. Group by category.
Include ALL skills from candidate profile.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PROFESSIONAL EXPERIENCE
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Azure Cloud Infrastructure Engineer (Senior Analyst)
Accenture Technology, Bengaluru | December 2021 – Present

[4-5 bullets. Use JD keywords. Frame AVD support experience positively.
Be honest - L2 support and project work. Include real metrics where possible.]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
PERSONAL PROJECT
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Azure Infrastructure Automation Suite | 2026
github.com/mohang9739/azure-infra-automation

[6-8 bullets ordered by JD relevance.
Always include these metrics:
- 4hrs → 18min provisioning
- 40% cost reduction
- Zero public exposure
- Zero credentials in code
Use exact JD keywords in bullets.]

Technologies: [List matching JD keywords first]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
EDUCATION
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Bachelor of Engineering in Computer Science
Vemana Institute of Technology, Bangalore | 2017-2021 | CGPA: 7.67/10"""

    return ask_ai(prompt)

if __name__ == '__main__':
    test_jd = """
    Azure Cloud Engineer - Bengaluru
    4-6 years Azure infrastructure experience
    Terraform IaC required
    Azure Virtual Desktop experience strongly preferred
    PowerShell scripting automation
    Azure networking - VNet NSG Private Endpoints
    Azure Monitor Log Analytics KQL
    AZ-140 or AZ-104 certification preferred
    Hub-Spoke network topology
    Key Vault secrets management
    GitHub Actions CI/CD
    """

    result = generate_full_resume(
        'Azure Cloud Engineer',
        'Wipro',
        test_jd,
        '14-15 LPA'
    )
    print(result)
