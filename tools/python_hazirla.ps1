# FishBot VIP - Python hazirlama
# 1) Bot kutuphanelerinin destekledigi en yeni Python surumunu PyPI'den bulur.
# 2) Bilgisayarda uygun Python varsa onu kullanir.
# 3) Yoksa python.org'dan o surumun en guncel halini indirir, sessizce kurar ve PATH'e ekler.
# 4) Bot klasorunde bu Python ile sanal ortam (.venv) olusturur.

param([switch]$Recreate)
$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"   # indirmeyi cok hizlandirir
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

$Root = Split-Path -Parent $PSScriptRoot
$Venv = Join-Path $Root ".venv"

$MinMinor = 10
$FallbackMax = 13
$Is64 = [Environment]::Is64BitOperatingSystem

function Say($t) { Write-Host $t }

function Get-Json($url) {
    try { return Invoke-RestMethod -Uri $url -UseBasicParsing -TimeoutSec 20 } catch { return $null }
}

# ---------------------------------------------------------------- 1) uyumlu en yeni surum
function Get-MaxSupportedMinor {
    $max = 99
    $plat = if ($Is64) { "win_amd64" } else { "win32" }

    # PySide6: requires_python ust siniri, or. ">=3.9, <3.15"
    $j = Get-Json "https://pypi.org/pypi/PySide6/json"
    if ($j -and $j.info.requires_python -match "<\s*3\.(\d+)") { $max = [Math]::Min($max, [int]$Matches[1] - 1) }
    elseif (-not $j) { return $FallbackMax }

    # surume ozel tekerlek (wheel) yayinlayan paketler: numpy, pywin32
    foreach ($pkg in @("numpy", "pywin32")) {
        $j = Get-Json "https://pypi.org/pypi/$pkg/json"
        if (-not $j) { return $FallbackMax }
        $minors = @()
        foreach ($f in $j.urls) {
            if ($f.filename -like "*$plat*" -and $f.filename -match "-cp3(\d+)-cp3\d+t?-") { $minors += [int]$Matches[1] }
        }
        if ($minors.Count -gt 0) { $max = [Math]::Min($max, [int](($minors | Measure-Object -Maximum).Maximum)) }
    }
    if ($max -eq 99 -or $max -lt $MinMinor) { return $FallbackMax }
    return $max
}

# ---------------------------------------------------------------- 2) kurulu Python'lari bul
function Get-PyInfo($exe) {
    try {
        if ($exe -like "*\WindowsApps\*") { return $null }   # Microsoft Store kisayolu
        $o = & $exe -c "import sys,struct;print('%d %d %d' % (sys.version_info[0], sys.version_info[1], struct.calcsize('P')*8))" 2>$null
        if ($LASTEXITCODE -ne 0 -or -not $o) { return $null }
        $p = "$o".Trim().Split(" ")
        return [pscustomobject]@{ Exe = $exe; Major = [int]$p[0]; Minor = [int]$p[1]; Bits = [int]$p[2] }
    } catch { return $null }
}

