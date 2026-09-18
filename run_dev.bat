@echo off
cd /d "c:\Disk D\Project\Lebedev"
".venv\Scripts\python.exe" -m uvicorn app.main:app --host 127.0.0.1 --port 8000
