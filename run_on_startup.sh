#!/bin/bash
cd /home/ubuntu/jarvis
source venv/bin/activate
python3 orchestrator.py >> /home/ubuntu/jarvis/orchestrator_run.log 2>&1
echo "=== Orchestrator run completed at $(date) ===" >> /home/ubuntu/jarvis/orchestrator_run.log
sleep 1800
sudo shutdown -h now
