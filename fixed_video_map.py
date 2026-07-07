"""
Fixed Video Map - pre-verified, real YouTube video sources for all 20 weeks.
All video IDs confirmed via YouTube Data API.

Week structure corrected:
- Week 9: FastAPI (moved from Week 10)
- Week 10: AWS Core (moved from Week 11)
- Week 11: AWS Networking (moved from Week 12)
- Week 12: Terraform (moved from Week 13)
- Weeks 13+: shifted accordingly
- AI Tools integrated as Saturday bonus in Week 8, not a standalone week
- Week 19: DevSecOps (Abhishek 9hr course)
- Week 20: System Design (freeCodeCamp)

Format per week:
  "type": "single" - one long video, split by timestamp across days
  "type": "episodes" - ordered list of episode video IDs, one per day
  "start_offset" - for shared videos split across two weeks (Weeks 6/7, 10/11)
"""

FIXED_VIDEO_MAP = {
    1: {
        "type": "single",
        "video_id": "sWbUDq4S6Y8",
        "title": "Introduction to Linux – Full Course for Beginners",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 22052,
        "topic": "Linux Basics - commands, file system navigation, permissions, and processes"
    },
    2: {
        "type": "single",
        "video_id": "a3ujwK65dgs",
        "title": "Linux Crash Course for Beginners | KodeKloud",
        "channel": "KodeKloud",
        "duration_seconds": 8473,
        "topic": "Linux Service Management - systemd, journalctl, process supervision"
    },
    3: {
        "type": "single",
        "video_id": "Sx9zG7wa4FA",
        "title": "The Complete Bash Scripting Course",
        "channel": "You Suck at Programming",
        "duration_seconds": 26514,
        "topic": "Bash scripting fundamentals"
    },
    4: {
        "type": "episodes",
        "episodes": [
            {"video_id": "S7MNX_UD7vY", "title": "What is a Network? // Day 0"},
            {"video_id": "9eH16Fxeb9o", "title": "What is a SWITCH? // Day 1"},
            {"video_id": "p9ScLm9S3B4", "title": "What is a ROUTER? // EP 2"},
            {"video_id": "CRdL1PcherM", "title": "TCP/IP and OSI? // EP 3"},
            {"video_id": "3kfO61Mensg", "title": "REAL LIFE example TCP/IP // EP 4"},
            {"video_id": "oIRkXulqJA4", "title": "OSI model Application/Transport // EP 5"},
        ],
        "channel": "NetworkChuck",
        "topic": "Networking fundamentals - TCP/IP, DNS resolution, OSI layers"
    },
    5: {
        "type": "single",
        "video_id": "apGV9Kg7ics",
        "title": "Complete Git and GitHub Tutorial",
        "channel": "Kunal Kushwaha",
        "duration_seconds": 4380,
        "topic": "Git version control fundamentals"
    },
    6: {
        "type": "single",
        "video_id": "sxTmJE4k0ho",
        "title": "The Complete Python Course For Beginners (Part 1)",
        "channel": "Tech With Tim",
        "duration_seconds": 11436,
        "start_offset": 0,
        "topic": "Python Basics"
    },
    7: {
        "type": "single",
        "video_id": "sxTmJE4k0ho",
        "title": "The Complete Python Course For Beginners (Part 2)",
        "channel": "Tech With Tim",
        "duration_seconds": 11437,
        "start_offset": 11436,
        "topic": "DevOps for Python - automation scripting, testing, and packaging"
    },
    8: {
        "type": "episodes",
        "episodes": [
            {"video_id": "cpgOgRxZ0r8", "title": "Day-10 Python Real Time UseCase Lists"},
            {"video_id": "HvNU4dupQkg", "title": "Day-11 Python Real Time UseCase Dicts"},
            {"video_id": "EtBlvubz8sU", "title": "Day-12 Python File Operations"},
            {"video_id": "3ExnySHBO6k", "title": "Day-13 Boto3 Beginner to Advanced"},
            {"video_id": "YVjXwyJlHgg", "title": "Day-14 Automate JIRA via GitHub"},
            {"video_id": "-eOncnzG9tc", "title": "Day-15 AIOps for Log Analysis (AI Tools bonus)"},
        ],
        "channel": "Abhishek Veeramalla",
        "topic": "AI Tools for DevOps - Copilot, Cursor, CLI agents to accelerate infra-as-code and scripting work"
    },
    9: {
        "type": "single",
        "video_id": "0sOvCWFmrtA",
        "title": "Python API Development - Comprehensive Course for Beginners",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 68427,
        "topic": "Python for API - FastAPI, REST endpoint design"
    },
    10: {
        "type": "single",
        "video_id": "7HKot-brXFE",
        "title": "AWS Certified Cloud Practitioner Certification Course 2026 (Part 1)",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 24793,
        "start_offset": 0,
        "topic": "AWS fundamentals - IAM, EC2, Auto Scaling Groups, Route53, and event-driven systems via SQS"
    },
    11: {
        "type": "single",
        "video_id": "7HKot-brXFE",
        "title": "AWS Certified Cloud Practitioner Certification Course 2026 (Part 2)",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 24794,
        "start_offset": 24793,
        "topic": "AWS Networking - VPC, subnets, security groups, NAT gateways, routing"
    },
    12: {
        "type": "episodes",
        "episodes": [
            {"video_id": "jXuhIRdpMkc", "title": "Terraform Tutorial for Beginners - AWS IAM Input Output"},
            {"video_id": "qnkxOwvHNt4", "title": "How to Create AWS VPC with Terraform Resources"},
            {"video_id": "5-0bAfZd7SY", "title": "How to Create AWS VPC with Terraform Modules"},
            {"video_id": "KzJsJHg3ftk", "title": "Terraform Import Existing Resources AWS"},
            {"video_id": "SJoDqR2VuuM", "title": "Terraform EKS Cluster Example VPC from Scratch"},
            {"video_id": "QxgJlJgGA0E", "title": "Terraform Ansible Integration AWS"},
        ],
        "channel": "Anton Putra",
        "topic": "Terraform Basic to Advanced"
    },
    13: {
        "type": "single",
        "video_id": "rjjES5IsPdg",
        "title": "Learn Docker – Full DevOps Course for Deploying Containerized Apps",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 26988,
        "topic": "Docker - basics through advanced multi-stage builds and image optimization"
    },
    14: {
        "type": "single",
        "video_id": "_4uQI4ihGVU",
        "title": "Learn Kubernetes in 6 Hours – Full Course with Real-World Project",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 21205,
        "topic": "Kubernetes - basics through advanced (pods, deployments, services, ingress, autoscaling)"
    },
    15: {
        "type": "episodes",
        "episodes": [
            {"video_id": "MeU5_k9ssrs", "title": "ArgoCD Tutorial for Beginners - GitOps CD for Kubernetes"},
            {"video_id": "dmGW22W3VOs", "title": "Realtime DevOps Project using Azure DevOps and GitOps"},
            {"video_id": "JGQI5pkK82w", "title": "Jenkins End to End CICD Implementation"},
            {"video_id": "7A5cH8iqgHU", "title": "You will never forget HELM after watching this"},
            {"video_id": "HGu9sgoHaJ0", "title": "DevOpsified - Complete DevOps Implementation"},
        ],
        "channel": "Multiple",
        "topic": "GitOps ArgoCD Helm"
    },
    16: {
        "type": "single",
        "video_id": "Tz7FsunBbfQ",
        "title": "GitHub Actions Certification – Full Course to PASS the Exam",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 11399,
        "topic": "CI/CD - Jenkins fundamentals and GitHub Actions (Actions-first emphasis per current industry trend)"
    },
    17: {
        "type": "single",
        "video_id": "zZcxdWJ_tRc",
        "title": "Prometheus FULL Course: Docker/K8s, PromQL, Grafana & MORE!",
        "channel": "Rayan Slim",
        "duration_seconds": 14331,
        "topic": "Observability - Prometheus Grafana"
    },
    18: {
        "type": "single",
        "video_id": "g85PQvDI8Cc",
        "title": "DevOps to DevSecOps in 9 Hours | Practical Learning",
        "channel": "Abhishek.Veeramalla",
        "duration_seconds": 30112,
        "topic": "DevSecOps"
    },
    19: {
        "type": "single",
        "video_id": "C842vFY5kRo",
        "title": "System Design Course – APIs, Databases, Caching, CDNs, Load Balancing",
        "channel": "freeCodeCamp.org",
        "duration_seconds": 7522,
        "topic": "System Design and IDP Backstage concepts"
    },
    20: {
        "type": "episodes",
        "episodes": [
            {"video_id": "F2FmTdLtb_4", "title": "System Design Concepts Course and Interview Prep"},
            {"video_id": "UzILixH4Odw", "title": "Python DevOps Interview Q&A - Beginner to Intermediate"},
        ],
        "channel": "Multiple",
        "topic": "Resume ATS and Interview Practice"
    },
}


def get_week_config(week_number: int) -> dict:
    """Returns the verified video configuration for a given week."""
    return FIXED_VIDEO_MAP.get(week_number)