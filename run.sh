#!/usr/bin/env bash
set -e
python3 -m venv .venv
source .venv/bin/activate
pip install -q -r requirements.txt
uvicorn src.agent:app --host 0.0.0.0 --port 8000
