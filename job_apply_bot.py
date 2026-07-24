import os
import requests
from datetime import datetime, timedelta
from db_client import supabase
from ai_client import ask_ai

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')

CANDIDATE_PROFILE = """
Name: Mohan G
Experience: 4.6 years Azure Cloud Infrastructure at Accenture
Certifications: AZ-140 Azure Virtual Desktop Specialty, AI-102 Azure AI Engineer, AZ-900
Location: Bengaluru, Karnataka
Available: October 1, 2026
Salary expectation: 14-15 LPA

Current Skills:
- Azure Virtual Desktop (AVD) - 4.6 years
- FSLogix profile management
- Entra ID / Azure AD
- Azure Monitor and Log Analytics
- BMC Helix ITSM

Building Skills (8-week roadmap):
- Terraform IaC
- PowerShell scripting
- Hub-Spoke VNet topology
- Private Endpoints
- Azure Key Vault
- Managed Identity
- GitHub Actions CI/CD

Project: Azure Infrastructure Automation Suite
- Reduced AVD provisioning from 4+ hours to 18 minutes using Terraform
- PowerShell health monitor auto-drains unhealthy AVD hosts
- Azure OpenAI with Private Endpoint zero public exposure
- GitHub: github.com/mohang9739/azure-infra-automation

Signature line:
"Reduced AVD provisioning from 4+ hours to 18 minutes using Terraform automation"
"""

def analyze_job(job_description: str) -> str:
    prompt = f"""You are a career coach helping an Azure Cloud Engineer apply for jobs.

CANDIDATE PROFILE:
{CANDIDATE_PROFILE}

JOB DESCRIPTION:
{job_description}

Generate exactly this format:

MATCH SCORE: X%

MATCHED KEYWORDS:
- keyword1
- keyword2
- keyword3

MISSING KEYWORDS:
- keyword1
- keyword2

TAILORED RESUME BULLETS:
- [bullet 1 - specific to this job using candidate metrics]
- [bullet 2 - specific to this job using candidate metrics]

COVER LETTER (80 words max):
[Write cover letter here]

WHY JOIN ANSWER (50 words):
[Write why join answer here]

TOP 3 INTERVIEW QUESTIONS FROM THIS JD:
1. [Question] → Your answer: [Answer using candidate project]
2. [Question] → Your answer: [Answer using candidate project]
3. [Question] → Your answer: [Answer using candidate project]

Keep everything specific to the candidate profile. Use real metrics."""

    response = ask_ai(prompt)
    return response

def send_job_analysis(job_description: str):
    print('[job_apply] Analyzing job description...')
    analysis = analyze_job(job_description)
    
    message = f"""━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 JOB APPLICATION PACKAGE
━━━━━━━━━━━━━━━━━━━━━━━━━
{analysis}

🔥 ALWAYS ADD THIS SIGNATURE LINE:
"Reduced AVD provisioning from 4+ hours
to 18 minutes using Terraform automation"

⚠️ FOR MISSING SKILLS ADD:
"Currently strengthening [skill] knowledge
as part of continuous learning"
━━━━━━━━━━━━━━━━━━━━━━━━━"""

    if DISCORD_WEBHOOK:
        # Split if too long
        if len(message) > 2000:
            parts = [message[i:i+1900] for i in range(0, len(message), 1900)]
            for part in parts:
                requests.post(DISCORD_WEBHOOK, json={'content': part})
        else:
            requests.post(DISCORD_WEBHOOK, json={'content': message})
        print('[job_apply] Analysis sent to Discord')
    else:
        print(message)

if __name__ == '__main__':
    # Test with sample JD
    test_jd = """
    Azure Cloud Engineer - Bengaluru
    
    Requirements:
    - 3-6 years Azure infrastructure experience
    - Terraform or ARM templates
    - Azure Virtual Desktop (AVD) experience preferred
    - PowerShell scripting
    - Azure networking (VNet, NSG, Private Endpoints)
    - Azure Monitor and Log Analytics
    - AZ-104 or AZ-140 certification preferred
    """
    send_job_analysis(test_jd)
