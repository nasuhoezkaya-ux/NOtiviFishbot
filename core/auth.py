"""Üye giriş katmanı.

İki sağlayıcı aynı arayüzü kullanır:
  • SupabaseAuthProvider — üyeler Supabase'de (core/server.py doluysa kullanılır)
  • LocalAuthProvider    — üyeler data/users.json dosyasında (sunucu ayarlı değilse)

Yönetici (is_admin) olan üye programdaki "Üyeler" sayfasından bütün üyeleri yönetebilir.
expires_at = None → süresiz üyelik.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
import urllib.error
import urllib.request
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from .config import DATA_DIR

USERS_PATH = os.path.join(DATA_DIR, "users.json")
PBKDF2_ROUNDS = 200_000


# ====================================================================== modeller
@dataclass
class Member:
    username: str
    expires_at: datetime | None = None        # None = süresiz
    active: bool = True
    is_admin: bool = False
    max_clients: int = 0                       # 0 = sınırsız
    hwid_lock: bool = False
    hwid: str = ""
    note: str = ""
    created_at: datetime | None = None
    last_login: datetime | None = None
    id: str = ""
    sessions: int = 0                          # son 15 dakikada açık oturum (bot çalışıyor)
    last_seen: datetime | None = None          # botun sunucuya son bağlandığı an

    @property
    def unlimited(self) -> bool:
        return self.expires_at is None

    @property
    def expired(self) -> bool:
        return self.expires_at is not None and self.expires_at <= datetime.now()


@dataclass
class Session:
    username: str
    expires_at: datetime | None               # None = süresiz
    is_admin: bool = False
    max_clients: int = 0
    token: str = ""
    extra: dict = field(default_factory=dict)

    @property
    def unlimited(self) -> bool:
        return self.expires_at is None

    @property
    def days_left(self) -> int:
        if self.expires_at is None:
            return 10 ** 6
        delta = self.expires_at - datetime.now()
        return max(0, delta.days + (1 if delta.seconds > 0 else 0))

    @property
    def is_valid(self) -> bool:
        return self.expires_at is None or datetime.now() < self.expires_at


class AuthError(Exception):
    """Kullanıcıya gösterilecek giriş hatası."""


class AuthProvider:
    name = "?"

    def login(self, username: str, password: str) -> Session:
        raise NotImplementedError

    def verify(self, session: Session) -> bool:
        """Bot çalışırken periyodik üyelik kontrolü (süre uzatılırsa session güncellenir)."""
        return session.is_valid

    # --- yönetim (sadece yönetici)
    def list_members(self, session: Session) -> list[Member]:
        raise NotImplementedError

    def save_member(self, session: Session, m: Member, password: str | None, original: str | None) -> None:
        """original=None: yeni üye (şifre zorunlu). Aksi halde o adlı üyeyi günceller (ad değişebilir)."""
        raise NotImplementedError

    def delete_member(self, session: Session, username: str) -> None:
        raise NotImplementedError

    def reset_hwid(self, session: Session, username: str) -> None:
        raise NotImplementedError

    def login_log(self, session: Session) -> list[dict]:
        return []

    def kick(self, session: Session, username: str) -> None:
        """Üyenin açık oturumlarını kapat: botu birkaç dakika içinde durur, yeniden giriş yapması gerekir."""

    def logout(self, session: Session) -> None:
        pass


def _dt(v) -> datetime | None:
    """ISO metni (saat dilimli olabilir) -> yerel saat (saat dilimsiz)."""
    if not v:
        return None
    try:
        d = datetime.fromisoformat(str(v).replace("Z", "+00:00"))
    except ValueError:
        return None
    if d.tzinfo is not None:
        d = d.astimezone().replace(tzinfo=None)
    return d


def _iso_utc(d: datetime | None) -> str | None:
    if d is None:
        return None
    return d.astimezone().astimezone(timezone.utc).isoformat()


# ====================================================================== yerel
def hash_password(password: str, salt: str | None = None) -> tuple[str, str]:
    salt = salt or secrets.token_hex(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), PBKDF2_ROUNDS)
    return salt, digest.hex()


class LocalUserStore:
    def __init__(self, path: str = USERS_PATH):
        self.path = path

    def load(self) -> dict:
        if not os.path.exists(self.path):
            return {}
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def save(self, users: dict) -> None:
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        tmp = self.path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(users, f, indent=2, ensure_ascii=False)
        os.replace(tmp, self.path)

    @staticmethod
    def to_member(u: dict) -> Member:
        return Member(username=u["username"], expires_at=_dt(u.get("expires")), active=u.get("active", True),
                      is_admin=u.get("admin", False), max_clients=int(u.get("max_clients", 0) or 0),
                      hwid_lock=u.get("hwid_lock", False), hwid=u.get("hwid", ""), note=u.get("note", ""),
                      created_at=_dt(u.get("created")), last_login=_dt(u.get("last_login")),
                      id=u.get("username", "").lower(), last_seen=_dt(u.get("last_login")))

    # yönetim işlemleri (tools/manage_users.py ve Üyeler sayfası kullanır)
    def add(self, username: str, password: str, days: int | None, admin: bool = False) -> None:
        """days=None ya da 0'dan küçük: süresiz."""
        users = self.load()
        key = username.strip().lower()
        if not key:
            raise AuthError("Kullanıcı adı boş olamaz.")
        if key in users:
            raise AuthError(f"'{username}' zaten var.")
        if not password:
            raise AuthError("Şifre boş olamaz.")
        salt, digest = hash_password(password)
        users[key] = {
            "username": username.strip(),
            "salt": salt,
            "hash": digest,
            "expires": None if days is None or days < 0 else
            (datetime.now() + timedelta(days=days)).isoformat(timespec="seconds"),
            "active": True,
            "admin": admin or not users,          # ilk üye yönetici olur
            "created": datetime.now().isoformat(timespec="seconds"),
        }
        self.save(users)

    def extend(self, username: str, days: int) -> datetime | None:
        users = self.load()
        u = users.get(username.lower())
        if not u:
            raise AuthError(f"'{username}' bulunamadı.")
        if u.get("expires") is None:
            return None                          # süresiz: uzatmaya gerek yok
        base = max(datetime.now(), datetime.fromisoformat(u["expires"]))
        new_exp = base + timedelta(days=days)
        u["expires"] = new_exp.isoformat(timespec="seconds")
        self.save(users)
        return new_exp

    def set_unlimited(self, username: str) -> None:
        users = self.load()
        u = users.get(username.lower())
        if not u:
            raise AuthError(f"'{username}' bulunamadı.")
        u["expires"] = None
        self.save(users)

    def set_password(self, username: str, password: str) -> None:
        users = self.load()
        u = users.get(username.lower())
        if not u:
            raise AuthError(f"'{username}' bulunamadı.")
        u["salt"], u["hash"] = hash_password(password)
        self.save(users)

    def set_active(self, username: str, active: bool) -> None:
        users = self.load()
        u = users.get(username.lower())
        if not u:
            raise AuthError(f"'{username}' bulunamadı.")
        u["active"] = active
        self.save(users)

    def remove(self, username: str) -> None:
        users = self.load()
        if users.pop(username.lower(), None) is None:
            raise AuthError(f"'{username}' bulunamadı.")
        self.save(users)


