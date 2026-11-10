# FishBot

Metin2 sunucusu için VIP üyelere özel, görüntü tabanlı balık botu. Sunucunun balık sistemi:
olta → kafada balık işareti → zamanlama penceresi (siyah balık + kutucuk) → ödül çarkı.

## Nasıl çalışır

Bot her client için şu döngüyü tekrarlar:

1. **Space** ile oltayı atar.
2. Karakterin kafasında **balık işareti** çıkınca (insan gibi 90–200 ms sonra) **Space**'e basar.
   - İşaret, `assets\olta\isaret\balik_isareti.png` resmiyle (konuşma balonu + olta + mavi balık) aranır.
     Resmin oyundaki boyutu ilk bulunuşta ölçülür ve hatırlanır; sonraki aramalar çok hızlıdır.
   - Resimle bulunamazsa (yedek) kafa bölgesinde "aniden çıkıp yerinde duran yeni şekil" aranır; Space'e
     basınca pencere açılırsa o şekil de resim olarak kaydedilir.
3. **Zamanlama penceresi** açılır. Bot mavi çubuğu, lacivert çerçeveli **kutucuğu** (her seferinde başka yerde)
   ve **siyah balığı** bulur. Bu pencere için resim gerekmez: çubuk rengiyle, kutucuk renk tonuyla, balık
   koyuluğuyla bulunur.
   - Kutucuk, etrafındaki 1 piksellik **lacivert çerçeveden** bulunur. Bu çerçevenin üst ve alt çizgisi mavi
     suyun dışında durduğu için su dokusu, sarımsı parlamalar ve balık onu şaşırtamaz. Çerçeve görülemezse
     yedek olarak renk tonuna bakılır.
   - Kutucuk önce **sabitlenir** (3 aynı okuma). Tur içinde yer değiştirirse bot yeni yerine geçer.
   - Pencere açıldıktan sonra ~0,4 sn beklenir; balık en az yarım kutucuk kadar **yol almalı** ve kutucuğun
     ortasına **doğru** gidiyor olmalı. Balık daha kıpırdamadan ya da ortadan uzaklaşırken asla basılmaz.
   - Balığın hızı **ve hızlanması** ölçülür (seri arttıkça balık hızlanabilir). Balık kutucuğun **tam ortasına** varmadan, tuşun oyuna ulaşma süresi kadar önce
     Space'e basılır. Botun o an neyi beklediği canlı görüntüde yazar ("kutucuk sabitleniyor", "izleniyor"…).
   - Bu "tuş gecikmesi" her turda balığın durduğu yere bakılarak ölçülür ve kendiliğinden düzeltilir.
     Log'da "merkeze +3 px" gibi görünür.
4. **Seri sayacı ile kontrol:** Pencerenin sağ üstündeki "Seri: N" sayısı isabette artar, ıskada sıfırlanır.
   Bot her pencerede bu sayının resmini okur ve bir önceki pencereyle karşılaştırır. Kendi ölçümü "isabet"
   dediği halde sayı artmadıysa turu **ıska olarak düzeltir** (ve tersi). Listede "seri sayacına göre
   düzeltildi" yazar. Oyun sayıyı bir sonraki pencerede güncelliyorsa düzeltme bir tur sonra gelir.
   Sayı birkaç turdur hiç değişmiyorsa (okunamıyorsa) bu kontrol kendiliğinden kapanır.
