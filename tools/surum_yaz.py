"""core/version.py içindeki sürümü değiştirir (diğer satırlara dokunmaz).  python tools/surum_yaz.py 2.0.5"""
import re
import sys
from pathlib import Path

v = sys.argv[1].strip().lstrip("vV")
if not re.fullmatch(r"\d+(\.\d+){0,3}", v):
    sys.exit(f"Geçersiz sürüm: {v!r} (ör. 2.0.5)")
p = Path(__file__).resolve().parent.parent / "core" / "version.py"
s = p.read_text(encoding="utf-8")
s, n = re.subn(r'^VERSION = ".*?"', f'VERSION = "{v}"', s, count=1, flags=re.M)
if n != 1:
    sys.exit("core/version.py içinde VERSION satırı bulunamadı")
p.write_text(s, encoding="utf-8")
print(f"Sürüm: {v}")
