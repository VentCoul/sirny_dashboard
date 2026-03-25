#!/bin/bash
set -e

LOG_FILE="/tmp/sirny_startup.log"
echo "$(date): Starting Sirny services..." >> $LOG_FILE

# Kill any lingering processes
pkill -f "streamlit run dashboard.py" || true
pkill -f "cloudflared tunnel" || true
sleep 2

cd /home/jdeere/dev/sirny_dashboard

# Start Streamlit with stability options
echo "$(date): Starting Streamlit..." >> $LOG_FILE
/home/jdeere/dev/sirny_dashboard/venv/bin/streamlit run dashboard.py \
  --server.port 8501 \
  --server.address 127.0.0.1 \
  --server.headless true \
  --logger.level=info \
  --client.showErrorDetails=false \
  >> $LOG_FILE 2>&1 &

STREAMLIT_PID=$!
echo "Streamlit PID: $STREAMLIT_PID" >> $LOG_FILE
sleep 8

# Verify Streamlit is responsive
for i in {1..10}; do
  if curl -s http://localhost:8501 > /dev/null 2>&1; then
    echo "$(date): Streamlit is responsive" >> $LOG_FILE
    break
  fi
  echo "$(date): Waiting for Streamlit... ($i/10)" >> $LOG_FILE
  sleep 2
done

# Start Cloudflare Tunnel
echo "$(date): Starting Cloudflare Tunnel..." >> $LOG_FILE
nohup /tmp/cloudflared tunnel --url http://localhost:8501 >> $LOG_FILE 2>&1 &
TUNNEL_PID=$!
echo "Tunnel PID: $TUNNEL_PID" >> $LOG_FILE

sleep 5
TUNNEL_URL=$(grep "trycloudflare.com" $LOG_FILE | tail -1 | grep -oE "https://[a-z0-9-]+\.trycloudflare\.com" || echo "PENDING")
echo "$(date): Tunnel URL: $TUNNEL_URL" >> $LOG_FILE

echo "$(date): All services started successfully!" >> $LOG_FILE