5. Alttaki **ödül çarkı** kendiliğinden döner. Çark durunca bot işaretin (▲) gösterdiği **eşyayı ve altındaki
   adedi** okur (ör. "15 × Mini balık") ve toplar. Çark her karede okunur; art arda aynı okunan son sonuç
   kazanandır. Pencere çok çabuk kapanırsa son karelerden okunur. Pencere kapanınca baştan başlar.
   - Eşyalar `assets\olta\odul\` klasöründeki resimlerle tanınır (`mini_balik.png`, `istiridye.png`,
     `yuzuk.png`). Adet, kutudaki rakamlardan resimsiz okunur.
   - Yeni bir eşya çıkarsa resmi `assets\olta\odul\bilinmeyen_1.png` olarak kaydedilir; dosyanın adını eşyanın
     adıyla değiştir (ör. `deniz_kabugu.png`), bot bir dahakine adıyla yazar.
   - **Ekran görüntüsü kaydedilmez.** Toplamlar sadece `data\odul_toplam.json` dosyasında tutulur (birkaç yüz
     bayt). Eski sürümün `data\oduller\` resimleri ve 10 günden eski tarama kayıtları açılışta silinir.

Birden fazla client aynı anda çalışabilir: hepsi balık beklerken paralel durur. Sadece tuşa basılan kısa anlar
ve zamanlama penceresi sırayla yapılır (oyun tuşu ancak öndeki pencereden alıyor).

**Yanında başka oyuncular da balık tutuyorsa** onların kafasında da işaret çıkar. Bot sadece kendi
karakterinin işaretine tepki verir:
- **Alan seçersen (önerilen):** Detay ekranında **🎯 İşaret alanımı seç** (ya da Ayarlar > Balık sistemi).
  Ekran görüntüsünde kendi kafanın üstünü çerçevele. Bot sadece o çerçevedeki işarete bakar.
- **Alan seçmezsen:** Kamera kendi karakterini hep ekranın ortasında tutar. Bot sadece ortadaki karakterin
  üstündeki işareti kabul eder. Olta atılır atılmaz ekranda olan işaretler de başkasınındır diye yok sayılır.
- Canlı görüntüde senin işaretin yeşil ("BENIM ISARETIM"), başkalarınınki gri ("baskasi") görünür.

**Testler (Ayarlar > Balık sistemi):**
- **Pencere testi:** Pencere açıkken bas. Kutucuk ve balık bulunuyor mu yazar, `data\pencere_testi.png`'yi kaydeder.
- **İşaret testi:** İşaret görünürken bas. Kayıtlı işaret resimleriyle bulunuyor mu yazar.

Canlı görüntüde balık beklerken kafa arama alanı (mavi) ve bulunan işaret (yeşil) görünür. Zamanlama sırasında:
- kutucuk yeşil çerçeve, **tam ortası kalın mor nokta** (hedef),
- siyah balık kırmızı çerçeve,
- tuş oyuna ulaştığında balığın olacağı yer sarı nokta.

Space'e basılınca balığın durduğu yer beyaz ✕ ile işaretlenir; "DURDU: hedefe +2 px ISABET" yazar.

## Kullanım

1. Oyunda fareyi oyun penceresinin üstüne getir ve **F7**'ye bas: client listeye eklenir ve detay ekranı açılır.
   Bot client'ın exe adını hatırlar; bir dahakine **Yenile** onu kendisi bulur.
2. Karakterinin elinde olta olsun. Ayarlar > **⌨ Tuşu test et** ile tuşun oyuna gittiğini bir kez doğrula.
3. Yanında başka oyuncular da balık tutuyorsa: detay ekranında **🎯 İşaret alanımı seç**. Ekran görüntüsünde
   kendi kafanın üstünü çerçevele.
4. **▶ Başlat**. Canlı izlemede her şey işaretli görünür. Her tur sonunda **✓ İSABET** / **✗ ISKA** bandı
   ve "hedefe +3 px" gibi uzaklık çıkar. **F8** tüm botları anında durdurur.

Detay ekranında:
- **Tarama penceresi:** Botun her adımını canlı listeler: işaret, kutucuk, balık hızı, basış anı, sonuç ve
  gecikme. Kayıtlar `data\tarama\` klasörüne de yazılır.
- **Özet:** Sadece botun gerçekten saydığı değerler: oynanan tur, isabet/ıska, Seri sayacıyla doğrulanan ve
  düzeltilen turlar, hedefe ortalama uzaklık, saatte tur, işaret gelmeyen atışlar, captcha.
- **Tarama:** Botun her adımda ne gördüğü panelde canlı akar ('Büyüt' ayrı pencerede açar).
  Kazanılan ödüller panelde gösterilmez; Kayıtlar sayfasına yazılır.

## Dil ve hız

- **Dil:** Ayarlar > Olta ve giriş > Dil: Türkçe, English, Deutsch. Program yeniden açılınca uygulanır.
- **Zamanlama penceresi** her zaman ekranın yakalanabildiği en yüksek hızda izlenir (genelde 100+ kare/sn).
- **Canlı görüntü kare hızı** ve **işaret arama hızı** 120 kare/sn'ye kadar ayarlanabilir. Canlı görüntü botun
  isabetini etkilemez; sadece paneldeki görüntüyü akıcı yapar. İşaret arama hızını yükseltmek işareti biraz
  daha çabuk görmesini sağlar, işlemciyi biraz daha yorar.

## Kurulum (Windows)

1. Zip'i bir klasöre çıkar (Masaüstü veya Belgeler). Zip'in içinden doğrudan çalıştırma.
2. `baslat.bat` çift tıkla. Gerisini kendisi yapar:
   - Bot kütüphanelerinin (PySide6, numpy, pywin32) desteklediği **en yeni Python sürümünü**
     PyPI'den belirler.
   - Bilgisayarda bu sürüm yoksa python.org'dan en güncel halini indirir, **sessizce kurar
     ve PATH'e ekler** (yönetici izni gerekmez, kullanıcıya kurulur).
   - Bot klasöründe ayrı bir ortam (`.venv`) açar ve kütüphaneleri kurar.
   - Hiç VIP üye yoksa hemen eklemeyi önerir (`uye_ekle.bat`).
   İlk çalıştırma internet hızına göre birkaç dakika sürer, sonraki açılışlar birkaç saniyedir.

Eski bir Python kuruluysa ona dokunulmaz; yeni sürüm yanına kurulur.

### Sorun giderme

- **Pencere açılıp kapanıyor / hiçbir şey olmuyor:** `baslat.bat` artık hatayı ekranda gösterip bekler.
  O pencerenin ekran görüntüsünü al.
- **"Python otomatik hazırlanamadı":** İnternet bağlantısını ve antivirüsü kontrol et. Olmazsa
  https://www.python.org/downloads/ adresinden elle kur ("Add python.exe to PATH" işaretli).
- **Paket kurulumu başarısız:** İnternet bağlantısını kontrol et, `.venv` klasörünü silip tekrar dene.
- **Bot açılıp hata veriyor:** Ayrıntı `data\hata.log` dosyasındadır.

## Captcha (bot kontrolü)

Sunucunun captcha'sı: "Atın üzerine tıklayın" gibi bir başlık, 3x3 ızgarada simgeler (kılıç, at, kitap, iksir,
balık, kalkan…) ve ~10 saniyelik "Kalan Süre" sayacı. Süre kısa olduğu için bot olta atmadan önce ve **her
bekleme anında ~0,7 sn'de bir** ekrana bakar (`assets\captcha\pencere\kalan_sure.png` ile, OCR'siz ve çok hızlı).
Captcha görünce:

1. Ne istendiğini okur: Windows yazı tanıması (OCR) ya da `assets\captcha\yazi\` klasöründeki başlık resimleri.
2. Izgarada `assets\captcha\esya\` klasöründeki simgeyi bulup insan gibi fareyle tıklar
   (dosya adı = eşyanın adı: `at.png`, `kilic.png`, `kalkan.png`…). Seçenekler yazıysa yazıya tıklar.
3. Bilmediği bir simge istenirse sesli uyarır, ekran görüntüsünü `data\captcha\` klasörüne kaydeder ve bekler.
   Sen **bir kez elle çözersen** bot tıkladığın simgeyi `esya\` klasörüne kaydeder; bir dahakine kendisi çözer.
4. Birden fazla client varsa: captcha'sı çıkan client sıranın başına geçer, o an oynayan client turunu bırakır.

Ayarlar > Captcha bölümündeki **Captcha testi** düğmesi, captcha ekrandayken botun ne okuduğunu ve nereye
tıklayacağını gösterir (tıklamaz). Yazı tanıma paketi `baslat.bat` tarafından otomatik kurulur; kurulamazsa
captcha penceresinin bir parçasını `assets\captcha\pencere\` klasörüne koyarak resimle algılatabilirsin.
Windows'ta Türkçe yazı tanıma yoksa (yönetici PowerShell):
`Add-WindowsCapability -Online -Name "Language.OCR~~~tr-TR~0.0.1.0"`

## Üyelik sistemi (Supabase)

1. supabase.com'da bir proje aç.
2. **SQL Editor → New query**: `sql/supabase_kurulum.sql` dosyasının tamamını yapıştır. En alttaki
   `'admin'` ve `'SifreniYaz'` kısmını kendi yönetici adın ve şifrenle değiştir → **Run**.
3. **Project Settings → API**: "Project URL" ve "anon public" anahtarını `core/server.py` içine yaz
   (`SUPABASE_URL`, `SUPABASE_ANON_KEY`). **service_role anahtarını asla yazma.**
4. Programı aç, yönetici hesabınla gir: sol menüde **Üyeler** sayfası çıkar. Oradan üye ekle, süre ver
   (+1/+7/+30/+90/+365 gün ya da **süresiz**), askıya al, aynı anda en fazla kaç client, cihaz kilidi, not, sil.
   Değişiklikler çalışan botlara birkaç dakika içinde yansır (askıya alınan üyenin botu durur).

Tablolar dışarıya kapalıdır (RLS); program sadece SQL dosyasındaki fonksiyonları çağırabilir. Şifreler bcrypt
ile saklanır, 10 dakikada 8 hatalı denemeden sonra giriş geçici olarak kilitlenir. `core/server.py` boşsa bot
eskisi gibi yerel üye dosyasıyla (`data/users.json`) çalışır.

## Otomatik güncelleme (GitHub)

1. Botu GitHub'a yükle ve `core/server.py` içindeki `UPDATE_REPO`'ya `"kullanici/depo"` yaz.
2. Yeni sürüm yayınlamak için bir etiket gönder: `git tag v2.1.0` ve `git push --tags`
   (ya da GitHub → Actions → **Yayin** → Run workflow). GitHub, Windows'ta FishBot.exe'yi derler ve
   `FishBot.zip`'i yayına ekler (`.github/workflows/yayin.yml`).
3. Kullanıcılar botu açınca yükleme ekranında "Bot güncelleniyor… 12.4 / 98.0 MB" görür; indirme bitince bot
   kendini günceller ve yeniden açılır. Ayarlar, üyeler ve öğrenilen resimler korunur.

Depo herkese açık (public) olmalı ya da en azından yayınlar (Releases) erişilebilir olmalı.

## Captcha menüsü

Sol menüdeki **Captcha** sayfasında: ayarlar (aç/kapat, otomatik çöz, sesli uyar, bekleme, saklanacak resim
sayısı), sayılar (görülen / otomatik / elle çözülen / çözülemeyen), test (seçili client'ta captcha arar,
nereye tıklayacağını resim üzerinde gösterir), öğrenilen simgeler (yeniden adlandır / sil), yakalanan captcha
resimleri (önizleme) ve captcha olayları.

## Windows programı (.exe) yapmak

1. Bot klasöründe **`exe_yap.bat`**'a çift tıkla. Python yoksa kendisi indirir; kütüphaneleri ve PyInstaller'ı
   kurar, programı oluşturur (ilk seferde 5-10 dakika).
2. Sonuç `cikti\FishBot\` klasöründe: **FishBot.exe** (bot) ve **UyeYonetimi.exe** (üye ekle / uzat / sil;
   çift tıklayınca menü açılır). Mevcut üyeler ve ayarlar da bu klasöre taşınır.
3. Bilgisayarda **Inno Setup 6** kuruluysa ayrıca `cikti\FishBot_Kurulum.exe` oluşur: masaüstü kısayolu,
   Başlat menüsü ve "Programı kaldır" desteğiyle normal bir kurulum. Inno Setup yoksa `cikti\FishBot.zip` oluşur.

Program kullanıcı klasörüne kurulur (`%LOCALAPPDATA%\Programs\FishBot`), böylece ayarlarını ve öğrendiği
resimleri kendi klasörüne yazabilir. Kendi yaptığın .exe'ler imzasız olduğu için Windows SmartScreen veya
antivirüs ilk açılışta uyarabilir; "Ek bilgi → Yine de çalıştır" ya da klasörü antivirüs istisnasına ekle.
Oyun yönetici olarak çalışıyorsa FishBot.exe'yi de yönetici olarak çalıştır.

## Yerel üye yönetimi (Supabase kullanılmıyorsa)

En kolayı `uye_ekle.bat` (kullanıcı adı, şifre, gün sorar). Komut satırından da yapılabilir.
Üyeler şimdilik `data/users.json` dosyasında tutulur (şifreler PBKDF2 ile hash'lenir):

```
python tools/manage_users.py ekle ahmet Sifre123 30   # 30 günlük VIP
python tools/manage_users.py uzat ahmet 30
python tools/manage_users.py sifre ahmet YeniSifre
python tools/manage_users.py askiya ahmet
python tools/manage_users.py aktif ahmet
python tools/manage_users.py sil ahmet
python tools/manage_users.py liste
```

> Not: Yerel dosya geçici bir çözümdür. Kullanıcılara dağıtırken `data/users.json`
> dosyasını **dahil etme**. Lisans sunucusu eklendiğinde `main.py` içinde
> `LocalAuthProvider` yerine `RemoteAuthProvider` kullanılacak, arayüz değişmeyecek.

## Önemli notlar

- Oyun penceresi **simge durumuna küçültülmemeli**. Başka pencerelerin arkasında kalması sorun değil.
  Zamanlama sırasında pencere bir an öne alınır, çünkü oyun tuşu yalnızca öndeki pencereden kabul ediyor.
- **Birden fazla client (Karma yöntemi):** Pencereler üst üste olabilir. Bir pencerenin önünde başka bir pencere
  varsa bot o pencereyi ekrandan değil doğrudan pencerenin kendisinden okur, böylece yanlış client'ı okumaz.
  Bot panelini oyun pencerelerinin üstüne koyma; zamanlama sırasında çubuğun önü açık olursa okuma daha hızlıdır.
- Botu yönetici olarak çalıştırman gerekebilir. Oyun yönetici olarak açıldıysa bot da öyle açılmalı.
- Sorun bildirirken `data\tarama\` klasöründeki o günün kaydını gönder.

## Klasör yapısı

```
main.py                giriş noktası
core/bot.py            client başına bot döngüsü (olta → işaret → zamanlama → ödül çarkı)
core/reward.py         ödül çarkı: eşya ve adet okuma, toplamlar
core/i18n.py           dil desteği (çeviriler core/i18n_tablo.py)
core/timing.py         zamanlama çubuğu / kutucuk / siyah balık, basış zamanı, kafadaki işaret, canlı çizim
core/captcha.py        captcha algılama ve çözme
core/ocr.py            Windows yazı tanıma (captcha başlığı için, isteğe bağlı)
core/winapi.py         client listeleme, arka plan ekran yakalama, klavye, odak, sıra kilidi
core/config.py         ayarlar (data/config.json)
core/auth.py           VIP giriş
gui/                   PySide6 arayüz (giriş, client'lar, ayarlar, kayıtlar, işaret alanı, tarama)
assets/olta/isaret/    kafadaki balık işaretinin resmi
assets/olta/odul/      ödül çarkındaki eşyaların resimleri
assets/captcha/        captcha penceresi, başlık ve simge resimleri
tools/manage_users.py  üye yönetimi
```
