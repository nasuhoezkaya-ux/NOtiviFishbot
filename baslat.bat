@echo off
chcp 65001 >nul
title FishBot VIP
cd /d "%~dp0"

echo ==================================================
echo   FishBot VIP baslatiliyor...
echo ==================================================
echo.

set "VPY=.venv\Scripts\python.exe"
set "RECREATE="
set "TRIED="

rem ---- 1) Bot ortami var mi ve Python surumu uygun mu?
if not exist "%VPY%" goto :prepare
"%VPY%" -c "import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)" >nul 2>nul
if errorlevel 1 set "RECREATE=-Recreate"
if defined RECREATE goto :prepare
goto :packages

rem ---- 2) Python bul / indir / kur + sanal ortam
:prepare
echo [..] Python hazirlaniyor. Gerekirse en guncel uyumlu surum python.org'dan
echo      indirilip otomatik kurulur ve PATH'e eklenir. Lutfen bekle...
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\python_hazirla.ps1" %RECREATE%
if errorlevel 1 goto :py_fail
if not exist "%VPY%" goto :py_fail
echo.

rem ---- 3) Kutuphaneler
:packages
"%VPY%" -c "import PySide6, cv2, numpy, win32gui, psutil" >nul 2>nul
if not errorlevel 1 goto :packages_ok
echo [..] Gerekli kutuphaneler kuruluyor, ilk seferde birkac dakika surebilir...
"%VPY%" -m pip install --upgrade pip --disable-pip-version-check
"%VPY%" -m pip install -r requirements.txt --disable-pip-version-check
if errorlevel 1 goto :pip_retry
"%VPY%" -c "import PySide6, cv2, numpy, win32gui, psutil"
if errorlevel 1 goto :pip_retry
:packages_ok
echo [OK] Kutuphaneler hazir.

rem ---- 3b) Captcha icin yazi tanima (istege bagli)
"%VPY%" -c "import winrt.windows.media.ocr" >nul 2>nul
if not errorlevel 1 goto :ocr_ok
echo [..] Captcha icin Windows yazi tanima paketi kuruluyor...
"%VPY%" -m pip install -r requirements-ocr.txt --disable-pip-version-check >nul 2>nul
"%VPY%" -c "import winrt.windows.media.ocr" >nul 2>nul
if errorlevel 1 goto :ocr_fail
:ocr_ok
echo [OK] Yazi tanima hazir.
goto :ocr_done
:ocr_fail
echo [!] Yazi tanima kurulamadi. Bot calisir, captcha sadece resimle aranir.
:ocr_done

rem ---- 4) Uye kontrolu
if exist "data\users.json" goto :start
echo.
echo [UYARI] Henuz hic VIP uye yok. Giris yapabilmek icin bir uye gerekli.
choice /c EH /m "Simdi uye eklemek ister misin? E=Evet H=Hayir"
if errorlevel 2 goto :start
call "%~dp0uye_ekle.bat"

:start
echo.
echo [..] Bot aciliyor...
"%VPY%" main.py
if errorlevel 1 goto :crashed
exit /b 0

rem ================================================== hatalar
:pip_retry
if defined TRIED goto :pip_fail
set "TRIED=1"
set "RECREATE=-Recreate"
echo.
echo [UYARI] Kutuphaneler kurulamadi. Bot ortami sifirdan kurulup tekrar denenecek...
echo.
goto :prepare

:py_fail
echo.
echo [HATA] Python otomatik hazirlanamadi.
echo        - Internet baglantini kontrol et.
echo        - Antivirus indirmeyi engellemis olabilir.
echo        - Elle kurmak icin: https://www.python.org/downloads/
echo          Kurulumda "Add python.exe to PATH" kutusunu isaretle, sonra bu dosyayi tekrar calistir.
goto :end

:pip_fail
echo.
echo [HATA] Kutuphaneler kurulamadi. Internet baglantini kontrol et.
echo        Hata devam ederse bu pencerenin ekran goruntusunu gonder.
goto :end

:crashed
echo.
echo [HATA] Bot bir hata ile kapandi. Ayrinti: data\hata.log
echo        Bu pencerenin ve hata.log dosyasinin ekran goruntusunu gonder.
goto :end

:end
echo.
pause
exit /b 1
