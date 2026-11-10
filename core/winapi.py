"""Windows API yardımcıları: pencere listeleme, arka plan yakalama, PostMessage girişi.

Sadece Windows'ta çalışır; diğer sistemlerde import edilebilir ama
fonksiyonlar boş liste / hata döner (arayüz testleri için).
"""
from __future__ import annotations

import ctypes
from ctypes import wintypes
import os
import sys
import time
from dataclasses import dataclass

import numpy as np

IS_WINDOWS = sys.platform == "win32"

if IS_WINDOWS:
    import psutil
    import win32con
    import win32gui
    import win32process
    import win32ui

    user32 = ctypes.windll.user32
    # Not: DPI farkındalığını Qt kendisi ayarlar (Per-Monitor V2). Burada ayrıca ayarlamak
    # Qt'nin "SetProcessDpiAwarenessContext() failed" uyarısına yol açıyordu.


def ensure_dpi_aware() -> None:
    """Qt olmadan çalışan araçlar için (Qt zaten ayarlıyorsa dokunmaz)."""
    if not IS_WINDOWS:
        return
    try:
        if ctypes.windll.user32.IsProcessDPIAware():
            return
        ctypes.windll.shcore.SetProcessDpiAwareness(2)
    except Exception:
        try:
            ctypes.windll.user32.SetProcessDPIAware()
        except Exception:
            pass


# ------------------------------------------------------------------ DPI
# Eski oyunlar (Metin2 gibi) DPI'yi bilmez: Windows ekran ölçeklemesi (%125 vb.) açıkken
# oyunun koordinatları ile ekranın gerçek koordinatları farklıdır. Bu yüzden oyunla ilgili
# her ölçüm (yakalama boyutu, imleç konumu) oyunun KENDİ DPI bağlamında yapılır.
if IS_WINDOWS:
    try:
        user32.GetWindowDpiAwarenessContext.restype = ctypes.c_void_p
        user32.GetWindowDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.SetThreadDpiAwarenessContext.restype = ctypes.c_void_p
        user32.SetThreadDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        user32.GetAwarenessFromDpiAwarenessContext.argtypes = [ctypes.c_void_p]
        _HAS_DPI_CTX = True
    except AttributeError:
        _HAS_DPI_CTX = False


class window_dpi:
    """with window_dpi(hwnd): ... -> bu iş parçacığı geçici olarak oyunun DPI bağlamında çalışır."""

    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.old = None

    def __enter__(self):
        if IS_WINDOWS and _HAS_DPI_CTX:
            try:
                ctx = user32.GetWindowDpiAwarenessContext(self.hwnd)
                if ctx:
                    self.old = user32.SetThreadDpiAwarenessContext(ctx)
            except Exception:
                self.old = None
        return self

    def __exit__(self, *exc):
        if self.old:
            try:
                user32.SetThreadDpiAwarenessContext(self.old)
            except Exception:
                pass
        return False


def dpi_info(hwnd: int) -> dict:
    """Oyunun DPI farkındalığı ve monitör ölçeği (bilgi kartı için)."""
    out = {"aware": None, "scale": None}
    if not IS_WINDOWS:
        return out
    try:
        if _HAS_DPI_CTX:
            ctx = user32.GetWindowDpiAwarenessContext(hwnd)
            out["aware"] = int(user32.GetAwarenessFromDpiAwarenessContext(ctx))
        hdc = user32.GetDC(0)
        dpi = ctypes.windll.gdi32.GetDeviceCaps(hdc, 88)   # LOGPIXELSX (sistem DPI)
        user32.ReleaseDC(0, hdc)
        try:
            mon = user32.MonitorFromWindow(hwnd, 2)
            dx, dy = ctypes.c_uint(), ctypes.c_uint()
            if ctypes.windll.shcore.GetDpiForMonitor(mon, 0, ctypes.byref(dx), ctypes.byref(dy)) == 0:
                dpi = dx.value
        except Exception:
            pass
        out["scale"] = round(dpi / 96 * 100)
    except Exception:
        pass
    return out


