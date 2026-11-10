"""Üye yönetimi (komut satırı; argümansız açılırsa menü).

Örnekler:
    python tools/manage_users.py ekle ahmet Sifre123 30      # 30 günlük VIP
    python tools/manage_users.py uzat ahmet 30               # süreye 30 gün ekle
    python tools/manage_users.py sifre ahmet YeniSifre
    python tools/manage_users.py askiya ahmet                # girişi engelle
    python tools/manage_users.py aktif ahmet                 # tekrar aç
    python tools/manage_users.py sil ahmet
    python tools/manage_users.py liste
"""
import argparse
import os
import sys
from datetime import datetime

if not getattr(sys, "frozen", False):
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.auth import AuthError, LocalUserStore  # noqa: E402


def interactive() -> int:
    """Argümansız açılınca (ör. UyeYonetimi.exe'ye çift tıklayınca) basit menü."""
    store = LocalUserStore()
    while True:
        print("\n=== FishBot üye yönetimi ===")
        print("1) Üye ekle   2) Süre uzat   3) Şifre değiştir   4) Askıya al / aç   5) Sil   6) Liste   0) Çıkış")
        c = input("Seçim: ").strip()
        try:
            if c == "1":
                g = input("Kaç gün (süresiz için S): ").strip().lower()
                store.add(input("Kullanıcı adı: ").strip(), input("Şifre: "), None if g.startswith("s") else int(g),
                          admin=input("Yönetici mi? (E/H): ").strip().lower().startswith("e"))
                print("✓ Eklendi.")
            elif c == "2":
                u = input("Kullanıcı adı: ").strip()
                g = input("Kaç gün eklensin (süresiz yapmak için S): ").strip().lower()
                if g.startswith("s"):
                    store.set_unlimited(u)
                    print("✓ Süresiz yapıldı.")
                else:
                    exp = store.extend(u, int(g))
                    print(f"✓ Yeni bitiş: {exp:%d.%m.%Y %H:%M}" if exp else "✓ Zaten süresiz.")
            elif c == "3":
                store.set_password(input("Kullanıcı adı: ").strip(), input("Yeni şifre: "))
                print("✓ Şifre güncellendi.")
            elif c == "4":
                u = input("Kullanıcı adı: ").strip()
                on = input("A = aç, K = askıya al: ").strip().lower().startswith("a")
                store.set_active(u, on)
                print("✓ Güncellendi.")
            elif c == "5":
                store.remove(input("Kullanıcı adı: ").strip())
                print("✓ Silindi.")
            elif c == "6":
                sys.argv = [sys.argv[0], "liste"]
                main()
            elif c == "0":
                return 0
        except (AuthError, ValueError) as e:
            print(f"✗ {e}")


def main() -> int:
    if len(sys.argv) == 1:
        return interactive()
    p = argparse.ArgumentParser(description="FishBot VIP üye yönetimi")
    sub = p.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("ekle", help="yeni VIP üye")
    a.add_argument("kullanici")
    a.add_argument("sifre")
    a.add_argument("gun", help="gün sayısı ya da 'suresiz'")
    a.add_argument("--admin", action="store_true", help="yönetici yap")
    u = sub.add_parser("uzat", help="VIP süresini uzat")
    u.add_argument("kullanici")
    u.add_argument("gun", type=int)
    s = sub.add_parser("sifre", help="şifre değiştir")
    s.add_argument("kullanici")
    s.add_argument("sifre")
    for name, h in (("askiya", "girişi engelle"), ("aktif", "girişi aç"), ("sil", "üyeyi sil")):
        x = sub.add_parser(name, help=h)
        x.add_argument("kullanici")
    sub.add_parser("liste", help="tüm üyeler")
    args = p.parse_args()

    store = LocalUserStore()
    try:
        if args.cmd == "ekle":
            days = None if str(args.gun).lower().startswith("s") else int(args.gun)
            store.add(args.kullanici, args.sifre, days, admin=args.admin)
            print(f"✓ {args.kullanici} eklendi ({'süresiz' if days is None else str(days) + ' gün'}).")
        elif args.cmd == "uzat":
            exp = store.extend(args.kullanici, args.gun)
            print(f"✓ {args.kullanici} yeni bitiş: {exp:%d.%m.%Y %H:%M}" if exp else f"✓ {args.kullanici} zaten süresiz.")
        elif args.cmd == "sifre":
            store.set_password(args.kullanici, args.sifre)
            print("✓ Şifre güncellendi.")
        elif args.cmd in ("askiya", "aktif"):
            store.set_active(args.kullanici, args.cmd == "aktif")
            print(f"✓ {args.kullanici} {'aktif' if args.cmd == 'aktif' else 'askıya alındı'}.")
        elif args.cmd == "sil":
            store.remove(args.kullanici)
            print(f"✓ {args.kullanici} silindi.")
        elif args.cmd == "liste":
            users = store.load()
            if not users:
                print("Kayıtlı üye yok.")
            now = datetime.now()
            print(f"{'Kullanıcı':<20}{'Bitiş':<20}{'Kalan':<10}Durum")
            for u in sorted(users.values(), key=lambda x: x.get("expires") or "9999"):
                exp = datetime.fromisoformat(u["expires"]) if u.get("expires") else None
                left = "süresiz" if exp is None else str(max((exp - now).days, 0))
                state = "askıda" if not u.get("active", True) else ("süresi dolmuş" if exp and exp <= now else "aktif")
                if u.get("admin"):
                    state += " (yönetici)"
                bit = "—" if exp is None else f"{exp:%d.%m.%Y %H:%M}"
                print(f"{u['username']:<20}{bit:<20}{left:<10}{state}")
    except AuthError as e:
        print(f"✗ {e}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
