@echo off
title XAUUSD Bot Launcher
color 0A

echo =======================================================
echo     XAUUSD SCALPING BOT TIZIMI ISHGA TUSHIRILMOQDA
echo =======================================================
echo.

echo 1. Veb Dashboard serveri ishga tushmoqda...
start "Dashboard (app.py)" cmd /k "python app.py"

:: Server to'liq ishga tushishi uchun 3 soniya kutamiz
timeout /t 3 /nobreak >nul

echo 2. Asosiy Scalper Bot ishga tushmoqda...
start "Savdo Boti (xauusd_scalper.py)" cmd /k "python xauusd_scalper.py"

:: Kichik pauza
timeout /t 2 /nobreak >nul

echo 3. Brauzerda Dashboard sahifasi ochilmoqda...
start http://127.0.0.1:5000

echo.
echo Barcha tizimlar muvaffaqiyatli ishga tushdi!
echo.
echo Diqqat: Ochilgan 2 ta qora oynani YOPMANG!
echo Siz hozirgi mana shu oynani yopib yuborsangiz bo'ladi.
echo.
pause
