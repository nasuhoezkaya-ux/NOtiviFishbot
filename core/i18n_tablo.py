# -*- coding: utf-8 -*-
"""Çeviri tablosu: Türkçe metin -> (English, Deutsch). Yeni metin eklenirse buraya eklenir; tabloda olmayan
metin Türkçe gösterilir."""

TABLO = {
    # --- giriş penceresi
    "FishBot VIP • Giriş": ("FishBot VIP • Login", "FishBot VIP • Anmeldung"),
    "ÜYE GİRİŞİ": ("MEMBER LOGIN", "MITGLIEDER-LOGIN"),
    "VIP kullanıcı adınız": ("Your VIP username", "Dein VIP-Benutzername"),
    "Kullanıcı adını hatırla": ("Remember username", "Benutzernamen merken"),
    "Giriş Yap": ("Log in", "Anmelden"),
    "Bot yalnızca VIP kart sahibi üyeler içindir.": ("The bot is for VIP members only.",
                                                    "Der Bot ist nur für VIP-Mitglieder."),
    "Doğrulanıyor…": ("Verifying…", "Wird geprüft…"),
    "Kullanıcı adı": ("Username", "Benutzername"),
    "Şifre": ("Password", "Passwort"),
    "Henüz hiç VIP üye yok. Bot klasöründeki uye_ekle.bat ile bir üye oluştur.":
        ("There are no VIP members yet. Create one with uye_ekle.bat in the bot folder.",
         "Es gibt noch keine VIP-Mitglieder. Lege eins mit uye_ekle.bat im Bot-Ordner an."),
    # --- birimler
    " sn": (" s", " s"), " ms": (" ms", " ms"), " dk": (" min", " Min."), " kare/sn": (" fps", " FPS"),
    "ile": ("to", "bis"),
    # --- ayarlar
    "Ayarlar": ("Settings", "Einstellungen"),
    "↺  Önerilen ayarlar": ("↺  Recommended settings", "↺  Empfohlene Einstellungen"),
    "Önerilen ayarlar": ("Recommended settings", "Empfohlene Einstellungen"),
    "Balık sistemi": ("Fishing system", "Angelsystem"),
    "Space ile olta atılır → karakterinin kafasında balık işareti çıkınca Space → açılan pencerede siyah balık "
    "kutucuğun ORTASINA (mor nokta) gelince Space → ödül çarkı kendiliğinden döner → pencere kapanınca baştan. "
    "Kutucuğun yeri her seferinde bulunur; tuş gecikmesi her turda ölçülüp öğrenilir.":
        ("Space casts the rod → when the fish icon appears above your character, Space → in the window that opens, "
         "Space when the black fish reaches the CENTER of the box (purple dot) → the reward wheel spins by itself → "
         "when the window closes it starts over. The box is located every time; the key delay is measured and "
         "learned every round.",
         "Mit Leertaste wird die Angel ausgeworfen → erscheint das Fisch-Symbol über deinem Charakter, Leertaste → "
         "im Fenster Leertaste, wenn der schwarze Fisch die MITTE des Kästchens (violetter Punkt) erreicht → das "
         "Belohnungsrad dreht sich von selbst → schließt sich das Fenster, beginnt alles von vorn. Das Kästchen "
         "wird jedes Mal gefunden; die Tastenverzögerung wird jede Runde gemessen und gelernt."),
    "her turda kendisi öğrensin": ("learn it automatically every round", "jede Runde selbst lernen"),
    "İşaret resimle bulunamazsa ani beliren şekille de ara (yedek)":
        ("If the icon image isn't found, also look for a suddenly appearing shape (fallback)",
         "Wird das Symbolbild nicht gefunden, auch nach plötzlich erscheinender Form suchen (Reserve)"),
    'Pencere açıkken "Pencere testi"ne bas: bot kutucuğu ve balığı bulabiliyor mu gösterir.':
        ('Press "Window test" while the window is open: shows whether the bot finds the box and the fish.',
         'Drücke "Fenstertest", während das Fenster offen ist: zeigt, ob der Bot Kästchen und Fisch findet.'),
    "Pencere testi": ("Window test", "Fenstertest"),
    "İşaret testi": ("Icon test", "Symboltest"),
    "İşaret klasörü": ("Icon folder", "Symbolordner"),
    "🎯  Alanı seç…": ("🎯  Select area…", "🎯  Bereich wählen…"),
    "Kendi karakterimin işaret alanı": ("My character's icon area", "Symbolbereich meines Charakters"),
    "Balık işaretini en fazla bekle": ("Max. wait for the fish icon", "Max. Wartezeit auf das Fisch-Symbol"),
    "İşareti görünce basmadan önce": ("Before pressing after the icon", "Vor dem Drücken nach dem Symbol"),
    "Tuş gecikmesi payı": ("Key delay allowance", "Tastenverzögerung"),
    "İşaret arama": ("Icon search", "Symbolsuche"),
    "Test": ("Test", "Test"),
    "Olta ve giriş": ("Rod and input", "Angel und Eingabe"),
    "Tuşun oyuna nasıl gönderileceği ve turlar arasındaki bekleme.":
        ("How the key is sent to the game and the pause between rounds.",
         "Wie die Taste an das Spiel gesendet wird und die Pause zwischen den Runden."),
    "⌨  Tuşu test et": ("⌨  Test key", "⌨  Taste testen"),
    "Tuşu test et": ("Test key", "Taste testen"),
    "Karakterin elinde olta varken bas.": ("Press while your character holds the rod.",
                                          "Drücken, während dein Charakter die Angel hält."),
    "Açık": ("On", "An"),
    "Tuş": ("Key", "Taste"),
    "Giriş yöntemi": ("Input method", "Eingabemethode"),
    "Tuş testi": ("Key test", "Tastentest"),
    "Ödülden sonra olta atmadan önce": ("Before casting after the reward", "Vor dem Auswerfen nach der Belohnung"),
    "Akıllı mola": ("Smart break", "Intelligente Pause"),
    "Mola sıklığı": ("Break frequency", "Pausenabstand"),
    "Mola süresi": ("Break length", "Pausenlänge"),
    "Canlı görüntü kare hızı": ("Live view frame rate", "Bildrate der Live-Ansicht"),
    "İşaret arama hızı": ("Icon search rate", "Symbol-Suchrate"),
    "Captcha (bot kontrolü)": ("Captcha (bot check)", "Captcha (Bot-Prüfung)"),
    'Sunucu "Atın üzerine tıklayın" gibi bir doğrulama penceresi açınca bot balık tutmayı durdurur, ne istendiğini '
    'okur ve doğru simgeye tıklar. Çözemezse sesli uyarır ve sen çözene kadar bekler.':
        ('When the server opens a check window like "Click on the horse", the bot stops fishing, reads what is asked '
         'and clicks the right icon. If it can\'t, it beeps and waits until you solve it.',
         'Öffnet der Server ein Prüffenster wie "Klicke auf das Pferd", hört der Bot auf zu angeln, liest die '
         'Aufgabe und klickt das richtige Symbol. Schafft er es nicht, piept er und wartet, bis du es löst.'),
    "Otomatik çöz": ("Solve automatically", "Automatisch lösen"),
    "Sesli uyar": ("Beep", "Signalton"),
    'Captcha ekrandayken "Captcha testi"ne bas: bot ne okuduğunu ve nereye tıklayacağını gösterir (tıklamaz).':
        ('Press "Captcha test" while a captcha is on screen: shows what the bot reads and where it would click '
         '(it doesn\'t click).',
         'Drücke "Captcha-Test", während ein Captcha zu sehen ist: zeigt, was der Bot liest und wohin er klicken '
         'würde (er klickt nicht).'),
    "Captcha testi": ("Captcha test", "Captcha-Test"),
    "Resim klasörünü aç": ("Open image folder", "Bildordner öffnen"),
    "Captcha": ("Captcha", "Captcha"),
    "Elle çözüm için en fazla bekle": ("Max. wait for manual solving", "Max. Wartezeit auf manuelles Lösen"),
    "Client'lar ve kısayollar": ("Clients and shortcuts", "Clients und Tastenkürzel"),
    "Hangi pencerelerin oyun client'ı sayılacağı.": ("Which windows count as game clients.",
                                                    "Welche Fenster als Spiel-Clients gelten."),
    "Temizle": ("Clear", "Leeren"),
    "Client seçme tuşu": ("Client pick key", "Taste zur Client-Auswahl"),
    "Süreç filtresi": ("Process filter", "Prozessfilter"),
    "Hatırlanan client'lar": ("Remembered clients", "Gemerkte Clients"),
    "Engellenen programlar": ("Blocked programs", "Gesperrte Programme"),
    "Kaydet": ("Save", "Speichern"),
    "Önerilen değerler yüklendi — uygulamak için Kaydet'e bas.": ("Recommended values loaded — press Save to apply.",
                                                                 "Empfohlene Werte geladen — zum Übernehmen Speichern drücken."),
    "Pencere testi: ekran okunuyor…": ("Window test: reading the screen…", "Fenstertest: Bildschirm wird gelesen…"),
    "Captcha: ekran okunuyor…": ("Captcha: reading the screen…", "Captcha: Bildschirm wird gelesen…"),
    "Kayıtlar": ("Logs", "Protokoll"),
    "Her ayarın yanındaki <b style='color:%s'>?</b> simgesinin üstüne gel: ne işe yaradığı, önerilen değer ve "
    "artırınca / azaltınca ne olacağı yazar.":
        ("Hover over the <b style='color:%s'>?</b> next to each setting: it explains what it does, the recommended "
         "value and what happens when you raise / lower it.",
         "Fahre über das <b style='color:%s'>?</b> neben jeder Einstellung: es erklärt die Funktion, den empfohlenen "
         "Wert und was beim Erhöhen / Verringern passiert."),
    "Bütün alanları önerilen değerlere getirir. Kaydet'e basana kadar uygulanmaz. Seçtiğin işaret alanı, öğrenilen "
    "gecikme ve kısayollar değişmez.":
        ("Sets all fields to the recommended values. Not applied until you press Save. Your icon area, the learned "
         "delay and the shortcuts are kept.",
         "Setzt alle Felder auf die empfohlenen Werte. Wird erst mit Speichern übernommen. Dein Symbolbereich, die "
         "gelernte Verzögerung und die Tastenkürzel bleiben."),
    "Seçilmedi: ekranın ortasındaki (kendi) karakterine en yakın işaret kullanılır. Yanında balık tutan oyuncular "
    "varsa alanı seç.":
        ("Not selected: the icon closest to your character in the middle of the screen is used. If other players "
         "fish next to you, select the area.",
         "Nicht gewählt: Das Symbol, das deinem Charakter in der Bildschirmmitte am nächsten ist, wird verwendet. "
         "Angeln andere Spieler neben dir, wähle den Bereich."),
    "Önce Panel'de bir client seç (F7 veya listeden tıkla).": ("First select a client (F7 or click it in the list).",
                                                             "Wähle zuerst einen Client (F7 oder in der Liste klicken)."),
    "Pencere testi: önce Panel'de bir client seç (F7 veya listeden tıkla).":
        ("Window test: first select a client (F7 or click it in the list).",
         "Fenstertest: wähle zuerst einen Client (F7 oder in der Liste klicken)."),
    "İşaret testi: önce Panel'de bir client seç (F7 veya listeden tıkla).":
        ("Icon test: first select a client (F7 or click it in the list).",
         "Symboltest: wähle zuerst einen Client (F7 oder in der Liste klicken)."),
    "Captcha: önce Panel'de bir client seç (F7 veya listeden tıkla).":
        ("Captcha: first select a client (F7 or click it in the list).",
         "Captcha: wähle zuerst einen Client (F7 oder in der Liste klicken)."),
    "Dil değişikliği program yeniden başlatılınca uygulanır.": ("The language change applies after restarting the program.",
                                                               "Die Sprachänderung gilt nach einem Neustart des Programms."),
    "Süresiz VIP": ("Unlimited VIP", "Unbegrenztes VIP"),
    "VIP üyeliğinin süresi doldu. Botlar durduruldu.": ("Your VIP membership has expired. Bots stopped.",
                                                       "Deine VIP-Mitgliedschaft ist abgelaufen. Bots gestoppt."),
    "Farenin altında bir pencere bulunamadı. Fareyi oyun penceresinin üstüne getirip tekrar dene.":
        ("No window under the mouse. Move the mouse over the game window and try again.",
         "Unter der Maus ist kein Fenster. Bewege die Maus über das Spielfenster und versuche es erneut."),
    "Pencere testi: oyun penceresinin görüntüsü alınamadı.": ("Window test: couldn't capture the game window.",
                                                             "Fenstertest: Spielfenster konnte nicht aufgenommen werden."),
    "İşaret testi: oyun penceresinin görüntüsü alınamadı.": ("Icon test: couldn't capture the game window.",
                                                            "Symboltest: Spielfenster konnte nicht aufgenommen werden."),
    "Captcha: oyun penceresinin görüntüsü alınamadı.": ("Captcha: couldn't capture the game window.",
                                                       "Captcha: Spielfenster konnte nicht aufgenommen werden."),
    "{0} gönderiliyor → PID {1} ({2})…": ("Sending {0} → PID {1} ({2})…", "Sende {0} → PID {1} ({2})…"),
    "Hatırlanan client'lar: {0}": ("Remembered clients: {0}", "Gemerkte Clients: {0}"),
    "✓ Kaydedildi ({0}). Çalışan botlar yeni ayarları hemen kullanır.":
        ("✓ Saved ({0}). Running bots use the new settings right away.",
         "✓ Gespeichert ({0}). Laufende Bots verwenden die neuen Einstellungen sofort."),
    "Hoş geldin {0}. VIP bitiş: {1:%d.%m.%Y %H:%M}": ("Welcome {0}. VIP until: {1:%d.%m.%Y %H:%M}",
                                                     "Willkommen {0}. VIP bis: {1:%d.%m.%Y %H:%M}"),
    "✓ Client seçildi: PID {0} • {1} ({2}). İşaretlendi, 'Seçilileri Başlat' ile başlatabilirsin.":
        ("✓ Client selected: PID {0} • {1} ({2}). You can start it now.",
         "✓ Client gewählt: PID {0} • {1} ({2}). Du kannst ihn jetzt starten."),
    "{0} ile client seçildi: PID {1} • {2} ({3})": ("Client selected with {0}: PID {1} • {2} ({3})",
                                                   "Client mit {0} gewählt: PID {1} • {2} ({3})"),
    "onizleme (bot calismiyor)": ("preview (bot not running)", "Vorschau (Bot laeuft nicht)"),
    "Seçili: {0}×{1} px — bot sadece buradaki işarete tepki verir.":
        ("Selected: {0}×{1} px — the bot only reacts to the icon here.",
         "Gewählt: {0}×{1} px — der Bot reagiert nur auf das Symbol hier."),
    "Pencere testi: zamanlama penceresi bulunamadı. Pencere ekrandayken (siyah balık giderken) tekrar dene.":
        ("Window test: timing window not found. Try again while it is on screen (while the black fish moves).",
         "Fenstertest: Timing-Fenster nicht gefunden. Erneut versuchen, während es zu sehen ist (der schwarze Fisch "
         "sich bewegt)."),
    "İşaret testi: henüz işaret resmi yok. Bot ilk balıkta işareti kendisi öğrenir; istersen işaretin ekran "
    "görüntüsünü kırpıp assets\\olta\\isaret klasörüne koy.":
        ("Icon test: no icon image yet. The bot learns the icon at the first fish; or crop a screenshot of the icon "
         "and put it into assets\\olta\\isaret.",
         "Symboltest: noch kein Symbolbild. Der Bot lernt das Symbol beim ersten Fisch; oder schneide einen "
         "Screenshot des Symbols aus und lege ihn in assets\\olta\\isaret."),
    "✓ {0} gönderildi (PID {1}, {2}). Oyunda olta atıldıysa bu yöntem çalışıyor; Kaydet'e bas. Atılmadıysa başka bir "
    "yöntem dene.":
        ("✓ {0} sent (PID {1}, {2}). If the rod was cast in the game, this method works; press Save. If not, try "
         "another method.",
         "✓ {0} gesendet (PID {1}, {2}). Wurde die Angel im Spiel ausgeworfen, funktioniert diese Methode; "
         "Speichern drücken. Sonst eine andere Methode probieren."),
    "{0} gün kaldı • {1:%d.%m.%Y}": ("{0} days left • {1:%d.%m.%Y}", "noch {0} Tage • {1:%d.%m.%Y}"),
    "{0} engellendi; artık client olarak listelenmeyecek.": ("{0} blocked; it won't be listed as a client anymore.",
                                                            "{0} gesperrt; wird nicht mehr als Client gelistet."),
    "PID {0} listeden kaldırıldı (bu oturum için).": ("PID {0} removed from the list (for this session).",
                                                      "PID {0} aus der Liste entfernt (für diese Sitzung)."),
    "Pencere testi: hata — {0}": ("Window test: error — {0}", "Fenstertest: Fehler — {0}"),
    "İşaret testi: hata — {0}": ("Icon test: error — {0}", "Symboltest: Fehler — {0}"),
    "İşaret klasörü: {0} ({1})": ("Icon folder: {0} ({1})", "Symbolordner: {0} ({1})"),
    "Captcha klasörü: {0} ({1})": ("Captcha folder: {0} ({1})", "Captcha-Ordner: {0} ({1})"),
    "Captcha testi hatası: {0!r}": ("Captcha test error: {0!r}", "Captcha-Test-Fehler: {0!r}"),
    "Hata: {0}": ("Error: {0}", "Fehler: {0}"),
    "Hata: {0!r}": ("Error: {0!r}", "Fehler: {0!r}"),
    "Client'lar": ("Clients", "Clients"),
    "Açık oyun pencereleri. Bir client'a tıkla: canlı görüntü, istatistik, turlar ve Başlat/Durdur. F7 ile fare "
    "altındaki pencereyi seçebilirsin.":
        ("Open game windows. Click a client: live view, statistics, rounds and Start/Stop. F7 picks the window under "
         "the mouse.",
         "Offene Spielfenster. Klicke einen Client: Live-Ansicht, Statistik, Runden und Start/Stopp. F7 wählt das "
         "Fenster unter der Maus."),
    "Balık sistemi, işaret alanı, tuş, captcha ve client ayarları — hepsi açıklamalı.":
        ("Fishing system, icon area, key, captcha and client settings — all explained.",
         "Angelsystem, Symbolbereich, Taste, Captcha und Client-Einstellungen — alle erklärt."),
    "Botun olay günlüğü: atılan oltalar, isabetler, uyarılar.": ("The bot's event log: casts, hits, warnings.",
                                                               "Ereignisprotokoll des Bots: Würfe, Treffer, Warnungen."),
    "■ {0} ile tüm botlar durduruldu.": ("■ All bots stopped with {0}.", "■ Alle Bots mit {0} gestoppt."),
    "{0} ile tüm botlar durduruldu.": ("All bots stopped with {0}.", "Alle Bots mit {0} gestoppt."),
    "KUTUCUK BULUNAMADI": ("BOX NOT FOUND", "KÄSTCHEN NICHT GEFUNDEN"),
    "BALIK BULUNAMADI": ("FISH NOT FOUND", "FISCH NICHT GEFUNDEN"),
    "Pencere testi: ✓ pencere bulundu — ": ("Window test: ✓ window found — ", "Fenstertest: ✓ Fenster gefunden — "),
    "✓ işaret ekranda.": ("✓ the icon is on screen.", "✓ das Symbol ist zu sehen."),
    "işaret şu an ekranda değil (işaret görünürken tekrar dene).":
        ("the icon is not on screen right now (try again while it is visible).",
         "das Symbol ist gerade nicht zu sehen (erneut versuchen, wenn es sichtbar ist)."),
    "çubuk {w}×{h} px": ("bar {w}×{h} px", "Leiste {w}×{h} px"),
    "İşaret testi: {0} resim, en iyi benzerlik {1:.2f} (eşik {2:.2f}) — ":
        ("Icon test: {0} image(s), best similarity {1:.2f} (threshold {2:.2f}) — ",
         "Symboltest: {0} Bild(er), beste Ähnlichkeit {1:.2f} (Schwelle {2:.2f}) — "),
    "Captcha: ekranda captcha bulunamadı. [{0}] ": ("Captcha: no captcha on screen. [{0}] ",
                                                   "Captcha: kein Captcha zu sehen. [{0}] "),
    " [{0}] Kayıtlı resimler: {1}": (" [{0}] Saved images: {1}", " [{0}] Gespeicherte Bilder: {1}"),
    "kutucuk x={a}-{b}": ("box x={a}-{b}", "Kästchen x={a}-{b}"),
    "balık x={x}": ("fish x={x}", "Fisch x={x}"),
    "balık kutucuk ortasına {d} px": ("fish to box center {d} px", "Fisch zur Kästchenmitte {d} px"),
    # --- tarama penceresi
    "Tarama — canlı kayıt": ("Scan — live log", "Scan — Live-Protokoll"),
    "Client: —": ("Client: —", "Client: —"),
    "isabet / ıska: 0 / 0": ("hits / misses: 0 / 0", "Treffer / daneben: 0 / 0"),
    "gecikme: — ms": ("delay: — ms", "Verzögerung: — ms"),
    "son: —": ("last: —", "zuletzt: —"),
    "Sadece olaylar": ("Events only", "Nur Ereignisse"),
    "Sadece ▶ ile başlayan olayları (işaret, isabet, ıska, captcha vb.) göster":
        ("Show only events starting with ▶ (icon, hit, miss, captcha, …)",
         "Nur Ereignisse mit ▶ anzeigen (Symbol, Treffer, daneben, Captcha, …)"),
    "Duraklat": ("Pause", "Pause"),
    "Kayıt klasörünü aç": ("Open log folder", "Protokollordner öffnen"),
    "Her satır data/tarama/ klasörüne de kaydedilir. Sorun olursa o dosyayı gönderebilirsin.":
        ("Every line is also saved to data/tarama/. If there is a problem you can send that file.",
         "Jede Zeile wird auch in data/tarama/ gespeichert. Bei Problemen kannst du diese Datei schicken."),
    "Devam": ("Resume", "Weiter"),
    "isabet / ıska: {0} / {1}": ("hits / misses: {0} / {1}", "Treffer / daneben: {0} / {1}"),
    "gecikme: {0} ms": ("delay: {0} ms", "Verzögerung: {0} ms"),
    "son: hedefe {0:+d} px": ("last: {0:+d} px from target", "zuletzt: {0:+d} px vom Ziel"),
    # --- panel
    "…  Duruyor": ("…  Stopping", "…  Stoppt"),
    "önizleme": ("preview", "Vorschau"),
    "Listeden kaldır": ("Remove from list", "Aus Liste entfernen"),
    "▶  Başlat": ("▶  Start", "▶  Start"),
    "Detay  →": ("Details  →", "Details  →"),
    "⟳  Yenile": ("⟳  Refresh", "⟳  Aktualisieren"),
    "▶  Tümünü Başlat": ("▶  Start all", "▶  Alle starten"),
    "■  Tümünü Durdur": ("■  Stop all", "■  Alle stoppen"),
    "■  Tümünü Durdur ({0})": ("■  Stop all ({0})", "■  Alle stoppen ({0})"),
    "Toplam tur": ("Total rounds", "Runden gesamt"),
    "İsabet": ("Hits", "Treffer"),
    "Iska": ("Misses", "Daneben"),
    "İsabet oranı": ("Hit rate", "Trefferquote"),
    "Ödül çarkı": ("Reward wheel", "Belohnungsrad"),
    "Aktif bot": ("Active bots", "Aktive Bots"),
    "Oyun client'ları": ("Game clients", "Spiel-Clients"),
    "Son turlar": ("Last rounds", "Letzte Runden"),
    "Özet": ("Summary", "Übersicht"),
    "Henüz tur yok": ("No rounds yet", "Noch keine Runden"),
    "Sıfırla": ("Reset", "Zurücksetzen"),
    "Kazanılan ödüller": ("Rewards won", "Gewonnene Belohnungen"),
    "Henüz yok": ("None yet", "Noch keine"),
    "←  Tüm client'lar": ("←  All clients", "←  Alle Clients"),
    "✕  Listeden kaldır": ("✕  Remove from list", "✕  Aus Liste entfernen"),
    "Canlı izleme": ("Live view", "Live-Ansicht"),
    "Görüntü bekleniyor…": ("Waiting for image…", "Warte auf Bild…"),
    "<b>Zamanlama:</b> <span style='color:#3ce63c'>■</span> kutucuk &nbsp; <span style='color:#ff28c8'>●</span> hedef "
    "(kutucuğun tam ortası) &nbsp; <span style='color:#ff2828'>■</span> siyah balık &nbsp; <span "
    "style='color:#ffdc00'>●</span> tuş oyuna ulaştığında balığın yeri &nbsp; ✕ balığın durduğu yer<br><b>Balık "
    "beklerken:</b> <span style='color:#28a0ff'>■</span> arama alanı &nbsp; <span style='color:#ff28c8'>+</span> "
    "kendi kafan &nbsp; <span style='color:#3ce63c'>■</span> senin işaretin &nbsp; <span "
    "style='color:#969696'>■</span> başka oyuncuların işareti (yok sayılır)":
        ("<b>Timing:</b> <span style='color:#3ce63c'>■</span> box &nbsp; <span style='color:#ff28c8'>●</span> target "
         "(exact box center) &nbsp; <span style='color:#ff2828'>■</span> black fish &nbsp; <span "
         "style='color:#ffdc00'>●</span> fish position when the key arrives &nbsp; ✕ where the fish stopped<br><b>While "
         "waiting:</b> <span style='color:#28a0ff'>■</span> search area &nbsp; <span style='color:#ff28c8'>+</span> "
         "your head &nbsp; <span style='color:#3ce63c'>■</span> your icon &nbsp; <span "
         "style='color:#969696'>■</span> other players' icons (ignored)",
         "<b>Timing:</b> <span style='color:#3ce63c'>■</span> Kästchen &nbsp; <span style='color:#ff28c8'>●</span> "
         "Ziel (genaue Kästchenmitte) &nbsp; <span style='color:#ff2828'>■</span> schwarzer Fisch &nbsp; <span "
         "style='color:#ffdc00'>●</span> Fischposition, wenn die Taste ankommt &nbsp; ✕ wo der Fisch stoppte<br><b>Beim "
         "Warten:</b> <span style='color:#28a0ff'>■</span> Suchbereich &nbsp; <span style='color:#ff28c8'>+</span> "
         "dein Kopf &nbsp; <span style='color:#3ce63c'>■</span> dein Symbol &nbsp; <span "
         "style='color:#969696'>■</span> Symbole anderer Spieler (ignoriert)"),
    "🎯  İşaret alanımı seç": ("🎯  Select my icon area", "🎯  Meinen Symbolbereich wählen"),
    "📈  Tarama penceresi": ("📈  Scan window", "📈  Scan-Fenster"),
    "📸  Anlık kayıt": ("📸  Snapshot", "📸  Schnappschuss"),
    "Oran": ("Rate", "Quote"),
    "Tuş gecikmesi": ("Key delay", "Tastenverzögerung"),
    "— ms": ("— ms", "— ms"),
    "Client bilgileri": ("Client info", "Client-Infos"),
    "Bu client'ın turları": ("This client's rounds", "Runden dieses Clients"),
    "Client'ı kaldır": ("Remove client", "Client entfernen"),
    "Sadece bu pencereyi mi kaldırmak istiyorsun, yoksa bu programı hiç listelememeyi mi?":
        ("Remove only this window, or never list this program again?",
         "Nur dieses Fenster entfernen oder dieses Programm nie mehr auflisten?"),
    "Sadece bu pencere": ("Only this window", "Nur dieses Fenster"),
    "{0} programını engelle": ("Block {0}", "{0} sperren"),
    "Vazgeç": ("Cancel", "Abbrechen"),
    "Bot, siyah balık mor noktaya varırken Space'e basar; tuş gecikmesini her turda balığın durduğu yere bakarak "
    "kendisi düzeltir.":
        ("The bot presses Space as the black fish reaches the purple dot; it corrects the key delay every round by "
         "looking at where the fish stopped.",
         "Der Bot drückt die Leertaste, wenn der schwarze Fisch den violetten Punkt erreicht; die Tastenverzögerung "
         "korrigiert er jede Runde anhand der Stelle, an der der Fisch stoppte."),
    "Bu oturumda henüz yok": ("None in this session yet", "In dieser Sitzung noch keine"),
    "■  Durdur": ("■  Stop", "■  Stopp"),
    "otomatik (ekranın ortası)": ("automatic (screen center)", "automatisch (Bildschirmmitte)"),
    "yok (ilk balıkta öğrenilir)": ("none (learned at the first fish)", "keins (wird beim ersten Fisch gelernt)"),
    "Önce canlı görüntü gelmeli.": ("Wait for the live view first.", "Warte zuerst auf die Live-Ansicht."),
    "Tüm zamanların ödül toplamları sıfırlansın mı?": ("Reset the all-time reward totals?",
                                                       "Belohnungssummen aller Zeiten zurücksetzen?"),
    "Durduruldu": ("Stopped", "Gestoppt"),
    "🎯\n\nHenüz client yok.\nOyunda fareyi oyun penceresinin üstüne getir ve {0} tuşuna bas.":
        ("🎯\n\nNo clients yet.\nMove the mouse over the game window and press {0}.",
         "🎯\n\nNoch keine Clients.\nBewege die Maus über das Spielfenster und drücke {0}."),
    "son {0}:  ✓ {1}   ✗ {2}": ("last {0}:  ✓ {1}   ✗ {2}", "letzte {0}:  ✓ {1}   ✗ {2}"),
    "✓ Kaydedildi: data\\anlik\\{0}_anlik.png": ("✓ Saved: data\\anlik\\{0}_anlik.png", "✓ Gespeichert: data\\anlik\\{0}_anlik.png"),
    "Önce {0} ile bir client seç.": ("First select a client with {0}.", "Wähle zuerst mit {0} einen Client."),
    "  simge durumunda!": ("  minimized!", "  minimiert!"),
    "✓ seçili  {0}×{1}": ("✓ selected  {0}×{1}", "✓ gewählt  {0}×{1}"),
    ", ölçek ilk balıkta bulunur": (", scale found at the first fish", ", Maßstab beim ersten Fisch ermittelt"),
    ", ölçek {s}": (", scale {s}", ", Maßstab {s}"),
    "{n} resim": ("{n} image(s)", "{n} Bild(er)"),
    "Tüm zamanlar": ("All time", "Alle Zeiten"),
    "{n} kez": ("{n}×", "{n}×"),
    "Olta atıldı": ("Casts", "Würfe"),
    "Balık işareti gelmedi": ("No fish icon", "Kein Fisch-Symbol"),
    "Yanlış alarm": ("False alarms", "Fehlalarme"),
    "Çözülen captcha": ("Captchas solved", "Gelöste Captchas"),
    "Program": ("Program", "Programm"),
    "Çözünürlük": ("Resolution", "Auflösung"),
    "Ekran konumu": ("Screen position", "Bildschirmposition"),
    "Ölçekleme": ("Scaling", "Skalierung"),
    "İşaret alanı": ("Icon area", "Symbolbereich"),
    "İşaret resmi": ("Icon image", "Symbolbild"),
    "Hedefe ortalama uzaklık": ("Avg. distance to target", "Mittl. Abstand zum Ziel"),
    "Son sonuç": ("Last result", "Letztes Ergebnis"),
    "Çalışma süresi": ("Uptime", "Laufzeit"),
    "oyun ölçeklemeyi bilmiyor": ("game is not DPI-aware", "Spiel kennt keine Skalierung"),
    "sistem": ("system", "System"),
    "monitör": ("monitor", "Monitor"),
    "Karma (önerilen)": ("Hybrid (recommended)", "Hybrid (empfohlen)"),
    "Arka plan": ("Background", "Hintergrund"),
    "Ön plan": ("Foreground", "Vordergrund"),
    "Hazır": ("Ready", "Bereit"),
    # --- ipuçları (help)
    "Yanında balık tutan başka oyuncular varsa onların kafasında da balık işareti çıkar. Burada kendi karakterinin "
    "kafasının üstünü seçersen bot SADECE oradaki işarete tepki verir. Seçmezsen ekranın ortasındaki karaktere "
    "(seninkine) en yakın işaret kullanılır; olta atılır atılmaz ekranda olan işaretler de başkasınındır diye yok "
    "sayılır. Canlı görüntüde başkalarının işaretleri gri ('baskasi'), seninki yeşil görünür.":
        ("If other players fish next to you, the fish icon also appears above their heads. If you select the area "
         "above your own head here, the bot reacts ONLY to the icon there. Otherwise the icon closest to the "
         "character in the middle of the screen (yours) is used; icons already visible right after casting are "
         "treated as someone else's. In the live view other players' icons are gray, yours is green.",
         "Angeln andere Spieler neben dir, erscheint das Fisch-Symbol auch über ihren Köpfen. Wählst du hier den "
         "Bereich über deinem Kopf, reagiert der Bot NUR auf das Symbol dort. Sonst wird das Symbol verwendet, das "
         "dem Charakter in der Bildschirmmitte (deinem) am nächsten ist; Symbole, die direkt nach dem Auswerfen "
         "schon zu sehen sind, gelten als fremd. In der Live-Ansicht sind fremde Symbole grau, deins grün."),
    "Yanında oyuncu varsa seç": ("Select if players are next to you", "Wählen, wenn Spieler neben dir sind"),
    "Olta atıldıktan sonra bu sürede işaret görülmezse olta yeniden atılır.":
        ("If no icon is seen within this time after casting, the rod is cast again.",
         "Wird nach dem Auswerfen in dieser Zeit kein Symbol gesehen, wird neu ausgeworfen."),
    "40 sn": ("40 s", "40 s"),
    "İnsan gibi görünmek için işaret ile Space arasında rastgele kısa bir bekleme.":
        ("A short random pause between the icon and Space, to look human.",
         "Eine kurze zufällige Pause zwischen Symbol und Leertaste, um menschlich zu wirken."),
    "90 – 200 ms": ("90 – 200 ms", "90 – 200 ms"),
    "Daha insansı ama işaret kısa sürüyorsa kaçabilir.": ("More human, but a short icon may be missed.",
                                                          "Menschlicher, aber ein kurzes Symbol kann verpasst werden."),
    "Daha hızlı tepki.": ("Faster reaction.", "Schnellere Reaktion."),
    "Space'e basıldığı an ile oyunun bunu işlediği an arasındaki süre. Bot, balık kutucuğun ortasına bu kadar süre "
    "KALA basar. 'Kendisi öğrensin' açıksa her turda balığın durduğu yere bakılıp düzeltilir.":
        ("The time between pressing Space and the game processing it. The bot presses this much BEFORE the fish "
         "reaches the box center. With automatic learning it is corrected every round from where the fish stopped.",
         "Die Zeit zwischen dem Drücken der Leertaste und der Verarbeitung im Spiel. Der Bot drückt um diese Zeit "
         "VOR dem Erreichen der Kästchenmitte. Mit automatischem Lernen wird sie jede Runde anhand der Stoppstelle "
         "korrigiert."),
    "45 ms + otomatik": ("45 ms + automatic", "45 ms + automatisch"),
    "Daha erken basar.": ("Presses earlier.", "Drückt früher."),
    "Daha geç basar.": ("Presses later.", "Drückt später."),
    "assets\\olta\\isaret klasöründe işaret resmi varsa onunla aranır (en güvenilir). Yoksa kafa bölgesinde aniden "
    "çıkıp yerinde duran yeni bir şekil aranır; Space'ten sonra pencere açılınca o şekil işaret resmi olarak "
    "kaydedilir.":
        ("If there is an icon image in assets\\olta\\isaret, it is used (most reliable). Otherwise a new shape that "
         "suddenly appears and stays still above the head is searched; if the window opens after Space, that shape "
         "is saved as the icon image.",
         "Liegt ein Symbolbild in assets\\olta\\isaret, wird es verwendet (am zuverlässigsten). Sonst wird über dem "
         "Kopf eine plötzlich erscheinende, stillstehende Form gesucht; öffnet sich nach der Leertaste das Fenster, "
         "wird diese Form als Symbolbild gespeichert."),
    "Pencere testi: zamanlama penceresi ekrandayken bas; kutucuğu ve balığı bulabiliyor mu yazar "
    "(data\\pencere_testi.png). İşaret testi: işaret görünürken bas; resimle bulunuyor mu yazar.":
        ("Window test: press while the timing window is on screen; shows whether the box and fish are found "
         "(data\\pencere_testi.png). Icon test: press while the icon is visible; shows whether the image finds it.",
         "Fenstertest: drücken, während das Timing-Fenster zu sehen ist; zeigt, ob Kästchen und Fisch gefunden "
         "werden (data\\pencere_testi.png). Symboltest: drücken, während das Symbol sichtbar ist."),
    "Olta atma, balık işaretine ve zamanlama penceresine basılan tuş.":
        ("The key used to cast, for the fish icon and for the timing window.",
         "Die Taste zum Auswerfen, für das Fisch-Symbol und für das Timing-Fenster."),
    "Karma: tuşa basarken oyun penceresi bir an öne alınır ve gerçek klavye kullanılır (oyun arka plandaki pencereye "
    "gönderilen tuşu kabul etmiyor). Birden fazla client varsa tuşa basılan anlar sırayla yapılır. Arka plan: "
    "pencereye tuş mesajı gönderilir (oyun destekliyorsa pencere hiç öne gelmez). Ön plan: tek client için gerçek "
    "klavye.":
        ("Hybrid: when pressing, the game window is briefly brought to the front and the real keyboard is used (the "
         "game ignores keys sent to background windows). With several clients the key presses take turns. "
         "Background: a key message is sent to the window (if the game supports it, the window never comes to the "
         "front). Foreground: real keyboard for a single client.",
         "Hybrid: Beim Drücken kommt das Spielfenster kurz nach vorn und die echte Tastatur wird benutzt (das Spiel "
         "ignoriert Tasten an Hintergrundfenster). Bei mehreren Clients wechseln sich die Tastendrücke ab. "
         "Hintergrund: eine Tastennachricht wird an das Fenster gesendet (falls unterstützt, kommt es nie nach vorn). "
         "Vordergrund: echte Tastatur für einen Client."),
    "Karma": ("Hybrid", "Hybrid"),
    "Seçili client'a tuşu bir kez gönderir. Karakterin elinde olta varken bas: olta atıldıysa seçili giriş yöntemi "
    "çalışıyor.":
        ("Sends the key once to the selected client. Press while the character holds the rod: if it casts, the "
         "input method works.",
         "Sendet die Taste einmal an den gewählten Client. Drücken, während der Charakter die Angel hält: wird "
         "ausgeworfen, funktioniert die Eingabemethode."),
    "Ödül çarkı kapandıktan sonra oltayı tekrar atmadan önce rastgele bekleme (insansı).":
        ("Random pause after the reward wheel closes before casting again (human-like).",
         "Zufällige Pause nach dem Schließen des Belohnungsrads vor dem nächsten Wurf (menschlich)."),
    "1200 – 1800 ms": ("1200 – 1800 ms", "1200 – 1800 ms"),
    "Daha insansı ama daha yavaş.": ("More human but slower.", "Menschlicher, aber langsamer."),
    "Daha hızlı.": ("Faster.", "Schneller."),
    "Belirli aralıklarla birkaç dakika hiçbir şey yapmadan bekler (insansı davranış).":
        ("Waits a few minutes at intervals doing nothing (human-like).",
         "Wartet in Abständen einige Minuten ohne Aktion (menschlich)."),
    "İsteğe bağlı": ("Optional", "Optional"),
    "İki mola arasındaki rastgele süre.": ("Random time between two breaks.", "Zufällige Zeit zwischen zwei Pausen."),
    "40 – 70 dk": ("40 – 70 min", "40 – 70 Min."),
    "Bir molanın rastgele uzunluğu.": ("Random length of a break.", "Zufällige Länge einer Pause."),
    "2 – 6 dk": ("2 – 6 min", "2 – 6 Min."),
    "Balık beklerken kafa bölgesine saniyede kaç kez bakılır (sadece o küçük bölge yakalanır). Zamanlama penceresi "
    "ise her zaman olabildiğince hızlı (100+ kare/sn) izlenir.":
        ("How often per second the head area is checked while waiting (only that small area is captured). The "
         "timing window is always watched as fast as possible (100+ fps).",
         "Wie oft pro Sekunde der Kopfbereich beim Warten geprüft wird (nur dieser kleine Bereich wird erfasst). "
         "Das Timing-Fenster wird immer so schnell wie möglich (100+ FPS) beobachtet."),
    "İşaret daha çabuk görülür, işlemci biraz daha çalışır.": ("The icon is seen sooner, slightly more CPU.",
                                                              "Symbol wird schneller erkannt, etwas mehr CPU."),
    "İşlemci rahatlar.": ("Less CPU.", "Weniger CPU."),
    "Türkçe, English, Deutsch. Yeniden başlatınca uygulanır.": ("Türkçe, English, Deutsch. Applies after restart.",
                                                               "Türkçe, English, Deutsch. Gilt nach Neustart."),
    "Panelde canlı izlemenin saniyedeki kare sayısı (en fazla 120). Botun kendisini etkilemez.":
        ("Frames per second of the live view (max. 120). Doesn't affect the bot itself.",
         "Bilder pro Sekunde der Live-Ansicht (max. 120). Beeinflusst den Bot selbst nicht."),
    "Sunucunun captcha'sı (\"Atın üzerine tıklayın\" + 3x3 simge + ~10 sn sayaç) bot beklerken ~0,7 sn'de bir aranır "
    "('Kalan Süre:' yazısının resmiyle, çok hızlı). Görünce balık tutmayı durdurur; 'Otomatik çöz' açıksa ne "
    "istendiğini okur (Windows yazı tanıması ya da başlık resmi) ve o simgeye insan gibi fareyle gidip tıklar. Birden "
    "fazla client varsa captcha'sı çıkan client sıranın başına geçer, oynayan client turunu bırakır. Bilinmeyen bir "
    "simge istenirse sesli uyarır; sen bir kez elle çözünce bot o simgeyi öğrenir.":
        ("The server's captcha (\"Click on the horse\" + 3x3 icons + ~10 s timer) is checked every ~0.7 s while "
         "waiting (very fast, by the 'Kalan Süre:' text image). When seen, fishing stops; with 'Solve automatically' "
         "the bot reads what is asked (Windows text recognition or title image) and clicks that icon like a human. "
         "With several clients, the client with the captcha goes first. If an unknown icon is asked it beeps; after "
         "you solve it once by hand, the bot learns that icon.",
         "Das Captcha des Servers (\"Klicke auf das Pferd\" + 3x3 Symbole + ~10 s Timer) wird beim Warten alle "
         "~0,7 s gesucht (sehr schnell, über das Bild des Textes 'Kalan Süre:'). Wird es gesehen, stoppt das Angeln; "
         "mit 'Automatisch lösen' liest der Bot die Aufgabe (Windows-Texterkennung oder Titelbild) und klickt das "
         "Symbol wie ein Mensch. Bei mehreren Clients kommt der Client mit Captcha zuerst. Bei unbekanntem Symbol "
         "piept er; löst du es einmal von Hand, lernt der Bot das Symbol."),
    "Hepsi açık": ("All on", "Alle an"),
    "Elle çözüm için bekleme": ("Wait for manual solving", "Warten auf manuelles Lösen"),
    "Otomatik çözülemeyen captcha için botun bekleyeceği en uzun süre. Süre dolarsa bot durur.":
        ("The longest the bot waits for a captcha it can't solve. When it runs out, the bot stops.",
         "Wie lange der Bot höchstens auf ein Captcha wartet, das er nicht lösen kann. Danach stoppt er."),
    "10 dk": ("10 min", "10 Min."),
    "Captcha ekrandayken bas: bot ne okuduğunu, neyi seçeceğini ve nereye tıklayacağını yazar (tıklamaz). Seçenekler "
    "resimse: her seçeneğin resmini kırpıp assets\\captcha\\esya klasörüne adıyla kaydet (kalkan.png, kilic.png, "
    "zirh.png…). Aynı şeyin birden fazla resmi olabilir: kalkan_2.png. Captcha penceresinin başlığının resmini "
    "assets\\captcha\\pencere klasörüne koyarsan yazı tanıma olmasa da pencere bulunur.":
        ("Press while a captcha is on screen: shows what the bot reads, what it would choose and where it would "
         "click (it doesn't click). For image options, crop each option and save it in assets\\captcha\\esya under "
         "its name (kalkan.png, kilic.png…). Several images per item are fine: kalkan_2.png.",
         "Drücken, während ein Captcha zu sehen ist: zeigt, was der Bot liest, was er wählen und wohin er klicken "
         "würde (er klickt nicht). Bei Bild-Optionen jede Option ausschneiden und in assets\\captcha\\esya unter "
         "ihrem Namen speichern (kalkan.png, kilic.png…). Mehrere Bilder pro Gegenstand sind möglich."),
    "Client listesinde sadece adı bu metni içeren programlar gösterilir (boş = hepsi).":
        ("Only programs whose name contains this text are listed (empty = all).",
         "Nur Programme, deren Name diesen Text enthält, werden gelistet (leer = alle)."),
    "Boş veya oyunun exe adı": ("Empty or the game's exe name", "Leer oder der EXE-Name des Spiels"),
    "Fare oyun penceresinin üstündeyken bu tuşa basınca o pencere client olarak seçilir.":
        ("Pressing this key while the mouse is over the game window selects that window as a client.",
         "Drückst du diese Taste, während die Maus über dem Spielfenster ist, wird es als Client gewählt."),
    "Daha önce seçtiğin oyun programları; bir sonraki açılışta otomatik listelenir.":
        ("Game programs you selected before; listed automatically next time.",
         "Früher gewählte Spielprogramme; werden beim nächsten Start automatisch gelistet."),
    "Bu programlar asla client olarak listelenmez (tarayıcı, Discord vb.). Virgülle ayır.":
        ("These programs are never listed as clients (browser, Discord, …). Separate with commas.",
         "Diese Programme werden nie als Client gelistet (Browser, Discord, …). Mit Kommas trennen."),
    "Seçili oyun penceresinin programı ve süreç numarası (PID).": ("Program and process ID (PID) of the game window.",
                                                                  "Programm und Prozess-ID (PID) des Spielfensters."),
    "Oyun penceresinin iç alanının boyutu.": ("Size of the game window's client area.",
                                             "Größe des Innenbereichs des Spielfensters."),
    "Oyun penceresinin ekrandaki sol üst köşesi.": ("Top-left corner of the game window on screen.",
                                                   "Obere linke Ecke des Spielfensters auf dem Bildschirm."),
    "Windows ekran ölçeklemesi (%100, %125...). Bot bunu kendisi hesaba katar.":
        ("Windows display scaling (100%, 125%…). The bot takes it into account.",
         "Windows-Anzeigeskalierung (100 %, 125 %…). Der Bot berücksichtigt sie."),
    "Bot bu client'ta ne kadardır çalışıyor.": ("How long the bot has been running on this client.",
                                                "Wie lange der Bot auf diesem Client läuft."),
    "Tuşun oyuna gönderilme şekli (Ayarlar'dan değişir).": ("How the key is sent to the game (change in Settings).",
                                                           "Wie die Taste an das Spiel gesendet wird (in den Einstellungen)."),
    "Botun balık işaretini aradığı yer. 'Seçili' ise sadece senin çerçevelediğin alana bakar; 'otomatik' ise ekranın "
    "ortasındaki (kendi) karakterinin üstüne bakar.":
        ("Where the bot looks for the fish icon. 'Selected': only your framed area; 'automatic': above your character "
         "in the middle of the screen.",
         "Wo der Bot das Fisch-Symbol sucht. 'Gewählt': nur dein markierter Bereich; 'automatisch': über deinem "
         "Charakter in der Bildschirmmitte."),
    "assets\\olta\\isaret klasöründeki balık işareti resimleri ve oyundaki ölçeği (ilk bulunuşta öğrenilir).":
        ("Fish icon images in assets\\olta\\isaret and their in-game scale (learned at first detection).",
         "Fisch-Symbolbilder in assets\\olta\\isaret und ihr Maßstab im Spiel (beim ersten Fund gelernt)."),
    "Space'e basınca balığın durduğu yerin kutucuğun tam ortasına (mor nokta) ortalama uzaklığı.":
        ("Average distance between where the fish stopped and the exact box center (purple dot).",
         "Mittlerer Abstand zwischen der Stoppstelle des Fisches und der genauen Kästchenmitte (violetter Punkt)."),
    "Son turun sonucu ve balığın hedefe uzaklığı.": ("Result of the last round and the fish's distance to the target.",
                                                    "Ergebnis der letzten Runde und Abstand des Fisches zum Ziel."),
    "Bu oturumda bütün client'larda oynanan zamanlama penceresi sayısı.":
        ("Number of timing windows played on all clients this session.",
         "Anzahl der Timing-Fenster auf allen Clients in dieser Sitzung."),
    "Balığın kutucuğun içinde durduğu turlar.": ("Rounds where the fish stopped inside the box.",
                                                 "Runden, in denen der Fisch im Kästchen stoppte."),
    "Balığın kutucuğun dışında durduğu turlar.": ("Rounds where the fish stopped outside the box.",
                                                  "Runden, in denen der Fisch außerhalb des Kästchens stoppte."),
    "İsabetlerin tüm turlara oranı.": ("Hits as a share of all rounds.", "Anteil der Treffer an allen Runden."),
    "Dönen ödül çarkı sayısı.": ("Number of reward wheel spins.", "Anzahl der Belohnungsrad-Drehungen."),
    "Şu anda çalışan bot sayısı (her client için bir bot).": ("Number of bots running now (one per client).",
                                                             "Anzahl laufender Bots (einer pro Client)."),
    "Space'e basıldığı an ile oyunun bunu işlediği an arasındaki süre. Bot balık mor noktaya varmadan bu kadar önce "
    "basar; her turda balığın durduğu yere bakarak düzeltir.":
        ("Time between pressing Space and the game processing it. The bot presses this much before the fish reaches "
         "the purple dot and corrects it every round from where the fish stopped.",
         "Zeit zwischen Drücken der Leertaste und Verarbeitung im Spiel. Der Bot drückt um diese Zeit, bevor der Fisch "
         "den violetten Punkt erreicht, und korrigiert sie jede Runde anhand der Stoppstelle."),
    "İşaret alanımı seç": ("Select my icon area", "Meinen Symbolbereich wählen"),
    "Yanında balık tutan başka oyuncular varsa onların kafasında da işaret çıkar. Kendi karakterinin kafasının "
    "üstünü çerçevele; bot sadece oradaki işarete tepki verir.":
        ("If other players fish next to you, the icon also appears above their heads. Frame the area above your own "
         "head; the bot reacts only to the icon there.",
         "Angeln andere Spieler neben dir, erscheint das Symbol auch über ihren Köpfen. Markiere den Bereich über "
         "deinem Kopf; der Bot reagiert nur auf das Symbol dort."),
    "Tarama penceresi": ("Scan window", "Scan-Fenster"),
    "Botun her adımda gördüğünü ve kararını canlı listeler (işaret, kutucuk, balık hızı, basış anı, sonuç). Kayıtlar "
    "data\\tarama klasörüne de yazılır.":
        ("Lists live what the bot sees and decides at each step (icon, box, fish speed, press time, result). Also "
         "written to data\\tarama.",
         "Zeigt live, was der Bot bei jedem Schritt sieht und entscheidet (Symbol, Kästchen, Fischgeschwindigkeit, "
         "Druckzeitpunkt, Ergebnis). Wird auch in data\\tarama gespeichert."),
    "Anlık kayıt": ("Snapshot", "Schnappschuss"),
    "O anki canlı görüntüyü data\\anlik klasörüne kaydeder.": ("Saves the current live view to data\\anlik.",
                                                              "Speichert die aktuelle Live-Ansicht in data\\anlik."),
    "Ödül çarkı durunca işaretin (▲) gösterdiği eşya ve altındaki adet okunur ve toplanır (ör. 15 Mini balık). "
    "Parantez içinde o eşyanın kaç kez çıktığı yazar. Tüm zamanların toplamı data\\odul_toplam.json dosyasında "
    "tutulur (birkaç yüz bayt); ekran görüntüsü kaydedilmez. Yeni bir eşya çıkarsa resmi "
    "assets\\olta\\odul\\bilinmeyen_N.png olarak kaydedilir; dosyanın adını eşyanın adıyla değiştirmen yeter.":
        ("When the reward wheel stops, the item under the marker (▲) and its count are read and added up (e.g. 15 "
         "Minnow). In brackets: how often the item was won. All-time totals are kept in data\\odul_toplam.json (a few "
         "hundred bytes); no screenshots are saved. A new item is saved as assets\\olta\\odul\\bilinmeyen_N.png; just "
         "rename the file to the item's name.",
         "Stoppt das Belohnungsrad, werden der Gegenstand unter der Markierung (▲) und seine Anzahl gelesen und "
         "summiert (z. B. 15 Elritze). In Klammern: wie oft er gewonnen wurde. Summen aller Zeiten stehen in "
         "data\\odul_toplam.json (wenige hundert Bytes); es werden keine Screenshots gespeichert. Ein neuer "
         "Gegenstand wird als assets\\olta\\odul\\bilinmeyen_N.png gespeichert; benenne die Datei einfach um."),
    "Tüm zamanların ödül toplamlarını sıfırlar.": ("Resets the all-time reward totals.",
                                                  "Setzt die Belohnungssummen aller Zeiten zurück."),
    "<b>Zamanlama penceresi:</b> yeşil çerçeve = kutucuk, <span style='color:#ff28c8'>●</span> kalın mor nokta = hedef "
    "(kutucuğun tam ortası), kırmızı çerçeve = siyah balık, sarı nokta = tuş oyuna ulaştığında balığın olacağı yer, "
    "✕ = balığın durduğu yer.<br><b>Balık beklerken:</b> mavi = arama alanı, mor artı = kendi kafan, yeşil = senin "
    "işaretin, gri = başka oyuncuların işareti (yok sayılır).":
        ("<b>Timing window:</b> green frame = box, <span style='color:#ff28c8'>●</span> thick purple dot = target "
         "(exact box center), red frame = black fish, yellow dot = fish position when the key arrives, ✕ = where the "
         "fish stopped.<br><b>While waiting:</b> blue = search area, purple plus = your head, green = your icon, gray "
         "= other players' icons (ignored).",
         "<b>Timing-Fenster:</b> grüner Rahmen = Kästchen, <span style='color:#ff28c8'>●</span> dicker violetter Punkt "
         "= Ziel (genaue Kästchenmitte), roter Rahmen = schwarzer Fisch, gelber Punkt = Fischposition, wenn die Taste "
         "ankommt, ✕ = Stoppstelle des Fisches.<br><b>Beim Warten:</b> blau = Suchbereich, violettes Plus = dein "
         "Kopf, grün = dein Symbol, grau = Symbole anderer Spieler (ignoriert)."),
    "Önce bir client seçip 'Ekran görüntüsü al'a bas": ("First select a client and press 'Take screenshot'",
                                                       "Wähle zuerst einen Client und drücke 'Screenshot'"),
    # --- tur sonucu
    "ISKA": ("MISS", "DANEBEN"),
    "İSABET": ("HIT", "TREFFER"),
    "ISABET": ("HIT", "TREFFER"),
    "hedefe {e} px": ("{e} px from target", "{e} px vom Ziel"),
    "  hedefe {e} px": ("  {e} px from target", "  {e} px vom Ziel"),
    # --- işaret alanı diyaloğu
    "🎯  Kendi karakterimin işaret alanı": ("🎯  My character's icon area", "🎯  Symbolbereich meines Charakters"),
    "Yanında balık tutan başka oyuncular varsa onların kafasında da işaret çıkar; bot sadece burada seçtiğin alana "
    "bakar.\n1) Oyunda oltayı at. İşaret çıktığında (ya da karakterin göründüğü herhangi bir anda) '📷 Görüntü al'a "
    "bas.\n2) KENDİ karakterinin kafasının üstünü (işaretin çıktığı yeri) fareyle çerçeve içine al. Yandaki "
    "oyuncuların kafaları çerçevenin DIŞINDA kalsın. İşaretin tamamı sığsın.\n3) 'Çizdiğim alanı kaydet'. Mor çerçeve "
    "= kayıtlı alan, mavi = alan seçilmezse botun baktığı yer, yeşil = ekranda bulunan işaretler.":
        ("If other players fish next to you, the icon also appears above their heads; the bot only looks at the area "
         "you select here.\n1) Cast the rod in the game. When the icon appears (or any time your character is "
         "visible) press '📷 Take image'.\n2) Draw a frame around the area above YOUR character's head (where the "
         "icon appears). Keep the other players' heads OUTSIDE the frame. The whole icon must fit.\n3) 'Save drawn "
         "area'. Purple = saved area, blue = where the bot looks without an area, green = icons found on screen.",
         "Angeln andere Spieler neben dir, erscheint das Symbol auch über ihren Köpfen; der Bot schaut nur auf den "
         "hier gewählten Bereich.\n1) Wirf im Spiel die Angel aus. Erscheint das Symbol (oder jederzeit, wenn dein "
         "Charakter zu sehen ist), drücke '📷 Bild aufnehmen'.\n2) Ziehe mit der Maus einen Rahmen um den Bereich "
         "über dem Kopf DEINES Charakters (wo das Symbol erscheint). Die Köpfe anderer Spieler bleiben AUSSERHALB. Das "
         "ganze Symbol muss hineinpassen.\n3) 'Gezeichneten Bereich speichern'. Violett = gespeicherter Bereich, blau "
         "= wo der Bot ohne Bereich sucht, grün = gefundene Symbole."),
    "📷  Görüntü al": ("📷  Take image", "📷  Bild aufnehmen"),
    "✓  Çizdiğim alanı kaydet": ("✓  Save drawn area", "✓  Gezeichneten Bereich speichern"),
    "Alanı sil (otomatik)": ("Delete area (automatic)", "Bereich löschen (automatisch)"),
    "Kapat": ("Close", "Schließen"),
    "Kayıtlı alan yok — bot ekranın ortasındaki karakterin (seninkinin) üstüne bakar ve ortaya en yakın işareti "
    "seçer. Yanında oyuncu varsa alanı seçmen önerilir.":
        ("No saved area — the bot looks above the character in the middle of the screen (yours) and picks the icon "
         "closest to the center. Selecting the area is recommended if players are next to you.",
         "Kein gespeicherter Bereich — der Bot schaut über den Charakter in der Bildschirmmitte (deinen) und wählt "
         "das Symbol, das der Mitte am nächsten ist. Sind Spieler neben dir, wähle den Bereich."),
    "Görüntü alınamadı (oyun penceresi simge durumunda olabilir).": ("Couldn't capture the image (the game window "
                                                                    "may be minimized).",
                                                                    "Bild konnte nicht aufgenommen werden (das "
                                                                    "Spielfenster ist evtl. minimiert)."),
    "Önce görüntüde kendi karakterinin kafasının üstünü fareyle çerçeve içine al.":
        ("First draw a frame around the area above your own character's head.",
         "Ziehe zuerst einen Rahmen um den Bereich über dem Kopf deines Charakters."),
    "Kayıtlı alan: {0}×{1} px (client ortasına göre {2:+d}, {3:+d}). Bot sadece bu alandaki işarete tepki verir.":
        ("Saved area: {0}×{1} px ({2:+d}, {3:+d} from the client center). The bot only reacts to the icon in this "
         "area.",
         "Gespeicherter Bereich: {0}×{1} px ({2:+d}, {3:+d} von der Client-Mitte). Der Bot reagiert nur auf das "
         "Symbol in diesem Bereich."),
    "  •  Ekranda {0} işaret bulundu (yeşil).": ("  •  {0} icon(s) found on screen (green).",
                                                "  •  {0} Symbol(e) auf dem Bildschirm gefunden (grün)."),
    # --- bot günlüğü
    "Bot başlatıldı.": ("Bot started.", "Bot gestartet."),
    "Durdu": ("Stopped", "Gestoppt"),
    "Bot durdu.": ("Bot stopped.", "Bot gestoppt."),
    "Molada": ("On break", "In Pause"),
    "Olta atılıyor": ("Casting", "Wirft aus"),
    "Olta atılıyor…": ("Casting…", "Wirft aus…"),
    "Zamanlama": ("Timing", "Timing"),
    "Balık bekleniyor": ("Waiting for fish", "Warte auf Fisch"),
    "Ödül çarkı dönüyor": ("Reward wheel spinning", "Belohnungsrad dreht sich"),
    "Ödül çarkı bitti, pencere kapandı.": ("Reward wheel done, window closed.", "Belohnungsrad fertig, Fenster geschlossen."),
    "CAPTCHA": ("CAPTCHA", "CAPTCHA"),
    "Captcha'yı lütfen ELLE çöz — bot bekliyor, fareyi bırakır; çözülünce kendiliğinden devam eder.":
        ("Please solve the captcha BY HAND — the bot waits and leaves the mouse free; it continues by itself once "
         "solved.",
         "Bitte löse das Captcha VON HAND — der Bot wartet und lässt die Maus frei; danach macht er von selbst "
         "weiter."),
    "CAPTCHA — elle çözülmesi bekleniyor": ("CAPTCHA — waiting for manual solving", "CAPTCHA — warte auf manuelles Lösen"),
    "Molada captcha penceresi göründü — mola bitirildi.": ("A captcha appeared during the break — break ended.",
                                                          "Während der Pause erschien ein Captcha — Pause beendet."),
    "Zamanlama penceresi bekleniyor": ("Waiting for the timing window", "Warte auf das Timing-Fenster"),
    "balik durmadi": ("fish did not stop", "Fisch stoppte nicht"),
    "ne istendiği okunamadı (Windows OCR kurulu mu? Ayarlar > Captcha testi)":
        ("couldn't read what is asked (is Windows OCR installed? Settings > Captcha test)",
         "Aufgabe nicht lesbar (ist Windows-OCR installiert? Einstellungen > Captcha-Test)"),
    "Hata": ("Error", "Fehler"),
    "Akıllı mola: {0:.1f} dakika dinleniliyor.": ("Smart break: resting {0:.1f} minutes.",
                                                  "Intelligente Pause: {0:.1f} Minuten Ruhe."),
    "Space'e basıldı ama zamanlama penceresi açılmadı (yanlış alarm ya da geç kalındı) — olta yeniden atılacak.":
        ("Space was pressed but the timing window didn't open (false alarm or too late) — casting again.",
         "Leertaste gedrückt, aber das Timing-Fenster öffnete sich nicht (Fehlalarm oder zu spät) — neuer Wurf."),
    "Arka arkaya işaret görülmedi — kafa konumu unutuldu, geniş alanda aranacak.":
        ("No icon seen several times in a row — head position forgotten, searching a wider area.",
         "Mehrmals kein Symbol gesehen — Kopfposition vergessen, suche in größerem Bereich."),
    "✓ Captcha kapandı, bot devam ediyor.": ("✓ Captcha closed, the bot continues.", "✓ Captcha geschlossen, der Bot macht weiter."),
    "Oyun penceresi kapandı, bot durduruluyor.": ("The game window closed, stopping the bot.",
                                                 "Das Spielfenster wurde geschlossen, Bot wird gestoppt."),
    "Balık işareti göründü ({0}) — Space'e basıldı.": ("Fish icon appeared ({0}) — Space pressed.",
                                                       "Fisch-Symbol erschienen ({0}) — Leertaste gedrückt."),
    "secili alan": ("selected area", "gewaehlter Bereich"),
    "otomatik alan": ("automatic area", "automatischer Bereich"),
    "{0:.0f} sn içinde balık işareti görülmedi — olta yeniden atılacak. (İşaret hiç görülmüyorsa: Ayarlar > Yeni balık "
    "sistemi > İşaret testi)":
        ("No fish icon within {0:.0f} s — casting again. (If the icon is never seen: Settings > Fishing system > Icon "
         "test)",
         "Kein Fisch-Symbol innerhalb von {0:.0f} s — neuer Wurf. (Wird das Symbol nie gesehen: Einstellungen > "
         "Angelsystem > Symboltest)"),
    "✓ İsabet — {0}": ("✓ Hit — {0}", "✓ Treffer — {0}"),
    "✗ Iska — {0}": ("✗ Miss — {0}", "✗ Daneben — {0}"),
    "⚠ CAPTCHA algılandı: “{0}”": ("⚠ CAPTCHA detected: “{0}”", "⚠ CAPTCHA erkannt: „{0}“"),
    "✓ Captcha çözüldü, bot devam ediyor.": ("✓ Captcha solved, the bot continues.", "✓ Captcha gelöst, der Bot macht weiter."),
    "Captcha otomatik çözülemedi: {0}.": ("Captcha couldn't be solved automatically: {0}.",
                                         "Captcha konnte nicht automatisch gelöst werden: {0}."),
    "VIP üyelik doğrulanamadı, bot durduruluyor.": ("VIP membership couldn't be verified, stopping the bot.",
                                                   "VIP-Mitgliedschaft nicht bestätigt, Bot wird gestoppt."),
    "✓ Balık işareti öğrenildi ({0}) — sonraki turlarda resimle aranacak.":
        ("✓ Fish icon learned ({0}) — will be searched by image from now on.",
         "✓ Fisch-Symbol gelernt ({0}) — wird ab jetzt per Bild gesucht."),
    "Zamanlama penceresi açık (işaret görülmeden) — oynanıyor.": ("Timing window is open (no icon seen) — playing.",
                                                                  "Timing-Fenster offen (ohne Symbol) — spiele."),
    "🎁 Ödül: {n} × {name}": ("🎁 Reward: {n} × {name}", "🎁 Belohnung: {n} × {name}"),
    "Captcha: {0} seçiliyor (deneme {1}).": ("Captcha: choosing {0} (try {1}).", "Captcha: wähle {0} (Versuch {1})."),
    "“{0}” simgesi henüz kayıtlı değil — bir kez ELLE çözersen bot o simgeyi öğrenir (ya da "
    "assets\\captcha\\esya\\{1}.png olarak ekle)":
        ("the “{0}” icon isn't saved yet — solve it BY HAND once and the bot learns it (or add "
         "assets\\captcha\\esya\\{1}.png)",
         "das Symbol „{0}“ ist noch nicht gespeichert — löse es einmal VON HAND, dann lernt es der Bot (oder füge "
         "assets\\captcha\\esya\\{1}.png hinzu)"),
    "“{0}” simgesi ekranda bulunamadı": ("the “{0}” icon wasn't found on screen", "das Symbol „{0}“ wurde nicht gefunden"),
    "Captcha {0:.0f} dakikadır çözülmedi — bot durduruluyor.": ("Captcha unsolved for {0:.0f} minutes — stopping the bot.",
                                                               "Captcha seit {0:.0f} Minuten ungelöst — Bot wird gestoppt."),
    "isaret resmi yok: degisimle": ("no icon image: by change", "kein Symbolbild: per Aenderung"),
    "BASILDI": ("PRESSED", "GEDRUECKT"),
    "DURDU: hedefe {d} px": ("STOPPED: {d} px from target", "GESTOPPT: {d} px vom Ziel"),
    " (yeni eşya resmi kaydedildi: assets\\olta\\odul\\{f}.png — adını değiştirebilirsin)":
        (" (new item image saved: assets\\olta\\odul\\{f}.png — you can rename it)",
         " (neues Gegenstandsbild gespeichert: assets\\olta\\odul\\{f}.png — du kannst es umbenennen)"),
    "balik bekleniyor {s} sn": ("waiting for fish {s} s", "warte auf Fisch {s} s"),
    "{n} isaret resmi": ("{n} icon image(s)", "{n} Symbolbild(er)"),
    "✓ “{0}” simgesi öğrenildi ({1}) — bir dahakine bot kendisi çözer.":
        ("✓ “{0}” icon learned ({1}) — next time the bot solves it itself.",
         "✓ Symbol „{0}“ gelernt ({1}) — nächstes Mal löst der Bot es selbst."),
    # --- canlı görüntü (OpenCV: sadece ASCII)
    "gecikme payi {ms} ms": ("key delay {ms} ms", "Verzoegerung {ms} ms"),
    "BENIM ISARETIM": ("MY ICON", "MEIN SYMBOL"),
    "pencere yok": ("no window", "kein Fenster"),
    "balik hedefe {d} px": ("fish to target {d} px", "Fisch zum Ziel {d} px"),
    "balik": ("fish", "Fisch"),
    "baskasi": ("other", "fremd"),
    "kutucuk sabitleniyor": ("locking the box", "Kaestchen wird fixiert"),
    "izleniyor": ("watching", "beobachte"),
    "hiz olculuyor": ("measuring speed", "messe Tempo"),
    "balik henuz hareket etmiyor": ("fish not moving yet", "Fisch bewegt sich noch nicht"),
    "balik ortadan uzaklasiyor": ("fish moving away from center", "Fisch entfernt sich von der Mitte"),
    "bekleniyor": ("waiting", "warte"),
    "Önerilen:": ("Recommended:", "Empfohlen:"),
    # --- seri sayacı
    "⚠ Seri sayacına göre önceki tur aslında: {0}": ("⚠ According to the streak counter the previous round was: {0}",
                                                    "⚠ Laut Serienzähler war die vorige Runde: {0}"),
    "⚠ Seri sayacına göre bu tur aslında: {0}": ("⚠ According to the streak counter this round was: {0}",
                                                "⚠ Laut Serienzähler war diese Runde: {0}"),
    " (kutucuk yanlış okunmuş olabilir)": (" (the box may have been misread)", " (Kästchen evtl. falsch erkannt)"),
    "Seri sayacı hiç değişmiyor — bu client'ta seri kontrolü kapatıldı, botun kendi ölçümü kullanılıyor.":
        ("The streak counter never changes — streak check disabled for this client, using the bot's own measurement.",
         "Der Serienzähler ändert sich nie — Serienprüfung für diesen Client aus, der Bot nutzt seine eigene Messung."),
    "lacivert çerçeveden": ("from the navy frame", "über den dunkelblauen Rahmen"),
    "renkten — yedek yöntem": ("by color — fallback", "über die Farbe — Reserve"),
    "seri sayısı okundu": ("streak number read", "Serienzahl gelesen"),
    "SERİ SAYISI OKUNAMADI": ("STREAK NUMBER NOT READ", "SERIENZAHL NICHT GELESEN"),
    "seri sayacına göre düzeltildi": ("corrected by the streak counter", "per Serienzähler korrigiert"),
    # --- yeni tasarım
    'Aktif üyelik': ('Active membership', 'Aktive Mitgliedschaft'),
    'Üyelik sona erdi': ('Membership expired', 'Mitgliedschaft abgelaufen'),
    'Atılan olta': ('Casts', 'Würfe'),
    'Balık otomasyonu': ('Fishing automation', 'Angel-Automatisierung'),
    'Basılamadan kapanan pencere': ('Window closed before pressing', 'Fenster vor dem Drücken geschlossen'),
    'Bitiş': ('Expires', 'Ablauf'),
    'Büyüt': ('Expand', 'Vergrößern'),
    'FishBot • Giriş': ('FishBot • Sign in', 'FishBot • Anmeldung'),
    'Gizle': ('Hide', 'Verbergen'),
    'Göster': ('Show', 'Zeigen'),
    'HOŞ GELDİN': ('WELCOME', 'WILLKOMMEN'),
    'Hesabına giriş yap': ('Sign in to your account', 'Bei deinem Konto anmelden'),
    'KALAN SÜRE': ('TIME LEFT', 'RESTZEIT'),
    'Klasör': ('Folder', 'Ordner'),
    'Kullanıcı adınız': ('Your username', 'Dein Benutzername'),
    'Kutucuğu ve balığı canlı izler': ('Tracks the box and the fish live', 'Verfolgt Kästchen und Fisch live'),
    'MENÜ': ('MENU', 'MENÜ'),
    'Oynanan tur': ('Rounds played', 'Gespielte Runden'),
    'Saatte tur': ('Rounds per hour', 'Runden pro Stunde'),
    'Seri sayacına göre düzeltilen': ('Corrected by streak counter', 'Per Serienzähler korrigiert'),
    'Seri sayacıyla doğrulanan': ('Verified by streak counter', 'Per Serienzähler bestätigt'),
    'Süresi doldu': ('Expired', 'Abgelaufen'),
    'Süresiz': ('Unlimited', 'Unbegrenzt'),
    'Tarama': ('Scan', 'Scan'),
    'düzeltilen {n}': ('{n} corrected', '{n} korrigiert'),
    'her turda öğrenilir': ('learned every round', 'jede Runde gelernt'),
    'sabit': ('fixed', 'fest'),
    'hız {v} px/sn': ('speed {v} px/s', 'Tempo {v} px/s'),
    'işaret gelmedi {n}': ('no icon {n}', 'kein Symbol {n}'),
    'ortalama {v} px': ('average {v} px', 'Mittel {v} px'),
    'seriyle doğrulanan {n}': ('{n} verified by streak', '{n} per Serie bestätigt'),
    'son {0}: {1} isabet': ('last {0}: {1} hits', 'letzte {0}: {1} Treffer'),
    '{0} client  ·  {1} çalışıyor': ('{0} clients  ·  {1} running', '{0} Clients  ·  {1} laufen'),
    '{d} gün {h} saat': ('{d} days {h} h', '{d} Tage {h} Std.'),
    '{h} saat {m} dk': ('{h} h {m} min', '{h} Std. {m} Min.'),
    '{n} client': ('{n} clients', '{n} Clients'),
    '{n} client içinden': ('of {n} clients', 'von {n} Clients'),
    'Çalışıyor  ·  {n} bot': ('Running  ·  {n} bots', 'Läuft  ·  {n} Bots'),
    "Birden fazla client'ı aynı anda yönetir": ('Runs several clients at once', 'Steuert mehrere Clients gleichzeitig'),
    "Botun gerçekten saydığı değerler. 'Seri sayacıyla doğrulanan': sonucu oyunun Seri sayısıyla kontrol edilen tur sayısı. 'Düzeltilen': botun ölçümü Seri sayısıyla çeliştiği için düzeltilen tur. 'Saatte tur': çalışma süresine göre.": ("Values the bot actually counted. 'Verified by streak counter': rounds checked against the game's streak number. 'Corrected': rounds where the bot's measurement contradicted the streak number. 'Rounds per hour': based on uptime.", "Vom Bot tatsächlich gezählte Werte. 'Per Serienzähler bestätigt': Runden, die mit der Serienzahl des Spiels geprüft wurden. 'Korrigiert': Runden, bei denen die Messung des Bots der Serienzahl widersprach. 'Runden pro Stunde': nach Laufzeit."),
    "Botun her adımda gördüğünü ve kararını canlı listeler (işaret, kutucuk, balık hızı, basış anı, sonuç, seri sayacı). 'Büyüt' ayrı bir pencerede açar. Kayıtlar data\\tarama klasörüne de yazılır.": ("Lists live what the bot sees and decides at each step (icon, box, fish speed, press time, result, streak counter). 'Expand' opens it in a separate window. Also written to data\\tarama.", "Zeigt live, was der Bot bei jedem Schritt sieht und entscheidet (Symbol, Kästchen, Fischtempo, Druckzeitpunkt, Ergebnis, Serienzähler). 'Vergrößern' öffnet ein eigenes Fenster. Wird auch in data\\tarama gespeichert."),
    'Bu oturumda atılan olta sayısı; altında işaret hiç gelmeyen atış sayısı.': ('Casts this session; below: casts where no icon appeared.', 'Würfe in dieser Sitzung; darunter: Würfe ohne Symbol.'),
    'Devam etmek için kullanıcı adını ve şifreni gir.': ('Enter your username and password to continue.', 'Gib Benutzername und Passwort ein, um fortzufahren.'),
    'Henüz hiç üye yok. Bot klasöründeki uye_ekle.bat ile bir üye oluştur.': ('No members yet. Create one with uye_ekle.bat in the bot folder.', 'Noch keine Mitglieder. Lege eins mit uye_ekle.bat im Bot-Ordner an.'),
    'Hesabın yoksa yöneticiden üyelik iste.': ('No account? Ask the administrator for a membership.', 'Kein Konto? Bitte den Administrator um eine Mitgliedschaft.'),
    'Hoş geldin {0}. Üyelik bitişi: {1:%d.%m.%Y %H:%M}': ('Welcome {0}. Membership until: {1:%d.%m.%Y %H:%M}', 'Willkommen {0}. Mitgliedschaft bis: {1:%d.%m.%Y %H:%M}'),
    'Metin2 için akıllı balık tutma asistanı': ('Smart fishing assistant for Metin2', 'Intelligenter Angel-Assistent für Metin2'),
    'Sonucu oyunun seri sayacıyla doğrular': ("Verifies results with the game's streak counter", 'Prüft Ergebnisse mit dem Serienzähler des Spiels'),
    'Tarama kaydını ayrı, büyük bir pencerede aç': ('Open the scan log in a separate, large window', 'Scan-Protokoll in einem großen Fenster öffnen'),
    'Tuş gecikmesini her turda kendisi öğrenir': ('Learns the key delay every round', 'Lernt die Tastenverzögerung jede Runde'),
    'Üyelik doğrulanamadı, bot durduruluyor.': ("Membership couldn't be verified, stopping the bot.", 'Mitgliedschaft nicht bestätigt, Bot wird gestoppt.'),
    'Üyeliğinin süresi doldu. Botlar durduruldu.': ('Your membership has expired. Bots stopped.', 'Deine Mitgliedschaft ist abgelaufen. Bots gestoppt.'),
    'Üyeliğinizin süresi dolmuş.': ('Your membership has expired.', 'Deine Mitgliedschaft ist abgelaufen.'),
    'Kullanıcı adı ve şifre gerekli.': ('Username and password are required.', 'Benutzername und Passwort erforderlich.'),
    'Kullanıcı adı veya şifre hatalı.': ('Wrong username or password.', 'Falscher Benutzername oder falsches Passwort.'),
    'Hesabınız askıya alınmış.': ('Your account is suspended.', 'Dein Konto ist gesperrt.'),
    "<span style='color:{0}'>{1}</span>&nbsp; client seç&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{0}'>{2}</span>&nbsp; hepsini durdur": ("<span style='color:{0}'>{1}</span>&nbsp; pick client&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{0}'>{2}</span>&nbsp; stop all", "<span style='color:{0}'>{1}</span>&nbsp; Client wählen&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{0}'>{2}</span>&nbsp; alle stoppen"),
    "<span style='color:{0}'><b>{1}</b></span> fare oyun penceresindeyken client seç&nbsp;&nbsp;·&nbsp;&nbsp;<b>İşaret alanımı seç</b> (yanında balık tutan oyuncu varsa)&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{2}'><b>{3}</b></span> tüm botları durdur": ("<span style='color:{0}'><b>{1}</b></span> pick the client under the mouse&nbsp;&nbsp;·&nbsp;&nbsp;<b>Select my icon area</b> (if players fish next to you)&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{2}'><b>{3}</b></span> stop all bots", "<span style='color:{0}'><b>{1}</b></span> Client unter der Maus wählen&nbsp;&nbsp;·&nbsp;&nbsp;<b>Meinen Symbolbereich wählen</b> (wenn Spieler neben dir angeln)&nbsp;&nbsp;·&nbsp;&nbsp;<span style='color:{2}'><b>{3}</b></span> alle Bots stoppen"),
    # --- captcha / üyeler / güncelleme
    ' • ölçülen gecikme {0} ms → {1} ms': (' • measured delay {0} ms → {1} ms', ' • gemessene Verzögerung {0} ms → {1} ms'),
    '+  Yeni üye': ('+  New member', '+  Neues Mitglied'),
    ', balık hızı {0} px/sn': (', fish speed {0} px/s', ', Fischtempo {0} px/s'),
    '7 gün içinde bitecek': ('Expiring within 7 days', 'Läuft in 7 Tagen ab'),
    'Aktif': ('Active', 'Aktiv'),
    'Aktif (kapalıysa giriş yapamaz)': ('Active (cannot log in if off)', 'Aktiv (ohne kein Login)'),
    'Ara: kullanıcı adı ya da not': ('Search: username or note', 'Suche: Benutzername oder Notiz'),
    'Askıda': ('Suspended', 'Gesperrt'),
    'Atla': ('Skip', 'Überspringen'),
    'Balık sistemi, işaret alanı, tuş ve client ayarları — hepsi açıklamalı.': ('Fishing system, icon area, key and client settings — all explained.', 'Angelsystem, Symbolbereich, Taste und Client-Einstellungen — alle erklärt.'),
    'Başlatılıyor…': ('Starting…', 'Startet…'),
    'Bir kayıt seç': ('Select an entry', 'Eintrag wählen'),
    'Bot birazdan yeniden açılacak.': ('The bot will reopen in a moment.', 'Der Bot startet gleich neu.'),
    'Bot bu resimlerle doğru simgeyi bulur. Dosya adı = simgenin adı (kalkan, kilic, at…). Bilinmeyen bir simge istenirse bir kez elle çözmen yeter: bot onu buraya ekler.': ('The bot finds the right icon with these images. File name = icon name (kalkan, kilic, at…). If an unknown icon is asked, solve it once by hand: the bot adds it here.', 'Der Bot findet mit diesen Bildern das richtige Symbol. Dateiname = Symbolname (kalkan, kilic, at…). Wird ein unbekanntes Symbol verlangt, löse es einmal von Hand: der Bot fügt es hier hinzu.'),
    'Bot güncelleniyor…': ('Updating the bot…', 'Bot wird aktualisiert…'),
    'Bu üye zaten süresiz.': ('This member is already unlimited.', 'Dieses Mitglied ist bereits unbegrenzt.'),
    'Captcha ayarları, test, öğrenilen simgeler ve yakalanan captcha resimleri.': ('Captcha settings, test, learned icons and captured captcha images.', 'Captcha-Einstellungen, Test, gelernte Symbole und erfasste Captcha-Bilder.'),
    'Captcha bulundu: “{0}” → istenen: {1}.': ('Captcha found: “{0}” → asked: {1}.', 'Captcha gefunden: „{0}“ → verlangt: {1}.'),
    'Captcha ekrandayken "Captcha testi"ne bas: bot ne okuduğunu ve nereye tıklayacağını gösterir (tıklamaz). Önce Client\'lar sayfasında bir client seç.': ('Press "Captcha test" while a captcha is on screen: shows what the bot reads and where it would click (it doesn\'t click). Select a client on the Clients page first.', 'Drücke "Captcha-Test", während ein Captcha zu sehen ist: zeigt, was der Bot liest und wohin er klicken würde (er klickt nicht). Wähle zuerst auf der Seite Clients einen Client.'),
    'Captcha olayları': ('Captcha events', 'Captcha-Ereignisse'),
    "Captcha'yı denetle": ('Watch for captchas', 'Auf Captchas achten'),
    'Cihaz kilidi': ('Device lock', 'Gerätesperre'),
    'Dil değişti. Arayüzün tamamının yeni dilde görünmesi için program yeniden açılsın mı?': ('The language changed. Restart the program so the whole interface uses the new language?', 'Die Sprache wurde geändert. Programm neu starten, damit die ganze Oberfläche die neue Sprache nutzt?'),
    'Durum': ('Status', 'Status'),
    'Elle çözülen': ('Solved by hand', 'Von Hand gelöst'),
    'En fazla client': ('Max. clients', 'Max. Clients'),
    'Giriş kayıtları': ('Login log', 'Anmeldeprotokoll'),
    'Görülen': ('Seen', 'Gesehen'),
    'Güncelleme kuruluyor…': ('Installing update…', 'Update wird installiert…'),
    'Güncelleme yapılamadı': ('Update failed', 'Update fehlgeschlagen'),
    'Güncellemeler denetleniyor…': ('Checking for updates…', 'Suche nach Updates…'),
    'Hoş geldin {0}. Üyelik bitişi: {1}': ('Welcome {0}. Membership until: {1}', 'Willkommen {0}. Mitgliedschaft bis: {1}'),
    "Kaynak koddan çalışıyor — güncellemeyi GitHub'dan indir.": ('Running from source — download the update from GitHub.', 'Läuft aus dem Quellcode — Update von GitHub laden.'),
    'Kayıt yok (yerel üyelikte giriş kaydı tutulmaz).': ('No entries (local membership keeps no login log).', 'Keine Einträge (lokale Mitgliedschaft führt kein Anmeldeprotokoll).'),
    'Kullanıcı adı boş olamaz.': ("Username can't be empty.", 'Benutzername darf nicht leer sein.'),
    'Not': ('Note', 'Notiz'),
    'Oluştur': ('Generate', 'Erzeugen'),
    'Otomatik çözülemeyen': ('Not solved automatically', 'Nicht automatisch gelöst'),
    'Otomatik çözülen': ('Solved automatically', 'Automatisch gelöst'),
    'Sadece ilk giriş yaptığı bilgisayarda çalışsın': ('Only works on the first computer it logs in from', 'Nur auf dem ersten Anmelde-PC nutzbar'),
    'Saklanacak captcha resmi': ('Captcha images to keep', 'Zu behaltende Captcha-Bilder'),
    'Seri kontrolü': ('Streak check', 'Serienprüfung'),
    'Simgenin adı (ör. kalkan, at):': ('Icon name (e.g. kalkan, at):', 'Symbolname (z. B. kalkan, at):'),
    'Sonucu oyunun Seri sayacıyla doğrula ve gerekirse düzelt': ("Verify the result with the game's streak counter and correct it if needed", 'Ergebnis mit dem Serienzähler prüfen und ggf. korrigieren'),
    "Space'e basılamadan pencere kapandı": ('Window closed before Space was pressed', 'Fenster schloss vor dem Drücken der Leertaste'),
    'Sunucu "Atın üzerine tıklayın" gibi bir doğrulama penceresi açınca bot balık tutmayı durdurur, ne istendiğini okur ve doğru simgeye tıklar. Çözemezse sesli uyarır ve sen çözene kadar bekler; elle çözdüğün simgeyi öğrenir.': ('When the server opens a check window like "Click on the horse", the bot stops fishing, reads what is asked and clicks the right icon. If it can\'t, it beeps and waits until you solve it; it learns the icon you solve by hand.', 'Öffnet der Server ein Prüffenster wie "Klicke auf das Pferd", hört der Bot auf zu angeln, liest die Aufgabe und klickt das richtige Symbol. Schafft er es nicht, piept er und wartet, bis du es löst; das von Hand gelöste Symbol lernt er.'),
    'Sunucuyla konuşuluyor…': ('Talking to the server…', 'Verbindung zum Server…'),
    'Supabase': ('Supabase', 'Supabase'),
    'Süresi dolmuş / askıda': ('Expired / suspended', 'Abgelaufen / gesperrt'),
    'Süresiz üyelik': ('Unlimited membership', 'Unbegrenzte Mitgliedschaft'),
    'Sürüm {a} → {b}': ('Version {a} → {b}', 'Version {a} → {b}'),
    'Sürüm {v}': ('Version {v}', 'Version {v}'),
    'Sınırsız': ('Unlimited', 'Unbegrenzt'),
    'Test görüntüsü burada görünür': ('The test image appears here', 'Das Testbild erscheint hier'),
    'Toplam üye': ('Total members', 'Mitglieder gesamt'),
    'Tıklanacak yer BULUNAMADI — bir kez elle çöz, bot simgeyi öğrensin.': ('Click target NOT FOUND — solve it once by hand so the bot learns the icon.', 'Klickziel NICHT GEFUNDEN — einmal von Hand lösen, damit der Bot das Symbol lernt.'),
    'Tıklanacak: {0} (x={1}, y={2}).': ('Would click: {0} (x={1}, y={2}).', 'Würde klicken: {0} (x={1}, y={2}).'),
    'Yakalanan bütün captcha resimleri silinsin mi?': ('Delete all captured captcha images?', 'Alle erfassten Captcha-Bilder löschen?'),
    "Yakalanan captcha'lar": ('Captured captchas', 'Erfasste Captchas'),
    'Yeni sürüm var: {v}': ('New version available: {v}', 'Neue Version verfügbar: {v}'),
    'Yeni üye': ('New member', 'Neues Mitglied'),
    'Yeni üye için şifre gerekli.': ('A password is required for a new member.', 'Für ein neues Mitglied ist ein Passwort nötig.'),
    'Yeniden adlandır': ('Rename', 'Umbenennen'),
    'Yönetici (Üyeler sayfasını görür)': ('Administrator (sees the Members page)', 'Administrator (sieht die Mitgliederseite)'),
    'balık izlenemedi': ('fish could not be tracked', 'Fisch nicht verfolgbar'),
    "balık x={0}'da durdu": ('fish stopped at x={0}', 'Fisch stoppte bei x={0}'),
    'resimle': ('by image', 'per Bild'),
    'değişimle': ('by change', 'per Änderung'),
    'değiştirmek için yaz': ('type to change', 'zum Ändern eingeben'),
    'zorunlu': ('required', 'erforderlich'),
    'ekran görüntüsü: {0}': ('screenshot: {0}', 'Screenshot: {0}'),
    'gün': ('days', 'Tage'),
    'henüz belli değil (botun ölçümü geçerli)': ("not known yet (bot's measurement stands)", 'noch unbekannt (Messung des Bots gilt)'),
    'işaret {0} {1} kutu {2}': ('icon {0} {1} box {2}', 'Symbol {0} {1} Box {2}'),
    'kutucuk görülemedi': ('box not seen', 'Kästchen nicht gesehen'),
    'okundu': ('read', 'gelesen'),
    'okunamadı': ('not read', 'nicht gelesen'),
    'isabet': ('hit', 'Treffer'),
    'ıska': ('miss', 'daneben'),
    'seri sayacı: başta {0}, sonda {1} → {2}': ('streak counter: start {0}, end {1} → {2}', 'Serienzähler: Anfang {0}, Ende {1} → {2}'),
    'tahmini (balık durmadı)': ("estimated (fish didn't stop)", 'geschätzt (Fisch stoppte nicht)'),
    'yerel dosya (data/users.json)': ('local file (data/users.json)', 'lokale Datei (data/users.json)'),
    'zamanlama: kutu {0}-{1} ({2}{3})  balık x={4} hız {5} px/sn  → {6} ms sonra basıldı (gecikme payı {7} ms, {8} örnek)': ('timing: box {0}-{1} ({2}{3})  fish x={4} speed {5} px/s  → pressed after {6} ms (delay {7} ms, {8} samples)', 'Timing: Kästchen {0}-{1} ({2}{3})  Fisch x={4} Tempo {5} px/s  → nach {6} ms gedrückt (Verzögerung {7} ms, {8} Proben)'),
    '{0}, merkeze {1} px (kutucuk yarısı {2} px{3})': ('{0}, {1} px from center (half box {2} px{3})', '{0}, {1} px von der Mitte (halbes Kästchen {2} px{3})'),
    '{n} kayıt': ('{n} entries', '{n} Einträge'),
    '{n} kez yer değiştirdi': ('moved {n}×', '{n}× verschoben'),
    '{n} simge': ('{n} icons', '{n} Symbole'),
    '{n} üye  ·  kaynak: {src}': ('{n} members  ·  source: {src}', '{n} Mitglieder  ·  Quelle: {src}'),
    'Çalışan {n} bot durdurulacak.': ('{n} running bots will be stopped.', '{n} laufende Bots werden gestoppt.'),
    'Önce listeden bir üye seç.': ('Select a member from the list first.', 'Wähle zuerst ein Mitglied aus der Liste.'),
    'Öğrenilen simgeler': ('Learned icons', 'Gelernte Symbole'),
    'Üye ekle, süre ver (süresiz dahil), askıya al, cihaz kilidi, sil.': ('Add members, give time (incl. unlimited), suspend, device lock, delete.', 'Mitglieder anlegen, Zeit geben (auch unbegrenzt), sperren, Gerätesperre, löschen.'),
    'Üye listesi': ('Member list', 'Mitgliederliste'),
    'Üyeler': ('Members', 'Mitglieder'),
    'Üyelik': ('Membership', 'Mitgliedschaft'),
    "Üyeliğin aynı anda en fazla {n} client'a izin veriyor.": ('Your membership allows at most {n} clients at once.', 'Deine Mitgliedschaft erlaubt höchstens {n} Clients gleichzeitig.'),
    'Üyeyi düzenle': ('Edit member', 'Mitglied bearbeiten'),
    'ödül okunamadı': ('reward not read', 'Belohnung nicht gelesen'),
    'ödül çarkı: {0} × {1} (benzerlik {2})': ('reward wheel: {0} × {1} (similarity {2})', 'Belohnungsrad: {0} × {1} (Ähnlichkeit {2})'),
    'ödül: {0} × {1} (benzerlik {2})': ('reward: {0} × {1} (similarity {2})', 'Belohnung: {0} × {1} (Ähnlichkeit {2})'),
    '“{0}” simgesi silinsin mi?': ('Delete the “{0}” icon?', 'Symbol „{0}“ löschen?'),
    '“{0}” üyesi kalıcı olarak silinsin mi?': ('Permanently delete member “{0}”?', 'Mitglied „{0}“ endgültig löschen?'),
    '✓ Güncellendi ({0}).': ('✓ Updated ({0}).', '✓ Aktualisiert ({0}).'),
    '✓ Kaydedildi ({0}).': ('✓ Saved ({0}).', '✓ Gespeichert ({0}).'),
    'Çalışıyor': ('Running', 'Läuft'),
    'Klasörü aç': ('Open folder', 'Ordner öffnen'),
    'Tümünü sil': ('Delete all', 'Alle löschen'),
    'Yenile': ('Refresh', 'Aktualisieren'),
    'Sil': ('Delete', 'Löschen'),
    'Kullanıcı': ('User', 'Benutzer'),
    'Kalan süre': ('Time left', 'Restzeit'),
    'Son giriş': ('Last login', 'Letzter Login'),
    'Client': ('Clients', 'Clients'),
    'Cihaz': ('Device', 'Gerät'),
    'Düzenle': ('Edit', 'Bearbeiten'),
    '+30 gün': ('+30 days', '+30 Tage'),
    'Süresiz yap': ('Make unlimited', 'Unbegrenzt machen'),
    'Askıya al / Aç': ('Suspend / Enable', 'Sperren / Freigeben'),
    'Cihaz kilidini sıfırla': ('Reset device lock', 'Gerätesperre zurücksetzen'),
    'kilitli': ('locked', 'gesperrt'),
    'serbest': ('free', 'frei'),
    'Beklenmeyen bir hata oluştu. Ayrıntı data\\hata.log dosyasına yazıldı.': ('An unexpected error occurred. Details were written to data\\hata.log.', 'Ein unerwarteter Fehler ist aufgetreten. Details stehen in data\\hata.log.'),
    'Çok fazla hatalı deneme. 10 dakika sonra tekrar dene.': ('Too many failed attempts. Try again in 10 minutes.', 'Zu viele Fehlversuche. In 10 Minuten erneut versuchen.'),
    'Bu hesap başka bir bilgisayara kilitli.': ('This account is locked to another computer.', 'Dieses Konto ist an einen anderen PC gebunden.'),
    'Bu işlem için yönetici yetkisi gerekli.': ('Administrator rights are required for this.', 'Dafür sind Administratorrechte nötig.'),
    'Bu kullanıcı adı zaten var.': ('This username already exists.', 'Dieser Benutzername existiert bereits.'),
    'Kendi hesabını silemezsin.': ("You can't delete your own account.", 'Du kannst dein eigenes Konto nicht löschen.'),
    'Kendi yönetici yetkini ya da hesabını kapatamazsın.': ("You can't remove your own admin rights or disable your account.", 'Du kannst deine eigenen Adminrechte oder dein Konto nicht deaktivieren.'),
    'Oturum bulunamadı.': ('Session not found.', 'Sitzung nicht gefunden.'),
    'Üye bulunamadı.': ('Member not found.', 'Mitglied nicht gefunden.'),
    "Zamanlama penceresindeki 'Seri' sayısı isabette artar, ıskada sıfırlanır. Açıksa bot kendi ölçümünü bu sayıyla karşılaştırır ve çelişirse turu düzeltir. Sayı birkaç turdur hiç değişmiyorsa kontrol kendiliğinden kapanır.": ("The 'Streak' number in the timing window rises on a hit and resets on a miss. If on, the bot compares its own measurement with it and corrects the round if they disagree. If the number doesn't change for several rounds, the check turns itself off.", 'Die Serienzahl im Timing-Fenster steigt bei einem Treffer und fällt bei einem Fehlschlag auf 0. Ist dies an, vergleicht der Bot seine Messung damit und korrigiert die Runde bei Widerspruch. Ändert sich die Zahl mehrere Runden nicht, schaltet sich die Prüfung ab.'),
    'Yakalanan captcha ekran görüntülerinden en yenileri tutulur, eskileri silinir (disk dolmasın).': ("The newest captured captcha screenshots are kept, older ones are deleted (so the disk doesn't fill up).", 'Die neuesten erfassten Captcha-Screenshots werden behalten, ältere gelöscht (damit die Platte nicht vollläuft).'),
    'Bir üye seç': ('Select a member', 'Mitglied wählen'),
    'Bu bilgileri üyeye gönder': ('Send these details to the member', 'Diese Daten an das Mitglied senden'),
    'Giriş bilgileri': ('Login details', 'Anmeldedaten'),
    'Kopyala': ('Copy', 'Kopieren'),
    'Yönetici': ('Administrator', 'Administrator'),
    'Üye': ('Member', 'Mitglied'),
    'çevrimdışı': ('offline', 'offline'),
    '● çevrimiçi': ('● online', '● online'),
    'Şifre değiştir': ('Change password', 'Passwort ändern'),
    'Şifre güvenlik için şifrelenmiş saklanır; bu pencere kapanınca bir daha gösterilemez. Unutulursa yeni şifre verilir.': ("For security the password is stored encrypted; it can't be shown again after this window closes. If forgotten, set a new one.", 'Aus Sicherheitsgründen wird das Passwort verschlüsselt gespeichert; nach dem Schließen dieses Fensters kann es nicht mehr angezeigt werden. Bei Verlust ein neues vergeben.'),
    '“{0}” için yeni şifre:': ('New password for “{0}”:', 'Neues Passwort für „{0}“:'),
    "•••••• (şifreli saklanır — 'Şifre değiştir' ile yenisini ver)": ("•••••• (stored encrypted — set a new one with 'Change password')", "•••••• (verschlüsselt — mit 'Passwort ändern' neu vergeben)"),
    'Kimlik (ID)': ('ID', 'ID'),
    'Rol': ('Role', 'Rolle'),
    'Çevrimiçi': ('Online', 'Online'),
    'Son görülme': ('Last seen', 'Zuletzt gesehen'),
    'Oluşturulma': ('Created', 'Erstellt'),
    'Cihaz kimliği': ('Device ID', 'Geräte-ID'),
    'Oturumu kapat': ('Log out member', 'Mitglied abmelden'),
}
