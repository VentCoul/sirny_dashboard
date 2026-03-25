#!/bin/bash

# Запуск Streamlit дашборду
cd /home/jdeere/dev/sirny_dashboard
nohup venv/bin/streamlit run dashboard.py --server.port 8501 > streamlit.log 2>&1 &
STREAMLIT_PID=$!
echo "Streamlit запущений (PID: $STREAMLIT_PID)"

# Дайте Streamlit час на запуск
sleep 5

# Запуск Cloudflare туннелю
nohup /tmp/cloudflared tunnel --url http://localhost:8501 > tunnel.log 2>&1 &
TUNNEL_PID=$!
echo "Cloudflare Tunnel запущений (PID: $TUNNEL_PID)"

echo "$(date): Сервіси запущені" >> /tmp/sirny_services.log
