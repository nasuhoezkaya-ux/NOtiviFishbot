# FishBot - Windows programi (.exe) olusturma
#  1) Python ortamini hazirlar (yoksa python_hazirla.ps1 indirir/kurar)
#  2) Kutuphaneleri + PyInstaller'i kurar
#  3) FishBot.exe (pencereli) ve UyeYonetimi.exe (konsol) olusturur
#  4) Hepsini cikti\FishBot klasorune toplar (assets, data, README)
#  5) Inno Setup yukluyse cikti\FishBot_Kurulum.exe kurulum dosyasini da olusturur, yoksa zip yapar
# Not: harici programlar (pip, PyInstaller) bilgi satirlarini stderr'e yazar; "Stop" olursa PowerShell 5
# bunlari hata sanip durur. Bu yuzden "Continue" ve her adimda cikis kodu kontrol edilir.
param([string]$Python = "", [switch]$NoOpen)
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
& $Py -m pip install "pyinstaller>=6.6" --disable-pip-version-check -q
if ($LASTEXITCODE -ne 0) { throw "PyInstaller kurulamadi." }
Ok "Kutuphaneler hazir"

# ---- 3) derleme
$Build = Join-Path $Root "build"
$Out = Join-Path $Root "cikti"
if (Test-Path $Build) { Remove-Item $Build -Recurse -Force -ErrorAction Stop }
$Icon = Join-Path $Root "assets\app.ico"
$common = @("--noconfirm", "--clean", "--distpath", "$Build\dist", "--workpath", "$Build\work", "--specpath", "$Build",
            "--icon", $Icon, "--log-level", "WARN", "--exclude-module", "tkinter", "--exclude-module", "matplotlib")

$ocr = $false
& $Py -c "import winrt.windows.media.ocr" 2>$null
if ($LASTEXITCODE -eq 0) { $ocr = $true }
$extra = @()
if ($ocr) { $extra += @("--collect-all", "winrt") }

Step "FishBot.exe olusturuluyor (birkac dakika)"
& $Py -m PyInstaller @common @extra --windowed --name FishBot --paths $Root "$Root\main.py"
if ($LASTEXITCODE -ne 0) { throw "FishBot.exe olusturulamadi." }
Ok "FishBot.exe hazir"

Step "UyeYonetimi.exe olusturuluyor"
& $Py -m PyInstaller @common --onefile --console --name UyeYonetimi --paths $Root "$Root\tools\manage_users.py"
if ($LASTEXITCODE -ne 0) { throw "UyeYonetimi.exe olusturulamadi." }
Ok "UyeYonetimi.exe hazir"

# ---- 4) klasoru topla
Step "Program klasoru hazirlaniyor"
$App = Join-Path $Out "FishBot"
if (Test-Path $App) { Remove-Item $App -Recurse -Force -ErrorAction Stop }
New-Item -ItemType Directory -Force -Path $Out | Out-Null
Copy-Item "$Build\dist\FishBot" $App -Recurse -ErrorAction Stop
Copy-Item "$Build\dist\UyeYonetimi.exe" $App
Copy-Item "$Root\assets" "$App\assets" -Recurse
Copy-Item "$Root\README.md" $App
New-Item -ItemType Directory -Force -Path "$App\data" | Out-Null
Ok "Program klasoru: $App"

# ---- 5) kurulum dosyasi (Inno Setup varsa) ya da zip
$iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
          "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
$zip = Join-Path $Out "FishBot.zip"
if (Test-Path $zip) { Remove-Item $zip -Force }
Compress-Archive -Path $App -DestinationPath $zip
Ok "Zip (GitHub yayini / guncelleme icin): $zip"
# zip'e girmesin diye SONRA: mevcut uyeler ve ayarlar (varsa) bu bilgisayardaki programa tasinir
foreach ($f in @("users.json", "config.json", "remember.json")) {
    $src = Join-Path $Root "data\$f"
    if (Test-Path $src) { Copy-Item $src "$App\data\$f" }
}
if ($iscc) {
    Step "Kurulum dosyasi olusturuluyor (Inno Setup)"
    & $iscc "/DAppDir=$App" "/DOutDir=$Out" "/DIconFile=$Icon" "$PSScriptRoot\kurulum.iss" | Out-Null
    if ($LASTEXITCODE -eq 0) { Ok "Kurulum dosyasi: $Out\FishBot_Kurulum.exe" } else { Write-Host "[!] Kurulum dosyasi olusturulamadi." }
} else {
    Write-Host "     (Kurulum dosyasi icin Inno Setup 6'yi kurup bu islemi tekrarla.)"
}

Write-Host ""
Write-Host "Bitti. Programi calistirmak icin: $App\FishBot.exe" -ForegroundColor Green
if (-not $NoOpen) { Start-Process explorer.exe $Out }
