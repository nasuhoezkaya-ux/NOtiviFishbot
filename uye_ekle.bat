@echo off
chcp 65001 >nul
title FishBot VIP - Uye yonetimi
cd /d "%~dp0"

set "VPY=.venv\Scripts\python.exe"
if exist "%VPY%" goto :run
set "VPY=py -3"
py -3 -c "import sys" >nul 2>nul && goto :run
set "VPY=python"
python -c "import sys" >nul 2>nul && goto :run
echo [HATA] Python bulunamadi. Once baslat.bat'i calistir.
pause
exit /b 1

:run
echo ==================================================
echo   FishBot VIP - VIP uye ekle
echo ==================================================
echo.
set /p "U=Kullanici adi: "
set /p "P=Sifre: "
set /p "D=Kac gun VIP: "
%VPY% tools\manage_users.py ekle "%U%" "%P%" %D%
echo.
echo Tum uyeler:
%VPY% tools\manage_users.py liste
echo.
pause
