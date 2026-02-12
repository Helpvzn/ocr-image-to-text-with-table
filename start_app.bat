@echo off
REM Vizan Designer Studio v2.0 Launcher
REM Running with default optimizations enabled (MKL/OneDNN)
REM Compatible with PaddlePaddle 2.6.2

echo ========================================
echo Vizan Designer Studio v2.0
echo ========================================
echo Starting application with High Performance Mode...
echo.

streamlit run vizan_studio_v2/app.py

pause
