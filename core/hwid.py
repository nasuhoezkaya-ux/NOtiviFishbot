"""Bilgisayar kimliği (üyeliği bir bilgisayara kilitlemek için). Kişisel veri içermez: Windows'un makine
kimliğinin özeti gönderilir."""
import hashlib
import platform
import uuid


def machine_id() -> str:
    raw = ""
    try:
        import winreg
        k = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Microsoft\Cryptography", 0,
                           winreg.KEY_READ | getattr(winreg, "KEY_WOW64_64KEY", 0))
        raw = winreg.QueryValueEx(k, "MachineGuid")[0]
    except Exception:
        raw = f"{uuid.getnode():x}-{platform.node()}"
    return hashlib.sha256(("fishbot:" + raw).encode()).hexdigest()[:32]
