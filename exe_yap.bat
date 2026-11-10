@echo off
chcp 65001 >nul
title FishBot - Program (.exe) olusturma
cd /d "%~dp0"
echo ==================================================
echo   FishBot programi (.exe) olusturuluyor
echo   Ilk seferde 5-10 dakika surebilir.
echo ==================================================
echo.
set "SURUM="
set /p "SURUM=Surum numarasi (or. 2.0.5, bos birakirsan degismez): "
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\exe_yap.ps1" -Version "%SURUM%"
if errorlevel 1 (
  echo.
  echo [HATA] Program olusturulamadi. Bu pencerenin ekran goruntusunu gonder.
  pause
  exit /b 1
)
echo.
pause