# ------------------------------------------------------------------ pencereler
@dataclass
class GameWindow:
    pid: int
    hwnd: int
    title: str
    exe: str

    @property
    def label(self) -> str:
        return f"{self.pid}  •  {self.title}"


def _window_info(hwnd: int) -> GameWindow | None:
    title = win32gui.GetWindowText(hwnd)
    _, pid = win32process.GetWindowThreadProcessId(hwnd)
    try:
        exe = psutil.Process(pid).name()
    except Exception:
        exe = "?"
    return GameWindow(pid=pid, hwnd=hwnd, title=title or exe, exe=exe)


def list_game_windows(name_filter: str = "metin2", extra_exes=(), blocked_exes=(),
                      hidden_hwnds=()) -> list[GameWindow]:
    """Süreç adı / pencere başlığı filtreyle eşleşen ya da daha önce F7 ile seçilmiş
    exe adına sahip görünür pencereler."""
    if not IS_WINDOWS:
        return []
    flt = (name_filter or "").lower().strip()
    exes = {e.lower() for e in extra_exes or ()}
    blocked = {e.lower() for e in blocked_exes or ()} - exes   # F7 ile seçilen engeli aşar
    hidden = set(hidden_hwnds or ())
    own = os.getpid()
    found: list[GameWindow] = []

    def _cb(hwnd, _):
        if not win32gui.IsWindowVisible(hwnd) or not win32gui.GetWindowText(hwnd):
            return True
        if hwnd in hidden:
            return True
        w = _window_info(hwnd)
        if w.pid == own or w.exe.lower() in blocked:
            return True
        if (flt and (flt in w.exe.lower() or flt in w.title.lower())) or w.exe.lower() in exes:
            found.append(w)
        return True

    win32gui.EnumWindows(_cb, None)
    found.sort(key=lambda w: w.pid)
    return found


def window_under_cursor() -> GameWindow | None:
    """Farenin altındaki üst düzey pencere (F7 ile client seçmek için)."""
    if not IS_WINDOWS:
        return None
    x, y = win32gui.GetCursorPos()
    hwnd = win32gui.WindowFromPoint((x, y))
    if not hwnd:
        return None
    root = user32.GetAncestor(hwnd, 2)   # GA_ROOT
    hwnd = root or hwnd
    w = _window_info(hwnd)
    if w.pid == os.getpid():
        return None
    return w


def client_info(hwnd: int) -> dict | None:
    """Client alanının boyutu ve ekrandaki konumu."""
    if not IS_WINDOWS or not win32gui.IsWindow(hwnd):
        return None
    try:
        with window_dpi(hwnd):
            l, t, r, b = win32gui.GetClientRect(hwnd)
            x, y = win32gui.ClientToScreen(hwnd, (0, 0))
        d = dpi_info(hwnd)
        return {"w": r - l, "h": b - t, "x": x, "y": y, "min": bool(win32gui.IsIconic(hwnd)),
                "aware": d["aware"], "scale": d["scale"]}
    except Exception:
        return None


def key_down(name: str) -> bool:
    """Tuş şu an basılı mı (oyun ön plandayken de çalışır)."""
    if not IS_WINDOWS:
        return False
    vk = VK.get(name.upper())
    return bool(vk and user32.GetAsyncKeyState(vk) & 0x8000)


def window_alive(hwnd: int) -> bool:
    return IS_WINDOWS and bool(win32gui.IsWindow(hwnd))


