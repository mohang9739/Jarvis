import os

# ─── 1. PRE-EMPTIVE FAILURE DRILLS ────────────────────────────────────────────
failure_drill_code = '''
import random
from datetime import datetime, timedelta

def should_send_failure_drill():
    """Randomly trigger mock outage during study hours (10 AM - 8 PM IST)"""
    now_ist = datetime.utcnow() + timedelta(hours=5, minutes=30)
    hour = now_ist.hour
    if not (10 <= hour <= 20):
        return False
    return random.random() < 0.3  # 30% chance during study hours

def send_failure_drill():
    """Send random production outage to Discord for incident response practice."""
    drills = [
        {
            "title": "P0 INCIDENT — Payment Service Down",
            "scenario": "Razorpay alert: 15,000 transactions/min failing. Payment pods in CrashLoopBackOff. Error rate 94%. Finance team escalating.",
            "task": "You are on-call. You have 10 minutes. What do you do first? Reply in Discord with your diagnosis steps."
        },
        {
            "title": "P1 INCIDENT — Database Connection Pool Exhausted",
            "scenario": "Swiggy alert: PostgreSQL max_connections reached. Orders stalling. API latency 45 seconds. 50,000 active users affected.",
            "task": "Immediate action required. What is your first command and why?"
        },
        {
            "title": "P0 INCIDENT — Kubernetes Node NotReady",
            "scenario": "PhonePe alert: 3 of 5 EKS nodes showing NotReady. Pods evicting. UPI service degraded. RBI SLA breach in 8 minutes.",
            "task": "Walk through your incident response. What do you check first?"
        },
        {
            "title": "P1 INCIDENT — CI/CD Pipeline Blocked",
            "scenario": "CRED alert: GitHub Actions pipeline failing for all PRs. ArgoCD sync stuck. Hotfix for critical bug cannot be deployed. 2 engineers waiting.",
            "task": "Unblock the pipeline. What is your immediate diagnosis?"
        },
        {
            "title": "P0 INCIDENT — Disk Space Critical",
            "scenario": "Groww alert: /var/log on payment server at 99% disk usage. Nginx log rotation failed. Service writes failing silently.",
            "task": "You have 5 minutes before service goes down. What do you do?"
        }
    ]
    drill = random.choice(drills)
    message = f"""
🚨🚨🚨 **JARVIS FAILURE DRILL** 🚨🚨🚨
━━━━━━━━━━━━━━━━━━━━━━━

**{drill['title']}**

{drill['scenario']}

⏱️ **YOUR TASK:** {drill['task']}

*This is a training drill. Respond with your incident response steps.*
━━━━━━━━━━━━━━━━━━━━━━━"""
    return message
'''

# Write failure drill to daily_task.py
content = open('daily_task.py').read()
if 'send_failure_drill' not in content:
    content = content.replace(
        'if __name__ == "__main__":',
        failure_drill_code + '\nif __name__ == "__main__":'
    )
    open('daily_task.py', 'w').write(content)
    print('✓ Pre-emptive Failure Drills added to daily_task.py')

# ─── 2. SMART CATCHUP SUMMARY ─────────────────────────────────────────────────
content = open('daily_task.py').read()
old_main = 'if __name__ == "__main__":\n    send_daily_tasks()'
new_main = '''if __name__ == "__main__":
    # Check if missed yesterday
    missed = check_missed_days()
    if missed:
        print("[daily_task] User missed yesterday - sending catchup briefing")
        now_ist = __import__("datetime").datetime.utcnow() + __import__("datetime").timedelta(hours=5, minutes=30)
        catchup_msg = f"""
━━━━━━━━━━━━━━━━━━━━━━━
🔄 **JARVIS CATCHUP — You missed yesterday**
━━━━━━━━━━━━━━━━━━━━━━━

No judgment. Today we pick up where we left off.

**Quick recap of what you missed:**
Yesterday covered Linux Basics concepts that today builds on.
Open /chat and say "JARVIS give me a quick catchup briefing" 
for a 2-minute audio summary before starting today.

**Today still matters more than yesterday.**
━━━━━━━━━━━━━━━━━━━━━━━"""
        if DISCORD_WEBHOOK:
            requests.post(DISCORD_WEBHOOK, json={"content": catchup_msg})
    send_daily_tasks()'''

