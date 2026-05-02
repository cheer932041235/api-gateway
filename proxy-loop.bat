@echo off
title Claude Gateway Proxy (Auto-Restart)
:loop
echo [%date% %time%] Starting proxy...
python "%~dp0proxy.py"
echo [%date% %time%] Proxy exited (code %errorlevel%). Restarting in 3s...
timeout /t 3 /nobreak >nul
goto loop