# ------------------------------------------------------------------ yakalama
class WindowCapture:
    """Pencere başka pencerelerin arkasında olsa da istemci alanını yakalar.
    (Simge durumuna küçültülmüş pencere yakalanamaz.)"""

    PW_CLIENTONLY = 0x1
    PW_RENDERFULLCONTENT = 0x2

    def __init__(self, hwnd: int):
        self.hwnd = hwnd
        self.region: tuple[int, int, int, int] | None = None   # hızlı yakalama bölgesi (istemci koord.)
        self.fast_ok: bool | None = None       # None: henüz denenmedi
        self._last_check = 0.0
        self.last_fast = False

    def set_region(self, x: int, y: int, w: int, h: int) -> None:
        """Balık penceresi bulununca sadece o bölge EKRANDAN hızlıca kopyalanır (PrintWindow
        tüm pencereyi yeniden çizdirdiği için yavaştır, ~5-10 kat). Doğruluk ara sıra
        PrintWindow ile karşılaştırılarak kontrol edilir; tutmazsa yavaş yönteme dönülür."""
        r = (int(x), int(y), int(w), int(h))
        if self.region is None or max(abs(a - b) for a, b in zip(r, self.region)) > 6:
            self.region = r

    def grab(self) -> np.ndarray | None:
        if not IS_WINDOWS or not win32gui.IsWindow(self.hwnd) or win32gui.IsIconic(self.hwnd):
            return None
        with window_dpi(self.hwnd):
            now = time.time()
            if self.region is not None and self.fast_ok is not False:
                if self.fast_ok is None or now - self._last_check > 15.0:   # seyrek: canlı görüntü takılmasın
                    full = self._grab()
                    self._last_check = now
                    fast = self._grab_screen(full.shape if full is not None else None)
                    if full is not None and fast is not None:
                        x, y, w, h = self.region
                        a = full[y:y + h, x:x + w].astype(np.int16)
                        b = fast[y:y + h, x:x + w].astype(np.int16)
                        diff = float(np.abs(a - b).mean()) if a.size and a.shape == b.shape else 999.0
                        if self.fast_ok is None:
                            if self._region_visible():          # üstü kapalıyken karar verme
                                self.fast_ok = diff < 18.0
                        elif diff > 40.0:       # üstüne başka pencere geldi vb. -> bu kare tam yakala
                            self.last_fast = False
                            return full
                    self.last_fast = False
                    return full
                # birden fazla client: bu pencerenin o bölgesinin önünde BAŞKA bir pencere (öne alınmış diğer
                # client, panel vb.) varsa ekrandan kopyalamak yanlış pencereyi okur -> o kare PrintWindow ile
                if self._region_visible():
                    img = self._grab_screen(None)
                    if img is not None:
                        self.last_fast = True
                        return img
            self.last_fast = False
            return self._grab()

    def _region_visible(self) -> bool:
        """Hızlı yakalama bölgesi ekranda gerçekten BU pencereye mi ait (üstü kapalı değil mi)?"""
        try:
            ox, oy = win32gui.ClientToScreen(self.hwnd, (0, 0))
            l, t, r, b = win32gui.GetClientRect(self.hwnd)
            x, y, w, h = self.region
            x0, y0 = max(0, x) + 2, max(0, y) + 2
            x1, y1 = min(r - l, x + w) - 3, min(b - t, y + h) - 3
            if x1 <= x0 or y1 <= y0:
                return False
            me = user32.GetAncestor(self.hwnd, 2) or self.hwnd
            for px, py in ((x0, y0), (x1, y0), (x0, y1), (x1, y1), ((x0 + x1) // 2, (y0 + y1) // 2),
                           ((x0 + x1) // 2, y0), ((x0 + x1) // 2, y1)):
                hw = win32gui.WindowFromPoint((ox + px, oy + py))
                if not hw or (user32.GetAncestor(hw, 2) or hw) != me:
                    return False
            return True
        except Exception:
            return False

    def _grab_screen(self, shape) -> np.ndarray | None:
        try:
            l, t, r, b = win32gui.GetClientRect(self.hwnd)
            cw, ch = r - l, b - t
            ox, oy = win32gui.ClientToScreen(self.hwnd, (0, 0))
            x, y, w, h = self.region
            x, y = max(0, x), max(0, y)
            w, h = min(w, cw - x), min(h, ch - y)
            if w <= 0 or h <= 0:
                return None
            sdc = win32gui.GetDC(0)
            mdc = win32ui.CreateDCFromHandle(sdc)
            cdc = mdc.CreateCompatibleDC()
            bmp = win32ui.CreateBitmap()
            try:
                bmp.CreateCompatibleBitmap(mdc, w, h)
                cdc.SelectObject(bmp)
                cdc.BitBlt((0, 0), (w, h), mdc, (ox + x, oy + y), win32con.SRCCOPY)
                part = np.frombuffer(bmp.GetBitmapBits(True), dtype=np.uint8).reshape(h, w, 4)[:, :, :3]
            finally:
                win32gui.DeleteObject(bmp.GetHandle())
                cdc.DeleteDC()
                mdc.DeleteDC()
                win32gui.ReleaseDC(0, sdc)
            out = np.zeros((ch, cw, 3), np.uint8)
            out[y:y + h, x:x + w] = part
            return out
        except Exception:
            return None

    def _grab(self) -> np.ndarray | None:
        left, top, right, bottom = win32gui.GetClientRect(self.hwnd)
        w, h = right - left, bottom - top
        if w <= 0 or h <= 0:
            return None
        hwnd_dc = win32gui.GetWindowDC(self.hwnd)
        mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
        save_dc = mfc_dc.CreateCompatibleDC()
        bmp = win32ui.CreateBitmap()
        try:
            bmp.CreateCompatibleBitmap(mfc_dc, w, h)
            save_dc.SelectObject(bmp)
            ok = user32.PrintWindow(self.hwnd, save_dc.GetSafeHdc(),
                                    self.PW_CLIENTONLY | self.PW_RENDERFULLCONTENT)
            if not ok:
                save_dc.BitBlt((0, 0), (w, h), mfc_dc, (0, 0), win32con.SRCCOPY)
            bits = bmp.GetBitmapBits(True)
            img = np.frombuffer(bits, dtype=np.uint8).reshape(h, w, 4)
            return img[:, :, :3].copy()  # BGRA -> BGR
        finally:
            win32gui.DeleteObject(bmp.GetHandle())
            save_dc.DeleteDC()
            mfc_dc.DeleteDC()
            win32gui.ReleaseDC(self.hwnd, hwnd_dc)


# ------------------------------------------------------------------ giriş
VK = {"SPACE": 0x20, "ENTER": 0x0D, "TAB": 0x09, "ESC": 0x1B, "SHIFT": 0x10, "CTRL": 0x11, "ALT": 0x12}
VK.update({f"F{i}": 0x6F + i for i in range(1, 13)})
VK.update({str(d): 0x30 + d for d in range(10)})
VK.update({chr(c): c for c in range(ord("A"), ord("Z") + 1)})
KEY_NAMES = list(VK.keys())

WM_MOUSEMOVE, WM_LBUTTONDOWN, WM_LBUTTONUP = 0x0200, 0x0201, 0x0202
WM_KEYDOWN, WM_KEYUP, WM_CHAR = 0x0100, 0x0101, 0x0102
WM_ACTIVATE, WA_ACTIVE = 0x0006, 1
MK_LBUTTON = 0x0001
INPUT_METHODS = {
    "karma": "Karma: pencere bir an öne alınır, gerçek klavye (önerilen)",
    "postmessage": "Arka plan: pencereye tuş mesajı, öne almaz (oyun desteklerse)",
    "sendinput": "Ön plan: gerçek klavye (tek client)",
}


def _lparam(x: int, y: int) -> int:
    return (int(y) & 0xFFFF) << 16 | (int(x) & 0xFFFF)


def _vk(name: str) -> int:
    vk = VK.get(name.upper())
    if vk is None:
        raise ValueError(f"Bilinmeyen tuş: {name}")
    return vk


# ---- SendInput (gerçek donanım girişi gibi; DirectInput kullanan oyunlar da görür)
if IS_WINDOWS:
    from ctypes import wintypes

    ULONG_PTR = ctypes.c_size_t

    class _KEYBDINPUT(ctypes.Structure):
        _fields_ = [("wVk", wintypes.WORD), ("wScan", wintypes.WORD), ("dwFlags", wintypes.DWORD),
                    ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class _MOUSEINPUT(ctypes.Structure):
        _fields_ = [("dx", wintypes.LONG), ("dy", wintypes.LONG), ("mouseData", wintypes.DWORD),
                    ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD), ("dwExtraInfo", ULONG_PTR)]

    class _HARDWAREINPUT(ctypes.Structure):
        _fields_ = [("uMsg", wintypes.DWORD), ("wParamL", wintypes.WORD), ("wParamH", wintypes.WORD)]

    class _INPUTUNION(ctypes.Union):
        _fields_ = [("ki", _KEYBDINPUT), ("mi", _MOUSEINPUT), ("hi", _HARDWAREINPUT)]

    class _INPUT(ctypes.Structure):
        _fields_ = [("type", wintypes.DWORD), ("u", _INPUTUNION)]

    def _send_key_scan(vk: int, up: bool) -> None:
        scan = user32.MapVirtualKeyW(vk, 0)
        flags = 0x0008 | (0x0002 if up else 0)          # KEYEVENTF_SCANCODE | KEYUP
        inp = _INPUT(type=1, u=_INPUTUNION(ki=_KEYBDINPUT(wVk=0, wScan=scan, dwFlags=flags, time=0,
                                                           dwExtraInfo=0)))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))

    def _send_mouse(flags: int) -> None:
        inp = _INPUT(type=0, u=_INPUTUNION(mi=_MOUSEINPUT(dx=0, dy=0, mouseData=0, dwFlags=flags,
                                                         time=0, dwExtraInfo=0)))
        user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(_INPUT))


