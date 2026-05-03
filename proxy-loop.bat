@echo off
chcp 65001 >nul
title API Gateway Proxy (Auto-Restart)
cd /d "%~dp0"

set LOGFILE=proxy.log

echo [%date% %time%] === Proxy Loop Started === >> %LOGFILE%

:loop
echo [%date% %time%] Starting proxy.py ... >> %LOGFILE%
python proxy.py >> %LOGFILE% 2>&1
set EXITCODE=%ERRORLEVEL%
echo [%date% %time%] Proxy exited with code %EXITCODE% >> %LOGFILE%

if %EXITCODE% EQU 0 (
    echo [%date% %time%] Clean exit, stopping loop. >> %LOGFILE%
    goto :end
)

echo [%date% %time%] Crash detected, restarting in 3 seconds... >> %LOGFILE%
timeout /t 3 /nobreak >nul
goto :loop

:end
echo [%date% %time%] === Proxy Loop Ended === >> %LOGFILE%