class LocalAuthProvider(AuthProvider):
    name = "local"

    def __init__(self, store: LocalUserStore | None = None):
        self.store = store or LocalUserStore()

    def login(self, username: str, password: str) -> Session:
        username = username.strip()
        if not username or not password:
            raise AuthError("Kullanıcı adı ve şifre gerekli.")
        users = self.store.load()
        u = users.get(username.lower())
        if not u:
            raise AuthError("Kullanıcı adı veya şifre hatalı.")
        _, digest = hash_password(password, u["salt"])
        if not hmac.compare_digest(digest, u["hash"]):
            raise AuthError("Kullanıcı adı veya şifre hatalı.")
        if not u.get("active", True):
            raise AuthError("Hesabınız askıya alınmış.")
        exp = _dt(u.get("expires"))
        if exp is not None and exp <= datetime.now():
            raise AuthError("Üyeliğinizin süresi dolmuş.")
        from .hwid import machine_id
        hw = machine_id()
        if u.get("hwid_lock") and u.get("hwid") and u["hwid"] != hw:
            raise AuthError("Bu hesap başka bir bilgisayara kilitli.")
        if not (u.get("hwid_lock") and u.get("hwid")):
            u["hwid"] = hw
        u["last_login"] = datetime.now().isoformat(timespec="seconds")
        self.store.save(users)
        return Session(username=u["username"], expires_at=exp, is_admin=bool(u.get("admin")),
                       max_clients=int(u.get("max_clients", 0) or 0))

    def verify(self, session: Session) -> bool:
        u = self.store.load().get(session.username.lower())
        if not u or not u.get("active", True):
            return False
        session.expires_at = _dt(u.get("expires"))
        session.max_clients = int(u.get("max_clients", 0) or 0)
        return session.is_valid

    def _need_admin(self, session: Session) -> dict:
        users = self.store.load()
        me = users.get(session.username.lower())
        if not me or not me.get("admin"):
            raise AuthError("Bu işlem için yönetici yetkisi gerekli.")
        return users

    def list_members(self, session: Session) -> list[Member]:
        users = self._need_admin(session)
        return [LocalUserStore.to_member(u) for u in sorted(users.values(), key=lambda x: x["username"].lower())]

    def save_member(self, session: Session, m: Member, password: str | None, original: str | None) -> None:
        users = self._need_admin(session)
        key = m.username.strip().lower()
        if not key:
            raise AuthError("Kullanıcı adı boş olamaz.")
        if original is None:
            if key in users:
                raise AuthError(f"'{m.username}' zaten var.")
            if not password:
                raise AuthError("Yeni üye için şifre gerekli.")
            u = {"created": datetime.now().isoformat(timespec="seconds")}
        else:
            u = users.pop(original.lower(), None)
            if u is None:
                raise AuthError(f"'{original}' bulunamadı.")
            if key in users:
                users[original.lower()] = u
                raise AuthError(f"'{m.username}' zaten var.")
        if password:
            u["salt"], u["hash"] = hash_password(password)
        u.update({"username": m.username.strip(),
                  "expires": None if m.expires_at is None else m.expires_at.isoformat(timespec="seconds"),
                  "active": m.active, "admin": m.is_admin, "max_clients": int(m.max_clients),
                  "hwid_lock": m.hwid_lock, "note": m.note})
        users[key] = u
        self.store.save(users)

    def delete_member(self, session: Session, username: str) -> None:
        users = self._need_admin(session)
        if username.lower() == session.username.lower():
            raise AuthError("Kendi hesabını silemezsin.")
        if users.pop(username.lower(), None) is None:
            raise AuthError(f"'{username}' bulunamadı.")
        self.store.save(users)

    def reset_hwid(self, session: Session, username: str) -> None:
        users = self._need_admin(session)
        u = users.get(username.lower())
        if u is None:
            raise AuthError(f"'{username}' bulunamadı.")
        u["hwid"] = ""
        self.store.save(users)


