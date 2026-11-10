"""Programın klasörü: kaynak koddan çalışırken proje klasörü, .exe olarak çalışırken .exe'nin yanındaki klasör.

assets/ (öğrenilen resimler eklenir) ve data/ (ayarlar, üyeler, kayıtlar) her zaman BU klasörün içindedir;
böylece .exe sürümünde de bot öğrendiklerini ve ayarlarını kaybetmez."""
import os
import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys.executable).resolve().parent
else:
    APP_DIR = Path(__file__).resolve().parent.parent

ASSETS = APP_DIR / "assets"
DATA = APP_DIR / "data"
