"""Açıklama sistemi: her ayarın / bilginin yanındaki (?) simgesi ve detaylı ipucu metinleri.

Fare (?) simgesinin üstüne gelince açıklama hemen açılır (beklemeden). Metinler tek bir yerde
toplanır ki her sayfada aynı dil ve aynı biçim kullanılsın.
"""
from __future__ import annotations

from core.i18n import T

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QHBoxLayout, QLabel, QToolTip, QWidget

from . import theme


def tip(title: str, body: str, rec: str = "", more: str = "", less: str = "") -> str:
    """Biçimli ipucu: başlık, açıklama, önerilen değer, artırınca / azaltınca ne olur."""
    title, body, rec, more, less = T(title), T(body), T(rec), T(more), T(less)
    h = (f"<div style='max-width:360px'>"
         f"<div style='font-weight:700; font-size:13px; color:{theme.ACCENT}; margin-bottom:4px'>{title}</div>"
         f"<div style='color:{theme.TEXT}'>{body}</div>")
    if more or less:
        h += "<table style='margin-top:6px' cellspacing='0' cellpadding='1'>"
        if more:
            h += f"<tr><td style='color:{theme.SUCCESS}'>▲&nbsp;</td><td>{more}</td></tr>"
        if less:
            h += f"<tr><td style='color:{theme.WARNING}'>▼&nbsp;</td><td>{less}</td></tr>"
        h += "</table>"
    if rec:
        h += (f"<div style='margin-top:6px; padding:4px 6px; background:{theme.BG}; border-radius:4px'>"
              f"<b>{T('Önerilen:')}</b> {rec}</div>")
    return h + "</div>"


class HelpIcon(QLabel):
    """Küçük yuvarlak (?) — üstüne gelince açıklama hemen görünür."""

    def __init__(self, html: str, parent=None):
        super().__init__("?", parent)
        self.setObjectName("helpIcon")
        self.setFixedSize(18, 18)
        self.setAlignment(Qt.AlignCenter)
        self.setCursor(Qt.CursorShape.WhatsThisCursor)
        self.setToolTip(html)
        self._html = html

    def enterEvent(self, e):
        QToolTip.showText(self.mapToGlobal(self.rect().bottomRight()), self._html, self)
        super().enterEvent(e)


def help_label(text: str, html: str | None, muted: bool = False) -> QWidget:
    """Form satırı etiketi: metin + (?) simgesi."""
    w = QWidget()
    lay = QHBoxLayout(w)
    lay.setContentsMargins(0, 0, 0, 0)
    lay.setSpacing(6)
    lbl = QLabel(T(text))
    if muted:
        lbl.setObjectName("muted")
    lay.addWidget(lbl)
    if html:
        lay.addWidget(HelpIcon(html))
        lbl.setToolTip(html)
    lay.addStretch(1)
    return w