# ====================================================================== Supabase
class SupabaseAuthProvider(AuthProvider):
    """Supabase üzerinden üyelik. Sadece sql/supabase_kurulum.sql içindeki fonksiyonlar çağrılır
    (tablolar RLS ile kapalı; "anon" anahtarı tek başına hiçbir veriyi okuyamaz)."""

    name = "supabase"

    def __init__(self, url: str, anon_key: str, timeout: float = 12.0):
        self.url = url.rstrip("/")
        self.key = anon_key
        self.timeout = timeout

    def _headers(self) -> dict:
        h = {"apikey": self.key, "Content-Type": "application/json", "Accept": "application/json"}
        # eski "anon" anahtarı (eyJ… JWT) Authorization'a da yazılır; yeni "sb_publishable_…" anahtarı yazılmaz
        if not self.key.startswith("sb_"):
            h["Authorization"] = f"Bearer {self.key}"
        return h

    def _rpc(self, fn: str, args: dict):
        req = urllib.request.Request(
            f"{self.url}/rest/v1/rpc/{fn}", data=json.dumps(args).encode("utf-8"), method="POST",
            headers=self._headers())
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as r:
                body = r.read().decode("utf-8") or "null"
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode("utf-8")).get("message") or str(e)
            except Exception:
                msg = str(e)
            raise AuthError(msg) from None
        except (urllib.error.URLError, TimeoutError, OSError) as e:
            raise ConnectionError(f"Sunucuya bağlanılamadı: {e}") from None
        data = json.loads(body)
        if isinstance(data, dict) and data.get("ok") is False:
            raise AuthError(data.get("error") or "İşlem reddedildi.")
        return data

    def login(self, username: str, password: str) -> Session:
        username = username.strip()
        if not username or not password:
            raise AuthError("Kullanıcı adı ve şifre gerekli.")
        from .hwid import machine_id
        try:
            d = self._rpc("fb_login", {"p_username": username, "p_password": password, "p_hwid": machine_id()})
        except ConnectionError as e:
            raise AuthError(str(e)) from None
        return Session(username=d["username"], expires_at=_dt(d.get("expires_at")),
                       is_admin=bool(d.get("is_admin")), max_clients=int(d.get("max_clients") or 0),
                       token=str(d["token"]))

    def verify(self, session: Session) -> bool:
        try:
            d = self._rpc("fb_verify", {"p_token": session.token})
        except ConnectionError:
            return session.is_valid          # internet anlık koptuysa botu durdurma
        except AuthError:
            return False
        session.expires_at = _dt(d.get("expires_at"))
        session.max_clients = int(d.get("max_clients") or 0)
        session.is_admin = bool(d.get("is_admin"))
        return session.is_valid

    def list_members(self, session: Session) -> list[Member]:
        rows = self._rpc("fb_admin_list", {"p_token": session.token}) or []
        out = []
        for r in rows:
            out.append(Member(username=r["username"], expires_at=_dt(r.get("expires_at")),
                              active=bool(r.get("active", True)), is_admin=bool(r.get("is_admin")),
                              max_clients=int(r.get("max_clients") or 0), hwid_lock=bool(r.get("hwid_lock")),
                              hwid=r.get("hwid") or "", note=r.get("note") or "",
                              created_at=_dt(r.get("created_at")), last_login=_dt(r.get("last_login")),
                              id=str(r.get("id") or ""), sessions=int(r.get("sessions") or 0),
                              last_seen=_dt(r.get("last_seen"))))
        return out

    def save_member(self, session: Session, m: Member, password: str | None, original: str | None) -> None:
        self._rpc("fb_admin_save", {
            "p_token": session.token, "p_original": original, "p_username": m.username.strip(),
            "p_password": password or None, "p_expires_at": _iso_utc(m.expires_at),
            "p_active": m.active, "p_is_admin": m.is_admin, "p_max_clients": int(m.max_clients),
            "p_hwid_lock": m.hwid_lock, "p_note": m.note})

    def delete_member(self, session: Session, username: str) -> None:
        self._rpc("fb_admin_delete", {"p_token": session.token, "p_username": username})

    def reset_hwid(self, session: Session, username: str) -> None:
        self._rpc("fb_admin_reset_hwid", {"p_token": session.token, "p_username": username})

    def login_log(self, session: Session) -> list[dict]:
        rows = self._rpc("fb_admin_log", {"p_token": session.token, "p_limit": 200}) or []
        for r in rows:
            r["at"] = _dt(r.get("at"))
        return rows

    def kick(self, session: Session, username: str) -> None:
        self._rpc("fb_admin_kick", {"p_token": session.token, "p_username": username})

    def logout(self, session: Session) -> None:
        try:
            self._rpc("fb_logout", {"p_token": session.token})
        except Exception:
            pass


def make_provider() -> AuthProvider:
    from . import server
    if server.supabase_ready():
        return SupabaseAuthProvider(server.SUPABASE_URL, server.SUPABASE_ANON_KEY)
    return LocalAuthProvider()
