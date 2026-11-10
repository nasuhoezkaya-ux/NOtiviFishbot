# FishBot - tek dosya Windows programi (FishBot.exe) olusturma
#  1) Python ortamini hazirlar (yoksa python_hazirla.ps1 indirir/kurar)
#  2) Kutuphaneleri + PyInstaller'i kurar
#  3) cikti\FishBot.exe olusturur: kullanici SADECE bu dosyayi indirir. Exe acilinca once guncelleme /
#     kontrol ekrani gelir, sorun yoksa uye giris ekrani. Ayarlar ve ogrenilen resimler
#     %LOCALAPPDATA%\FishBot klasorunde tutulur.
#  4) (yerel) cikti\UyeYonetimi.exe - yerel uye dosyasi icin; Supabase kullaniliyorsa gerekmez.
# Not: pip / PyInstaller bilgi satirlarini stderr'e yazar; "Stop" olursa PowerShell 5 durur. Bu yuzden
# "Continue" ve her adimda cikis kodu kontrol edilir.
param([string]$Python = "", [switch]$NoOpen, [string]$Version = "")
$ErrorActionPreference = "Continue"
$ProgressPreference = "SilentlyContinue"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root
$Py = if ($Python) { $Python } else { Join-Path $Root ".venv\Scripts\python.exe" }

function Step($t) { Write-Host ""; Write-Host "[..] $t" -ForegroundColor Cyan }
function Ok($t) { Write-Host "[OK] $t" -ForegroundColor Green }

# ---- 1) Python
if (-not (Test-Path $Py)) {
    Step "Python hazirlaniyor"
    & powershell -NoProfile -ExecutionPolicy Bypass -File (Join-Path $PSScriptRoot "python_hazirla.ps1")
    if (-not (Test-Path $Py)) { throw "Python ortami olusturulamadi." }
}
Ok "Python: $(& $Py --version)"

# ---- 2) kutuphaneler
Step "Kutuphaneler ve PyInstaller kuruluyor"
& $Py -m pip install --upgrade pip --disable-pip-version-check -q
& $Py -m pip install -r requirements.txt --disable-pip-version-check -q
if ($LASTEXITCODE -ne 0) { throw "requirements.txt kurulamadi." }
& $Py -m pip install -r requirements-ocr.txt --disable-pip-version-check -q 2>$null
& $Py -m pip install "pyinstaller>=6.10" --disable-pip-version-check -q
if ($LASTEXITCODE -ne 0) { throw "PyInstaller kurulamadi." }
Ok "Kutuphaneler hazir"

# ---- surum (verildiyse core\version.py'ye yazilir)
if ($Version) {
    & $Py "$Root\tools\surum_yaz.py" $Version
    if ($LASTEXITCODE -ne 0) { throw "Surum yazilamadi." }
}

# ---- 3) derleme (tek dosya)
$Build = Join-Path $Root "build"
$Out = Join-Path $Root "cikti"
if (Test-Path $Build) { Remove-Item $Build -Recurse -Force -ErrorAction Stop }
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$Icon = Join-Path $Root "assets\app.ico"
$common = @("--noconfirm", "--clean", "--distpath", "$Build\dist", "--workpath", "$Build\work", "--specpath", "$Build",
            "--icon", $Icon, "--log-level", "WARN", "--exclude-module", "matplotlib")

$extra = @("--add-data", "$Root\assets;assets")
& $Py -c "import winrt.windows.media.ocr" 2>$null
if ($LASTEXITCODE -eq 0) { $extra += @("--collect-all", "winrt") }

Step "FishBot.exe olusturuluyor (birkac dakika)"
& $Py -m PyInstaller @common @extra --onefile --windowed --uac-admin --name FishBot --splash "$Root\assets\splash.png" --paths $Root "$Root\main.py"
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Acilis resmiyle olmadi, resimsiz deneniyor..."
    & $Py -m PyInstaller @common @extra --onefile --windowed --uac-admin --name FishBot --paths $Root "$Root\main.py"
    if ($LASTEXITCODE -ne 0) { throw "FishBot.exe olusturulamadi." }
}
Copy-Item "$Build\dist\FishBot.exe" "$Out\FishBot.exe" -Force -ErrorAction Stop
Ok "FishBot.exe hazir: $Out\FishBot.exe ($([math]::Round((Get-Item "$Out\FishBot.exe").Length / 1MB, 1)) MB)"

Step "UyeYonetimi.exe olusturuluyor (yerel uyelik icin)"
& $Py -m PyInstaller @common --onefile --console --name UyeYonetimi --paths $Root "$Root\tools\manage_users.py"
if ($LASTEXITCODE -eq 0) { Copy-Item "$Build\dist\UyeYonetimi.exe" "$Out\UyeYonetimi.exe" -Force; Ok "UyeYonetimi.exe hazir" }

Write-Host ""
Write-Host "Bitti. Kullanicilara sadece cikti\FishBot.exe dosyasini ver (ya da GitHub yayinina ekle)." -ForegroundColor Green
if (-not $NoOpen) { Start-Process explorer.exe $Out }
