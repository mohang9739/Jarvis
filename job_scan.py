import os
import requests
from datetime import datetime, timedelta
from db_client import supabase

DISCORD_WEBHOOK = os.getenv('DISCORD_WEBHOOK_URL')

def get_ist_now():
    return datetime.utcnow() + timedelta(hours=5, minutes=30)

def run_job_scan():
    now = get_ist_now()
    
    # Only run from August 25 onwards
    start_scan_date = datetime(2026, 8, 25)
    if now < start_scan_date:
        days_left = (start_scan_date - now).days
        print(f'[job_scan] Job scan starts August 25. {days_left} days remaining. Focus on studying!')
        return

    try:
        from jobspy import scrape_jobs
        import pandas as pd

        print('[job_scan] Scanning jobs...')

        jobs = scrape_jobs(
            site_name=['linkedin', 'indeed', 'glassdoor'],
            search_term='Azure Cloud Engineer',
            location='Bengaluru, India',
            results_wanted=20,
            hours_old=24,
            country_indeed='India'
        )

        if jobs is None or len(jobs) == 0:
            print('[job_scan] No jobs found today')
            return

        # Candidate keywords
        my_keywords = [
            'azure', 'avd', 'virtual desktop', 'terraform', 
            'powershell', 'az-140', 'fslogix', 'entra',
            'infrastructure', 'cloud engineer', 'managed identity',
            'key vault', 'private endpoint', 'hub spoke'
        ]

        # Score each job
        scored_jobs = []
        for _, job in jobs.iterrows():
            title = str(job.get('title', '')).lower()
            description = str(job.get('description', '')).lower()
            company = str(job.get('company', ''))
            salary = str(job.get('min_amount', '')) 

            # Calculate match score
            score = 0
            matched = []
            missing = []

            for kw in my_keywords:
                if kw in title or kw in description:
                    score += 1
                    matched.append(kw)
                else:
                    missing.append(kw)

            match_pct = int((score / len(my_keywords)) * 100)

            # Priority tier
            if match_pct >= 85:
                tier = '🔥 Tier 1'
            elif match_pct >= 70:
                tier = '⚡ Tier 2'
            else:
                tier = '⏳ Tier 3'

            if match_pct >= 70:
                scored_jobs.append({
                    'company': company,
                    'title': str(job.get('title', '')),
                    'location': str(job.get('location', 'Bengaluru')),
                    'salary': salary,
                    'match_pct': match_pct,
                    'tier': tier,
                    'matched': matched[:5],
                    'missing': missing[:3],
                    'url': str(job.get('job_url', '')),
                    'source': str(job.get('site', ''))
                })

        # Sort by match score
        scored_jobs.sort(key=lambda x: x['match_pct'], reverse=True)
        top_jobs = scored_jobs[:5]

        if not top_jobs:
            print('[job_scan] No matching jobs found today')
            return

        # Save to Supabase
        for j in top_jobs:
            try:
                supabase.table('jarvis_job_applications').insert({
                    'company': j['company'],
                    'role': j['title'],
                    'salary': j['salary'],
                    'match_score': j['match_pct'],
                    'tier': j['tier'],
                    'status': 'found',
                    'apply_link': j['url']
                }).execute()
            except:
                pass

        # Build Discord message
        message = f"""━━━━━━━━━━━━━━━━━━━━━━━━━
🔍 AZURE JOB SCAN — {now.strftime('%B %d, %Y')}
━━━━━━━━━━━━━━━━━━━━━━━━━
"""
        for i, j in enumerate(top_jobs, 1):
            message += f"""
**{i}. {j['title']} — {j['company']}**
{j['tier']} | Match: {j['match_pct']}%
📍 {j['location']} | 💰 {j['salary'] or 'Not listed'}
✅ Matched: {', '.join(j['matched'][:3])}
⚠️ Missing: {', '.join(j['missing'][:2])}
🔗 {j['url'][:80]}
"""

        message += f"""
━━━━━━━━━━━━━━━━━━━━━━━━━
📌 Apply to top 2-3 today (20 min)
🔥 Signature line to add:
"Reduced AVD provisioning from 4+ hours
to 18 minutes using Terraform automation"
━━━━━━━━━━━━━━━━━━━━━━━━━"""

        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={'content': message})
            print(f'[job_scan] Sent {len(top_jobs)} jobs to Discord')
        else:
            print(message)

    except Exception as e:
        print(f'[job_scan] Error: {e}')

if __name__ == '__main__':
    run_job_scan()