# ---------------------------------------------------------------------------- metinler
H = {
    # --- Balık sistemi
    "bite_area": tip(T("Kendi karakterimin işaret alanı"),
                     T("Yanında balık tutan başka oyuncular varsa onların kafasında da balık işareti çıkar. Burada "
                     "kendi karakterinin kafasının üstünü seçersen bot SADECE oradaki işarete tepki verir. "
                     "Seçmezsen ekranın ortasındaki karaktere (seninkine) en yakın işaret kullanılır; olta atılır "
                     "atılmaz ekranda olan işaretler de başkasınındır diye yok sayılır. Canlı görüntüde başkalarının "
                     "işaretleri gri ('baskasi'), seninki yeşil görünür."), T("Yanında oyuncu varsa seç"), "", ""),
    "bite_timeout": tip(T("Balık işaretini en fazla bekle"),
                        T("Olta atıldıktan sonra bu sürede işaret görülmezse olta yeniden atılır."), T("40 sn"), "", ""),
    "bite_react": tip(T("İşareti görünce basmadan önce"),
                      T("İnsan gibi görünmek için işaret ile Space arasında rastgele kısa bir bekleme."),
                      T("90 – 200 ms"), T("Daha insansı ama işaret kısa sürüyorsa kaçabilir."), T("Daha hızlı tepki.")),
    "timing_latency": tip(T("Tuş gecikmesi payı"),
                          T("Space'e basıldığı an ile oyunun bunu işlediği an arasındaki süre. Bot, balık kutucuğun "
                          "ortasına bu kadar süre KALA basar. 'Kendisi öğrensin' açıksa her turda balığın durduğu "
                          "yere bakılıp düzeltilir."), T("45 ms + otomatik"), T("Daha erken basar."), T("Daha geç basar.")),
    "bite_change": tip(T("İşaret arama"),
                       T("assets\\olta\\isaret klasöründe işaret resmi varsa onunla aranır (en güvenilir). Yoksa kafa "
                       "bölgesinde aniden çıkıp yerinde duran yeni bir şekil aranır; Space'ten sonra pencere açılınca "
                       "o şekil işaret resmi olarak kaydedilir."), T("Açık"), "", ""),
    "timing_test": tip(T("Test"),
                       T("Pencere testi: zamanlama penceresi ekrandayken bas; kutucuğu ve balığı bulabiliyor mu yazar "
                       "(data\\pencere_testi.png). İşaret testi: işaret görünürken bas; resimle bulunuyor mu yazar."),
                       "", "", ""),
    # --- Olta ve giriş
    "cast_key": tip(T("Tuş"), T("Olta atma, balık işaretine ve zamanlama penceresine basılan tuş."), T("SPACE"), "", ""),
    "input_method": tip(T("Giriş yöntemi"),
                        T("Karma: tuşa basarken oyun penceresi bir an öne alınır ve gerçek klavye kullanılır (oyun "
                        "arka plandaki pencereye gönderilen tuşu kabul etmiyor). Birden fazla client varsa tuşa "
                        "basılan anlar sırayla yapılır. Arka plan: pencereye tuş mesajı gönderilir (oyun destekliyorsa "
                        "pencere hiç öne gelmez). Ön plan: tek client için gerçek klavye."), T("Karma"), "", ""),
    "key_test": tip(T("Tuşu test et"),
                    T("Seçili client'a tuşu bir kez gönderir. Karakterin elinde olta varken bas: olta atıldıysa "
                    "seçili giriş yöntemi çalışıyor."), "", "", ""),
    "cooldown": tip(T("Ödülden sonra olta atmadan önce"),
                    T("Ödül çarkı kapandıktan sonra oltayı tekrar atmadan önce rastgele bekleme (insansı)."),
                    T("1200 – 1800 ms"), T("Daha insansı ama daha yavaş."), T("Daha hızlı.")),
    "break": tip(T("Akıllı mola"), T("Belirli aralıklarla birkaç dakika hiçbir şey yapmadan bekler (insansı davranış)."),
                 T("İsteğe bağlı"), "", ""),
    "break_every": tip(T("Mola sıklığı"), T("İki mola arasındaki rastgele süre."), T("40 – 70 dk"), "", ""),
    "break_len": tip(T("Mola süresi"), T("Bir molanın rastgele uzunluğu."), T("2 – 6 dk"), "", ""),
    "scan_fps": tip(T("İşaret arama hızı"),
                    T("Balık beklerken kafa bölgesine saniyede kaç kez bakılır (sadece o küçük bölge yakalanır). "
                    "Zamanlama penceresi ise her zaman olabildiğince hızlı (100+ kare/sn) izlenir."), "60",
                    T("İşaret daha çabuk görülür, işlemci biraz daha çalışır."), T("İşlemci rahatlar.")),
    "language": tip(T("Dil / Language / Sprache"), T("Türkçe, English, Deutsch. Yeniden başlatınca uygulanır."), "", "", ""),
    "preview_fps": tip(T("Canlı görüntü kare hızı"),
                       T("Panelde canlı izlemenin saniyedeki kare sayısı (en fazla 120). Botun kendisini etkilemez."), "60", "", ""),
    # --- Captcha
    "captcha": tip(T("Captcha (bot kontrolü)"),
                   T("Sunucunun captcha'sı (\"Atın üzerine tıklayın\" + 3x3 simge + ~10 sn sayaç) bot beklerken "
                   "~0,7 sn'de bir aranır ('Kalan Süre:' yazısının resmiyle, çok hızlı). Görünce balık tutmayı "
                   "durdurur; 'Otomatik çöz' açıksa ne istendiğini okur (Windows yazı tanıması ya da başlık "
                   "resmi) ve o simgeye insan gibi fareyle gidip tıklar. Birden fazla client varsa captcha'sı "
                   "çıkan client sıranın başına geçer, oynayan client turunu bırakır. Bilinmeyen bir simge "
                   "istenirse sesli uyarır; sen bir kez elle çözünce bot o simgeyi öğrenir."),
                   T("Hepsi açık"), "", ""),
    "captcha_wait": tip(T("Elle çözüm için bekleme"),
                        T("Otomatik çözülemeyen captcha için botun bekleyeceği en uzun süre. Süre dolarsa bot durur."),
                        T("10 dk"), "", ""),
    "captcha_test": tip(T("Captcha testi"),
                        T("Captcha ekrandayken bas: bot ne okuduğunu, neyi seçeceğini ve nereye tıklayacağını yazar "
                        "(tıklamaz). Seçenekler resimse: her seçeneğin resmini kırpıp assets\\captcha\\esya "
                        "klasörüne adıyla kaydet (kalkan.png, kilic.png, zirh.png…). Aynı şeyin birden fazla "
                        "resmi olabilir: kalkan_2.png. Captcha penceresinin başlığının resmini "
                        "assets\\captcha\\pencere klasörüne koyarsan yazı tanıma olmasa da pencere bulunur."),
                        "", "", ""),
    # --- Client'lar
    "filter": tip(T("Süreç filtresi"),
                  T("Client listesinde sadece adı bu metni içeren programlar gösterilir (boş = hepsi)."),
                  T("Boş veya oyunun exe adı")),
    "pick_key": tip(T("Client seçme tuşu"),
                    T("Fare oyun penceresinin üstündeyken bu tuşa basınca o pencere client olarak seçilir."),
                    T("F7")),
    "known": tip(T("Hatırlanan client'lar"),
                 T("Daha önce seçtiğin oyun programları; bir sonraki açılışta otomatik listelenir.")),
    "blocked": tip(T("Engellenen programlar"),
                   T("Bu programlar asla client olarak listelenmez (tarayıcı, Discord vb.). Virgülle ayır."),
                   T("firefox.exe, chrome.exe, discord.exe")),
    # --- Client bilgileri
    "i_exe": tip(T("Program"), T("Seçili oyun penceresinin programı ve süreç numarası (PID).")),
    "i_res": tip(T("Çözünürlük"), T("Oyun penceresinin iç alanının boyutu.")),
    "i_pos": tip(T("Ekran konumu"), T("Oyun penceresinin ekrandaki sol üst köşesi.")),
    "i_dpi": tip(T("Ölçekleme"), T("Windows ekran ölçeklemesi (%100, %125...). Bot bunu kendisi hesaba katar.")),
    "i_uptime": tip(T("Çalışma süresi"), T("Bot bu client'ta ne kadardır çalışıyor.")),
    "i_input": tip(T("Giriş yöntemi"), T("Tuşun oyuna gönderilme şekli (Ayarlar'dan değişir).")),
    "i_area": tip(T("İşaret alanı"),
                  T("Botun balık işaretini aradığı yer. 'Seçili' ise sadece senin çerçevelediğin alana bakar; "
                  "'otomatik' ise ekranın ortasındaki (kendi) karakterinin üstüne bakar.")),
    "i_sign": tip(T("İşaret resmi"),
                  T("assets\\olta\\isaret klasöründeki balık işareti resimleri ve oyundaki ölçeği (ilk bulunuşta "
                  "öğrenilir).")),
    "i_err": tip(T("Hedefe ortalama uzaklık"),
                 T("Space'e basınca balığın durduğu yerin kutucuğun tam ortasına (mor nokta) ortalama uzaklığı.")),
    "i_last": tip(T("Son sonuç"), T("Son turun sonucu ve balığın hedefe uzaklığı.")),
    # --- Panel kartları / düğmeler
    "s_total": tip(T("Toplam tur"), T("Bu oturumda bütün client'larda oynanan zamanlama penceresi sayısı.")),
    "s_ok": tip(T("İsabet"), T("Balığın kutucuğun içinde durduğu turlar.")),
    "s_fail": tip(T("Iska"), T("Balığın kutucuğun dışında durduğu turlar.")),
    "s_rate": tip(T("Oran"), T("İsabetlerin tüm turlara oranı.")),
    "s_active": tip(T("Aktif bot"), T("Şu anda çalışan bot sayısı (her client için bir bot).")),
    "s_lat": tip(T("Tuş gecikmesi"),
                 T("Space'e basıldığı an ile oyunun bunu işlediği an arasındaki süre. Bot balık mor noktaya "
                 "varmadan bu kadar önce basar; her turda balığın durduğu yere bakarak düzeltir.")),
    "b_head": tip(T("İşaret alanımı seç"),
                  T("Yanında balık tutan başka oyuncular varsa onların kafasında da işaret çıkar. Kendi karakterinin "
                  "kafasının üstünü çerçevele; bot sadece oradaki işarete tepki verir.")),
    "b_scan": tip(T("Tarama"),
                  T("Botun her adımda gördüğünü ve kararını canlı listeler (işaret, kutucuk, balık hızı, basış anı, "
                  "sonuç, seri sayacı). 'Büyüt' ayrı bir pencerede açar. Kayıtlar data\\tarama klasörüne de yazılır.")),
    "b_snap": tip(T("Anlık kayıt"), T("O anki canlı görüntüyü data\\anlik klasörüne kaydeder.")),
    "streak_check": tip(T("Seri kontrolü"),
                        T("Zamanlama penceresindeki 'Seri' sayısı isabette artar, ıskada sıfırlanır. Açıksa bot "
                        "kendi ölçümünü bu sayıyla karşılaştırır ve çelişirse turu düzeltir. Sayı birkaç turdur hiç "
                        "değişmiyorsa kontrol kendiliğinden kapanır.")),
    "captcha_keep": tip(T("Saklanacak captcha resmi"),
                        T("Yakalanan captcha ekran görüntülerinden en yenileri tutulur, eskileri silinir (disk dolmasın).")),
    "b_tile": tip(T("Pencereleri diz"),
                  T("Client pencerelerini (en fazla 4) ekrana 2x2 dizer, boyutlarına dokunmaz. Pencereler üst üste "
                  "binmezse her bot kendi çubuğunu ekrandan çok hızlı okur; birbirini örtmez.")),
    "summary": tip(T("Özet"),
                   T("Botun gerçekten saydığı değerler. 'Seri sayacıyla doğrulanan': sonucu oyunun Seri sayısıyla "
                   "kontrol edilen tur sayısı. 'Düzeltilen': botun ölçümü Seri sayısıyla çeliştiği için düzeltilen "
                   "tur. 'Saatte tur': çalışma süresine göre.")),
    "s_casts": tip(T("Atılan olta"), T("Bu oturumda atılan olta sayısı; altında işaret hiç gelmeyen atış sayısı.")),
    "live": tip(T("Canlı izleme"),
                T("<b>Zamanlama penceresi:</b> yeşil çerçeve = kutucuk, <span style='color:#ff28c8'>●</span> kalın mor "
                "nokta = hedef (kutucuğun tam ortası), kırmızı çerçeve = siyah balık, sarı nokta = tuş oyuna "
                "ulaştığında balığın olacağı yer, ✕ = balığın durduğu yer.<br>"
                "<b>Balık beklerken:</b> mavi = arama alanı, mor artı = kendi kafan, yeşil = senin işaretin, "
                "gri = başka oyuncuların işareti (yok sayılır).")),
}
