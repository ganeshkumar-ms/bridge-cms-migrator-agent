@echo off
echo Starting BRIDGE Backend on http://localhost:8004...
python -m uvicorn main:app --host 0.0.0.0 --port 8004 --reload