def get_cursor() -> tuple[int, int]:
    try:
        pt = wintypes.POINT()
        user32.GetCursorPos(ctypes.byref(pt))
        return int(pt.x), int(pt.y)
    except Exception:
        return 0, 0


def mouse_down(button: str = "left") -> bool:
    """Fare tuşu şu an basılı mı? (kullanıcının captcha'yı elle çözerken tıkladığı yeri öğrenmek için)"""
    try:
        vk = 0x01 if button == "left" else 0x02
        return bool(user32.GetAsyncKeyState(vk) & 0x8000)
    except Exception:
        return False


def set_cursor(x: float, y: float) -> None:
    try:
        user32.SetCursorPos(int(round(x)), int(round(y)))
    except Exception:
        pass


def client_rect_screen(hwnd: int) -> tuple[int, int, int, int]:
    """(sol, üst, genişlik, yükseklik) — pencere iç alanının ekrandaki gerçek yeri."""
    l, t, r, b = win32gui.GetClientRect(hwnd)
    ox, oy = win32gui.ClientToScreen(hwnd, (0, 0))
    return ox, oy, r - l, b - t


def mouse_click(button: str = "left", hold: float = 0.06) -> bool:
    """İmlecin bulunduğu yere GERÇEK fare tıklaması (SendInput)."""
    try:
        down, up = (0x0002, 0x0004) if button == "left" else (0x0008, 0x0010)
        _send_mouse(down)
        time.sleep(hold)
        _send_mouse(up)
        return True
    except Exception:
        return False