function Find-Installed($maxMinor) {
    $cands = New-Object System.Collections.Generic.List[string]
    foreach ($base in @("$env:LOCALAPPDATA\Programs\Python", "$env:ProgramFiles", "${env:ProgramFiles(x86)}", "$env:SystemDrive\")) {
        if ($base -and (Test-Path $base)) {
            Get-ChildItem -Path $base -Directory -Filter "Python3*" -ErrorAction SilentlyContinue |
                ForEach-Object { $e = Join-Path $_.FullName "python.exe"; if (Test-Path $e) { $cands.Add($e) } }
        }
    }
    try {   # py baslaticisinin bildigi kurulumlar
        $lst = & py -0p 2>$null
        foreach ($l in $lst) { if ($l -match "([A-Za-z]:\\.*python\.exe)") { $cands.Add($Matches[1]) } }
    } catch {}
    try { foreach ($c in (Get-Command python.exe -All -ErrorAction SilentlyContinue)) { $cands.Add($c.Source) } } catch {}

    $wantBits = if ($Is64) { 64 } else { 32 }
    $best = $null
    foreach ($e in ($cands | Select-Object -Unique)) {
        $i = Get-PyInfo $e
        if (-not $i -or $i.Major -ne 3 -or $i.Minor -lt $MinMinor -or $i.Minor -gt $maxMinor -or $i.Bits -ne $wantBits) { continue }
        if (-not $best -or $i.Minor -gt $best.Minor) { $best = $i }
    }
    return $best
}

# ---------------------------------------------------------------- 3) indir + kur
function Find-Installer($minor) {
    $suffix = if ($Is64) { "-amd64" } else { "" }
    $vers = @()
    try {
        $html = (Invoke-WebRequest -Uri "https://www.python.org/ftp/python/" -UseBasicParsing -TimeoutSec 30).Content
        $vers = [regex]::Matches($html, "href=""(3\.$minor\.\d+)/""") | ForEach-Object { $_.Groups[1].Value } |
            Sort-Object { [version]$_ } -Descending
    } catch {}
    foreach ($v in $vers) {   # en yeni yamadan baslayarak kurulum dosyasi olani sec
        $url = "https://www.python.org/ftp/python/$v/python-$v$suffix.exe"
        try { Invoke-WebRequest -Uri $url -Method Head -UseBasicParsing -TimeoutSec 20 | Out-Null; return @{ Version = $v; Url = $url } } catch {}
    }
    return $null
}

function Install-Python($maxMinor) {
    for ($m = $maxMinor; $m -ge $MinMinor; $m--) {
        Say "[..] Python 3.$m icin en guncel kurulum dosyasi araniyor..."
        $inst = Find-Installer $m
        if (-not $inst) { continue }
        $file = Join-Path $env:TEMP "python-$($inst.Version)-fishbot.exe"
        Say "[..] Python $($inst.Version) indiriliyor (~30 MB)..."
        Invoke-WebRequest -Uri $inst.Url -OutFile $file -UseBasicParsing -TimeoutSec 600
        Say "[..] Python $($inst.Version) kuruluyor (sessiz kurulum, PATH'e ekleniyor)..."
        $instArgs = @("/quiet", "InstallAllUsers=0", "PrependPath=1", "Include_launcher=1",
                      "InstallLauncherAllUsers=0", "Include_test=0", "Include_doc=0", "Shortcuts=0", "Include_pip=1")
        $p = Start-Process -FilePath $file -ArgumentList $instArgs -Wait -PassThru
        Remove-Item $file -Force -ErrorAction SilentlyContinue
        $dir = if ($Is64) { "Python3$m" } else { "Python3$m-32" }
        $exe = Join-Path "$env:LOCALAPPDATA\Programs\Python\$dir" "python.exe"
        if (-not (Test-Path $exe)) { $i = Find-Installed $m; if ($i) { $exe = $i.Exe } }
        if (-not (Test-Path $exe)) { throw "Python kurulumu basarisiz (kod $($p.ExitCode))." }
        # PATH'i bu oturum icin de guncelle (yeni pencereler zaten kurulumdan alir)
        $env:Path = (Split-Path -Parent $exe) + ";" + (Join-Path (Split-Path -Parent $exe) "Scripts") + ";" + $env:Path
        return $exe
    }
    throw "python.org uzerinde uygun Python kurulum dosyasi bulunamadi."
}

# ---------------------------------------------------------------- ana akis
try {
    Say "[..] Kutuphanelerin destekledigi en yeni Python surumu kontrol ediliyor..."
    $maxMinor = Get-MaxSupportedMinor
    Say "[OK] Uyumlu en yeni surum: Python 3.$maxMinor"

    $found = Find-Installed $maxMinor
    if ($found -and $found.Minor -eq $maxMinor) {
        $exe = $found.Exe
        Say "[OK] Kurulu Python kullanilacak: $exe"
    } else {
        if ($found) { Say "[..] Kurulu Python 3.$($found.Minor) var; daha yeni Python 3.$maxMinor kurulacak." }
        try {
            $exe = Install-Python $maxMinor
            Say "[OK] Python kuruldu: $exe"
        } catch {
            if (-not $found) { throw }
            Say "[UYARI] Yeni Python kurulamadi ($($_.Exception.Message)). Kurulu 3.$($found.Minor) kullanilacak."
            $exe = $found.Exe
        }
    }
    $vpy = Join-Path $Venv "Scripts\python.exe"
    if ($Recreate -and (Test-Path $Venv)) {
        Say "[..] Eski sanal ortam siliniyor..."
        Remove-Item -Recurse -Force $Venv
    }
    if (-not (Test-Path $vpy)) {
        Say "[..] Bot icin sanal ortam olusturuluyor..."
        & $exe -m venv $Venv
        if ($LASTEXITCODE -ne 0 -or -not (Test-Path $vpy)) { throw "Sanal ortam olusturulamadi." }
    }
    Say "[OK] Sanal ortam hazir."
    exit 0
} catch {
    Write-Host ""
    Write-Host "[HATA] $($_.Exception.Message)"
    exit 1
}