if 'check_missed_days' in content and 'send_daily_tasks()' in content:
    content = content.replace(old_main, new_main)
    open('daily_task.py', 'w').write(content)
    print('✓ Smart Catchup Summary added')

# ─── 3. SHADOW SENIOR + ARCHITECTURE ROAST + AI-OPS brain modes ───────────────
pages = ['jarvis_home.html','jarvis_chat.html','jarvis_quiz.html',
         'jarvis_interview.html','jarvis_code.html','jarvis_payflow.html','jarvis_complete.html']

new_buttons = """      <button class="bm-btn" onclick="runBrainMode('shadowsenior','Shadow Senior Mode','Review my answer or code like an aggressive Staff Engineer at Razorpay. Point out every edge case I missed, scalability bottleneck, cost implication, and security flaw. Be direct and unsparing.')">👔 Shadow Senior</button>
      <button class="bm-btn" onclick="runBrainMode('archroast','Architecture Roast','I will describe my PayFlow architecture. Systematically tear it down: find every single point of failure, scaling limit, security vulnerability, and cost leak. Do not hold back. This is a roast.')">🔥 Architecture Roast</button>
      <button class="bm-btn" onclick="runBrainMode('aiops','AI-Ops Defender','Ask me how I would use AI tools in a production DevOps workflow at Razorpay in 2026. What would I automate with AI, what would I never automate, and where does human judgment stay essential?')">🤖 AI-Ops</button>"""

for page in pages:
    if not os.path.exists(page):
        continue
    content = open(page).read()
    if 'brain-panel' not in content:
        continue
    if 'shadowsenior' in content:
        continue
    old = '      <button class="bm-btn" onclick="runBrainMode(\'thinkaloud\''
    if old in content:
        content = content.replace(old, new_buttons + '\n      <button class="bm-btn" onclick="runBrainMode(\'thinkaloud\'')
        open(page, 'w').write(content)
        print(f'✓ New brain modes added to {page}')

# ─── 4. TONE DRIFT + COGNITIVE LOAD in voice_jarvis.py ───────────────────────
content = open('voice_jarvis.py').read()
if 'TONE DRIFT' not in content:
    old = 'CASUAL CONVERSATION:'
    new = '''TONE DRIFT — adapt personality based on context:
- User scoring below 5 consistently: be warmer, more encouraging, simpler explanations
- User scoring above 8 consistently: be more demanding, push harder, no hand-holding
- During incident simulation: shift to fast-paced Incident Commander tone — short sharp commands
- User speaking fast (high WPM > 160): be calming, slow down the pace deliberately
- User has missed days (0 sessions recently): be supportive not judgmental, ease back in gently
- User answers correctly multiple times in a row: increase challenge level naturally

COGNITIVE LOAD DETECTION:
- If user says "I dont understand", "confused", "lost", "what": immediately simplify
- If user gives very short answers (under 5 words): probe deeper or ask if they need a break
- If WPM spikes above 180 AND answer is incomplete: user is anxious, slow them down
- Suggest a 5-minute break if user seems overwhelmed: "Take 5. Come back fresh."

CASUAL CONVERSATION:'''
    content = content.replace(old, new)
    open('voice_jarvis.py', 'w').write(content)
    print('✓ Tone Drift + Cognitive Load Detection added to voice_jarvis.py')

# ─── 5. COST & SECURITY GUARDRAILS as brain mode ──────────────────────────────
guardrail_prompt = "Review my Terraform or Kubernetes code for: 1) Cloud cost leaks (over-provisioned instances, missing auto-scaling, NAT Gateway waste), 2) Security flaws (public S3 buckets, missing encryption, overprivileged IAM, containers running as root), 3) OWASP top risks. Be specific about each issue found."

for page in pages:
    if not os.path.exists(page):
        continue
    content = open(page).read()
    if 'guardrails' in content or 'brain-panel' not in content:
        continue
    old = '      <button class="bm-btn" onclick="runBrainMode(\'monorepo\''
    if old in content:
        new = f'      <button class="bm-btn" onclick="runBrainMode(\'guardrails\',\'Cost & Security Guardrails\',\'{guardrail_prompt}\')">🔒 Cost & Security</button>\n      <button class="bm-btn" onclick="runBrainMode(\'monorepo\''
        content = content.replace(old, new)
        open(page, 'w').write(content)
        print(f'✓ Cost & Security Guardrails added to {page}')

print('\nAll features built successfully!')