def beep(kind: str = "uyari") -> None:
    """Sesli uyarı (Windows)."""
    try:
        import winsound
        if kind == "uyari":
            for f in (880, 660, 880):
                winsound.Beep(f, 180)
        else:
            winsound.MessageBeep()
    except Exception:
        pass


def is_foreground(hwnd: int) -> bool:
    try:
        return user32.GetForegroundWindow() == hwnd
    except Exception:
        return True


def focus_window(hwnd: int, timeout: float = 0.6) -> bool:
    """Pencereyi öne alır. Windows arka plandaki programların odak çalmasını kısıtladığı için
    önce iş parçacığı girişi bağlanır, olmazsa ALT hilesi denenir."""
    if user32.GetForegroundWindow() == hwnd:
        return True
    if user32.IsIconic(hwnd):
        user32.ShowWindow(hwnd, 9)     # SW_RESTORE
    fg = user32.GetForegroundWindow()
    cur_tid = ctypes.windll.kernel32.GetCurrentThreadId()
    fg_tid = user32.GetWindowThreadProcessId(fg, None) if fg else 0
    attached = bool(fg_tid and fg_tid != cur_tid and user32.AttachThreadInput(cur_tid, fg_tid, True))
    try:
        user32.BringWindowToTop(hwnd)
        user32.SetForegroundWindow(hwnd)
    finally:
        if attached:
            user32.AttachThreadInput(cur_tid, fg_tid, False)
    end = time.time() + timeout
    while time.time() < end:
        if user32.GetForegroundWindow() == hwnd:
            time.sleep(0.05)           # oyunun odağı işlemesi için kısa bekleme
            return True
        time.sleep(0.02)
    # son çare: ALT bas-bırak, Windows odak kilidini açar
    user32.keybd_event(0x12, 0, 0, 0)
    user32.SetForegroundWindow(hwnd)
    user32.keybd_event(0x12, 0, 0x0002, 0)
    time.sleep(0.1)
    return user32.GetForegroundWindow() == hwnd


