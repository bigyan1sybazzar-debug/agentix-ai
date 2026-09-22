@echo off
title Learnami Automation Engine
echo ============================================================
echo Starting Learnami AutoEngine Web Server...
echo Open your browser at: http://127.0.0.1:8000/
echo ============================================================
python manage.py runserver 127.0.0.1:8000
pause
