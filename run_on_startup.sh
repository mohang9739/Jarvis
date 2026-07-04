#!/bin/bash

TOKEN=$(curl -s -X PUT "http://169.254.169.254/latest/api/token" -H "X-aws-ec2-metadata-token-ttl-seconds: 21600")
INSTANCE_ID=$(curl -s -H "X-aws-ec2-metadata-token: $TOKEN" http://169.254.169.254/latest/meta-data/instance-id)
TAG_VALUE=$(aws ec2 describe-tags --filters "Name=resource-id,Values=$INSTANCE_ID" "Name=key,Values=TriggerType" --region us-east-1 --query "Tags[0].Value" --output text)

if [ "$TAG_VALUE" != "automated" ]; then
    echo "$(date): Manual start detected (TriggerType=$TAG_VALUE) - skipping auto-orchestration/shutdown" >> /home/ubuntu/jarvis/orchestrator_run.log
    exit 0
fi

# Remove the tag so it doesn't persist into future boots
aws ec2 delete-tags --resources "$INSTANCE_ID" --tags Key=TriggerType --region us-east-1

cd /home/ubuntu/jarvis
source venv/bin/activate
python3 orchestrator.py >> /home/ubuntu/jarvis/orchestrator_run.log 2>&1
echo "=== Orchestrator run completed at $(date) ===" >> /home/ubuntu/jarvis/orchestrator_run.log
sleep 1800
sudo shutdown -h now