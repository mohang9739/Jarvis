import os
import requests
from datetime import datetime, timedelta
from db_client import supabase
from ai_client import ask_ai
from resume_builder import generate_full_resume

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')
SALARY = '14-15 LPA'

def analyze_job(title: str, company: str, jd: str, resume: str = "") -> str:
    prompt = f"""ATS analysis for Azure Cloud Engineer application.

CANDIDATE RESUME:
{resume[:2000] if resume else """
Mohan G | AZ-140, AI-102, AZ-900
4.6 years Azure at Accenture
Terraform, PowerShell, AVD, FSLogix
Hub-Spoke VNet, Private Endpoints, Key Vault
Managed Identity, GitHub Actions, KQL
Azure Monitor, Log Analytics
Azure Infrastructure Automation Suite project
- 4hrs to 18min AVD provisioning
- 40% cost saving
- Zero public exposure
"""}

JOB: {title} at {company}
JD: {jd[:1000]}

Score the resume against the JD.
Respond in exactly this format:
ATS SCORE: X%
MATCHED: keyword1, keyword2, keyword3, keyword4, keyword5
MISSING: keyword1, keyword2 (or None if all matched)
COVER LETTER (80 words): [write here]
WHY JOIN (50 words): [write here]
Q1: [interview question from JD] → A: [answer using candidate project]
Q2: [interview question from JD] → A: [answer using candidate project]
Q3: [interview question from JD] → A: [answer using candidate project]
RECOMMENDATION: Apply immediately / Apply today / Skip"""
    return ask_ai(prompt)

def send_job_package(job: dict):
    title = job.get('title', '')
    company = job.get('company', '')
    jd = job.get('description', '')
    url = job.get('url', '')
    salary = job.get('salary', 'Not listed')
    match_pct = job.get('match_pct', 0)
    tier = job.get('tier', '')

    print(f'[job_apply] Generating package for {title} at {company}...')

    # Generate full tailored resume first
    resume = generate_full_resume(title, company, jd, SALARY)
    
    # Generate ATS analysis using the tailored resume
    analysis = analyze_job(title, company, jd, resume)

    # Resume already generated above

    # Message 1: Job header + ATS analysis
    msg1 = f"""━━━━━━━━━━━━━━━━━━━━━━━━━
🎯 JOB MATCH — {tier}
━━━━━━━━━━━━━━━━━━━━━━━━━
**{title} — {company}**
💰 Salary: {salary}
📊 Match: {match_pct}%
🔗 Apply: {url[:100]}
━━━━━━━━━━━━━━━━━━━━━━━━━

{analysis}

🔥 SIGNATURE LINE (always add):
"Reduced AVD provisioning from 4+ hours to 18 minutes using Terraform automation"
━━━━━━━━━━━━━━━━━━━━━━━━━"""

    # Message 2: Complete tailored resume
    msg2 = f"""━━━━━━━━━━━━━━━━━━━━━━━━━
📄 TAILORED RESUME — {company}
━━━━━━━━━━━━━━━━━━━━━━━━━

{resume}
━━━━━━━━━━━━━━━━━━━━━━━━━"""

    if DISCORD_WEBHOOK:
        # Send analysis
        if len(msg1) > 1900:
            parts = [msg1[i:i+1900] for i in range(0, len(msg1), 1900)]
            for part in parts:
                requests.post(DISCORD_WEBHOOK, json={'content': part})
        else:
            requests.post(DISCORD_WEBHOOK, json={'content': msg1})

        # Send resume
        if len(msg2) > 1900:
            parts = [msg2[i:i+1900] for i in range(0, len(msg2), 1900)]
            for part in parts:
                requests.post(DISCORD_WEBHOOK, json={'content': part})
        else:
            requests.post(DISCORD_WEBHOOK, json={'content': msg2})

        print(f'[job_apply] Full package sent for {title} at {company}')
    else:
        print(msg1)
        print(msg2)

if __name__ == '__main__':
    test_job = {
        'title': 'Azure Cloud Engineer',
        'company': 'Wipro',
        'description': '''
        4-6 years Azure infrastructure experience
        Terraform IaC required
        Azure Virtual Desktop experience preferred
        PowerShell scripting automation
        Azure networking VNet NSG Private Endpoints
        Azure Monitor Log Analytics KQL
        AZ-140 preferred
        Hub-Spoke topology
        Key Vault secrets management
        ''',
        'url': 'https://wipro.com/careers/123',
        'salary': '12-16 LPA',
        'match_pct': 87,
        'tier': '🔥 Tier 1'
    }
    send_job_package(test_job)
