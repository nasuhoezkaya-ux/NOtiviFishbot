"""Otomatik güncelleme (GitHub Releases).

Akış: açılışta en son yayın (releases/latest) okunur. Etiketi (ör. v2.1.0) programın sürümünden yeniyse
yayına ekli FishBot*.zip indirilir (ilerleme anlık bildirilir), geçici klasöre açılır, küçük bir .bat
program kapanınca yeni dosyaları programın klasörüne kopyalar ve programı yeniden açar.
data\\ klasörüne (ayarlar, üyeler, kayıtlar) dokunulmaz; assets\\ içindeki öğrenilmiş resimler silinmez.
Güncelleme sadece .exe sürümünde kurulur; kaynak koddan çalışırken sadece "yeni sürüm var" denir.
"""
from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from .paths import APP_DIR
from .version import VERSION

UA = {"User-Agent": "FishBot-Updater", "Accept": "application/vnd.github+json"}


@dataclass
class Release:
    version: str
    url: str
    size: int
    notes: str = ""


def _ver(t: str) -> tuple:
    nums = re.findall(r"\d+", t or "")
    return tuple(int(n) for n in nums[:4]) or (0,)


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def check(repo: str, timeout: float = 8.0) -> Release | None:
    """Daha yeni bir sürüm varsa Release, yoksa None. Ağ hatasında istisna fırlatır."""
    if not repo or "/" not in repo:
        return None
    req = urllib.request.Request(f"https://api.github.com/repos/{repo.strip()}/releases/latest", headers=UA)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        d = json.loads(r.read().decode("utf-8"))
    tag = d.get("tag_name") or ""
    if _ver(tag) <= _ver(VERSION):
        return None
    for a in d.get("assets") or []:
        n = (a.get("name") or "").lower()
        if n.endswith(".zip") and "fishbot" in n:
            return Release(version=tag.lstrip("vV"), url=a["browser_download_url"], size=int(a.get("size") or 0),
                           notes=d.get("body") or "")
    return None


def download(rel: Release, progress: Callable[[int, int], None], cancel=lambda: False) -> Path:
    """Zip'i geçici klasöre indir. progress(indirilen_bayt, toplam_bayt)."""
    tmp = Path(tempfile.mkdtemp(prefix="fishbot_update_"))
    dest = tmp / "update.zip"
    req = urllib.request.Request(rel.url, headers={"User-Agent": UA["User-Agent"]})
    with urllib.request.urlopen(req, timeout=30) as r, open(dest, "wb") as f:
        total = int(r.headers.get("Content-Length") or rel.size or 0)
        done = 0
        while True:
            if cancel():
                raise RuntimeError("iptal")
            chunk = r.read(256 * 1024)
            if not chunk:
                break
            f.write(chunk)
            done += len(chunk)
            progress(done, total)
    return dest


def install(zip_path: Path) -> None:
    """Zip'i aç ve program kapanınca kopyalayıp yeniden açacak .bat'ı başlat. Sonra program kapanmalı."""
    work = zip_path.parent
    src = work / "yeni"
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(src)
    # zip'in içinde FishBot.exe'nin bulunduğu klasör
    root = next((p.parent for p in src.rglob("FishBot.exe")), None)
    if root is None:
        raise RuntimeError("Güncelleme paketinde FishBot.exe yok.")
    bat = work / "guncelle.bat"
    pid = os.getpid()
    bat.write_text(
        "@echo off\r\n"
        "chcp 65001 >nul\r\n"
        ":bekle\r\n"
        f'tasklist /FI "PID eq {pid}" 2>nul | find "{pid}" >nul && (timeout /t 1 /nobreak >nul & goto bekle)\r\n'
        f'robocopy "{root}" "{APP_DIR}" /E /R:3 /W:1 /XD "{root / "data"}" /NFL /NDL /NJH /NJS /NP >nul\r\n'
        f'start "" "{APP_DIR / "FishBot.exe"}"\r\n'
        f'rmdir /s /q "{src}" >nul 2>nul\r\n'
        f'del "{zip_path}" >nul 2>nul\r\n'
        '(goto) 2>nul & del "%~f0"\r\n', encoding="utf-8")
    flags = 0x08000000 | 0x00000200        # CREATE_NO_WINDOW | CREATE_NEW_PROCESS_GROUP
    subprocess.Popen(["cmd", "/c", str(bat)], creationflags=flags, close_fds=True, cwd=str(work))