def _child_windows(hwnd: int) -> list[int]:
    out: list[int] = []
    try:
        win32gui.EnumChildWindows(hwnd, lambda h, _: out.append(h) or True, None)
    except Exception:
        pass
    return out


class PostMessageInput:
    """Arka planda: pencere öne gelmez (oyun arka plan tuşunu kabul ederse)."""

    def __init__(self, hwnd: int):
        self.hwnd = hwnd

    def key(self, name: str, hold: float = 0.06) -> None:
        vk = _vk(name)
        scan = user32.MapVirtualKeyW(vk, 0)
        targets = [self.hwnd] + _child_windows(self.hwnd)
        for h in targets:   # bazı oyunlar pencereyi aktif sanmadıkça tuş işlemez
            user32.PostMessageW(h, WM_ACTIVATE, WA_ACTIVE, 0)
            user32.PostMessageW(h, WM_KEYDOWN, vk, 1 | (scan << 16))
            if vk == 0x20 or 0x30 <= vk <= 0x5A:
                user32.PostMessageW(h, WM_CHAR, vk if vk != 0x20 else 0x20, 1 | (scan << 16))
        time.sleep(hold)
        for h in targets:
            user32.PostMessageW(h, WM_KEYUP, vk, 1 | (scan << 16) | 0xC0000000)


class SendInputInput:
    """Ön planda: gerçek klavye. Pencere öne alınır; aynı anda tek client için uygundur."""

    def __init__(self, hwnd: int):
        self.hwnd = hwnd

    def key(self, name: str, hold: float = 0.06) -> None:
        vk = _vk(name)
        focus_window(self.hwnd)
        _send_key_scan(vk, False)
        time.sleep(hold)
        _send_key_scan(vk, True)

    def key_now(self, name: str, hold: float = 0.04) -> None:
        """Zamanlama için: pencere zaten öndeyse odak işlemi yapmadan HEMEN bas."""
        vk = _vk(name)
        if user32.GetForegroundWindow() != self.hwnd:
            focus_window(self.hwnd)
        _send_key_scan(vk, False)
        time.sleep(hold)
        _send_key_scan(vk, True)

    def focus(self) -> None:
        focus_window(self.hwnd)


class HybridInput(PostMessageInput):
    """Karma: tuşlar için client bir an öne alınıp gerçek klavye girişi (tarama kodu) gönderilir
    (oyun arka plandaki pencereye gönderilen tuşu kabul etmiyor). Odak tek olduğu için tuşa basılan anlar
    client'lar arasında sırayla yapılır (CONTROL_LOCK)."""

    real_cursor = True

    def key(self, name: str, hold: float = 0.06) -> None:
        vk = _vk(name)
        with _FOCUS_LOCK:          # aynı anda iki client odak kapmasın
            focus_window(self.hwnd)
            _send_key_scan(vk, False)
            time.sleep(hold)
            _send_key_scan(vk, True)
            time.sleep(0.05)

    def key_now(self, name: str, hold: float = 0.04) -> None:
        """Zamanlama için: pencere zaten öndeyse odak işlemi yapmadan HEMEN bas (gecikme ~1 ms)."""
        vk = _vk(name)
        if user32.GetForegroundWindow() != self.hwnd:
            with _FOCUS_LOCK:
                focus_window(self.hwnd)
        _send_key_scan(vk, False)
        time.sleep(hold)
        _send_key_scan(vk, True)

    def focus(self) -> None:
        with _FOCUS_LOCK:
            focus_window(self.hwnd)


import threading as _threading  # noqa: E402

_FOCUS_LOCK = _threading.Lock()     # aynı anda iki client odak kapmasın


