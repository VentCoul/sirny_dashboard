#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
streamlit run dashboard.py --server.port 8501
