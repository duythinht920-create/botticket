@echo off
title Bot Ticket TDT - 24/7
cd /d "%~dp0"

:loop
echo [%date% %time%] Dang khoi dong bot...
python bot.py
echo [%date% %time%] Bot da tat. Khoi dong lai sau 5 giay...
timeout /t 5 /nobreak >nul
goto loop