class _FairLock:
    """Sıra kilidi (ilk gelen ilk alır). Normal kilitte turu biten bot kilidi hemen geri alıp
    diğer client'ı hiç oynatmayabiliyordu; bu kilitte client'lar gerçekten SIRAYLA oynar."""

    def __init__(self):
        self._cv = _threading.Condition()
        self._owner = None
        self._queue: list = []
        self._urgent: set = set()
        self._critical: set = set()

    def acquire(self, timeout: float | None = None, urgent: bool = False, critical: bool = False) -> bool:
        """urgent=True: bu client'ta captcha var / işaret çıktı -> sıranın başına geçer (diğer acillerin arkasına).
        critical=True: zamanlama penceresinde basış anı geldi -> herkesin önüne geçer (milisaniyeler önemli)."""
        me = _threading.get_ident()
        with self._cv:
            if critical and me not in self._critical:
                if me in self._queue:
                    self._queue.remove(me)
                i = 0
                while i < len(self._queue) and self._queue[i] in self._critical:
                    i += 1
                self._queue.insert(i, me)
                self._critical.add(me)
                self._urgent.add(me)
                self._cv.notify_all()
            elif urgent and me not in self._urgent:
                if me in self._queue:
                    self._queue.remove(me)
                i = 0
                while i < len(self._queue) and self._queue[i] in self._urgent:
                    i += 1
                self._queue.insert(i, me)
                self._urgent.add(me)
                self._cv.notify_all()
            elif me not in self._queue:
                self._queue.append(me)
            ok = self._cv.wait_for(lambda: self._owner is None and self._queue and self._queue[0] == me,
                                   timeout)
            if not ok:
                return False          # sıradaki yerini korur, tekrar çağırınca devam eder
            self._queue.pop(0)
            self._urgent.discard(me)
            self._critical.discard(me)
            self._owner = me
            return True

    def release(self) -> None:
        with self._cv:
            self._owner = None
            self._cv.notify_all()

    def leave(self) -> None:
        """Bekleyen bot durdurulursa sıradan çıkar."""
        me = _threading.get_ident()
        with self._cv:
            self._urgent.discard(me)
            self._critical.discard(me)
            if me in self._queue:
                self._queue.remove(me)
                self._cv.notify_all()


CONTROL_LOCK = _FairLock()
PostMessageInput.real_cursor = False
SendInputInput.real_cursor = True


def make_input(method: str, hwnd: int):
    if method == "sendinput":
        return SendInputInput(hwnd)
    if method == "postmessage":
        return PostMessageInput(hwnd)
    return HybridInput(hwnd)


def tile_windows(hwnds: list[int]) -> int:
    """Oyun pencerelerini (en fazla 4) bulundukları monitörde 2x2 ızgaraya diz; boyutlarına dokunmaz.
    Pencereler üst üste binmezse her bot kendi çubuğunu ekrandan hızlıca okuyabilir. Dizilen pencere sayısı."""
    if not IS_WINDOWS or not hwnds:
        return 0
    try:
        import win32api
        mon = win32api.MonitorFromWindow(hwnds[0], 2)
        wl, wt, wr, wb = win32api.GetMonitorInfo(mon)["Work"]
    except Exception:
        return 0
    n = min(4, len(hwnds))
    cols = 1 if n == 1 else 2
    rows = 1 if n <= 2 else 2
    cw, ch = (wr - wl) // cols, (wb - wt) // rows
    done = 0
    for i, hw in enumerate(hwnds[:n]):
        try:
            l, t, r, b = win32gui.GetWindowRect(hw)
            w, h = r - l, b - t
            cx, cy = wl + (i % cols) * cw, wt + (i // cols) * ch
            # pencere hücreden büyükse ekran dışına taşmasın
            x = min(cx, wr - w) if w <= wr - wl else wl
            y = min(cy, wb - h) if h <= wb - wt else wt
            win32gui.SetWindowPos(hw, 0, max(wl, x), max(wt, y), 0, 0, 0x0001 | 0x0004 | 0x0010)  # NOSIZE|NOZORDER|NOACTIVATE
            done += 1
        except Exception:
            pass
    return done
