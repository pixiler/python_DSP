# Python Öğrenme Planı — MATLAB'dan Python/NumPy'a Geçiş
 
## Genel Hedef
 
MATLAB'da alışkın olunan matris/vektör işlemlerini Python + NumPy ile
yapabilmek, telekomünikasyon temalı DSP işlemlerini Python'da tekrar
üretebilmek ve sonunda VUnit ile profesyonel VHDL testbench'leri
kurabilecek Python altyapısına sahip olmak.
 
**Sıra:** Python temelleri → NumPy → Matplotlib → SciPy (DSP) →
profesyonel alışkanlıklar (pytest, modüler kod) → VUnit.
 
---
 
## Seviye Tespiti (yapıldı)
 
Program başında kısa bir quiz + mini kod görevi ile mevcut seviye
ölçüldü. Sonuç: **kod yazma pratiği teorik bilginin önünde.**
 
- Güçlü: fonksiyonlara bölme, docstring alışkanlığı, f-string,
  `if __name__ == "__main__"`, pip/venv kavramı.
- Boşluklar: slicing kuralları (bitiş dahil değil), dict mantığı,
  list/tuple farkı, list comprehension, dosya okuma/yazma.
Bu yüzden Hafta 1, sıfırdan anlatım yerine sadece bu boşluklara
odaklanacak şekilde daraltıldı.
 
---
 
## Hafta 1 — Python Temelleri (MATLAB Gözlüğüyle) ✅ Tamamlandı
 
**Konular:** slicing kuralları, dict, tuple vs liste, list comprehension,
dosya okuma/yazma (`with open(...)`).
 
**Görev 1 — Sinyal ölçüm dosyası analizi:**
`kanal_adi,deger` formatındaki bir `olcumler.txt` dosyasını satır satır
okuyup, verileri kanal bazında bir dict içinde topladı
(`{"ch1": [2.5, 2.7, ...], ...}`), her kanal için ortalama/max hesapladı,
list comprehension ile kare alma ve filtreleme yaptı, slicing ile ilk/son
elemanları ve ters listeyi aldı, sonucu `sonuclar.txt`'ye yazdı.
 
**Durum:** Tamamlandı. `analiz.py` (yardımcı fonksiyonlar: ortalama,
maximum, even_count, square) ve `signal_result_folder_analysis.py`
(ana akış) olarak modüler şekilde çözüldü, import mekanizması
(`from analiz import ...`) pratiği yapıldı.
 
---
 
## Hafta 2 — NumPy: MATLAB'ın Python'daki Karşılığı ✅ Tamamlandı
 
**Konular:** `np.array`, `zeros`, `ones`, `linspace`, `arange`, slicing,
broadcasting, matris çarpımı (`@` vs eleman bazlı `*` — MATLAB'ın tam
tersi), `A.T`.
 
**Görev 2 — MATLAB kodunu NumPy'a çevir:**
 
1. **Isınma:** Tahminlerin 5'te 3'ü ilk seferde doğruydu. İki kritik
   yanılgı düzeltildi: `linspace(0,1,5)` adım sayısını `N` değil `N-1`
   böler (`endpoint` mantığı); `A*B`/`A@B` MATLAB'ın tam tersi yönde
   karıştırılmıştı (NumPy'da `*` eleman bazlı, `@` matris çarpımı).
2. **Asıl görev — `assiment.m`'in tam çevirisi:** `sine_wave`,
   `plot_signal`, `fir1`, `freqz`, `fft`, `fir_filter`, `plot_spectrum`
   fonksiyonlarından oluşan modüler bir yapı (`matlab_example.py`)
   kuruldu; upsample/downsample (interpolation/decimation) ayrı bir
   dosyada (`interpolation_decimation.py`) `up_sample`, `down_sample`,
   `interpolate`, `decimate` fonksiyonlarıyla tamamlandı.
   **Yolda bulunup düzeltilen gerçek hatalar** (öğretici oldukları için
   not ediliyor):
   - `list + list` toplama değil **birleştirme** yapıyor — `sine_wave()`
     `.tolist()` yerine `np.ndarray` döndürecek şekilde güncellendi.
   - `plt.subplots(2,2)` unpacking hatası — `(ax1, ax2) = axs` ile değil
     `axs[satır, sütun]` ile erişilmesi gerektiği görüldü.
   - **İsim gölgeleme:** fonksiyon parametresini `signal` diye adlandırmak
     `import scipy.signal as signal` modülünü fonksiyon içinde gölgeliyor
     — `fir_filter` içinde `AttributeError`'a yol açtı, parametre adı
     değiştirilerek çözüldü.
   - FFT genlik normalizasyonu eksikti (MATLAB'daki `/L` adımı unutulmuş,
     eklendi).
   - `len(signal)` ile gerçek örnekleme hızı `Fs` karıştırılmıştı
     (`interpolate`/`decimate` fonksiyonlarında `Fs_new` yanlış
     hesaplanıyordu) — fonksiyonlara `Fs` parametre olarak eklenerek
     düzeltildi.
   - `decimate()`'de filtrelenmiş ama henüz downsample edilmemiş sinyal
     yanlış (yeni) örnekleme hızıyla çizdiriliyordu.
   **Kavramsal olarak pekiştirilenler:** `-6dB` kesim noktasını
   interpolasyonla bulup grafikte işaretleme; upsample sonrası oluşan
   *image*'in ve filtre ile bastırılmasının sayısal doğrulaması;
   **aliasing**'in somut bir örnekle (filtresiz downsample'da 15kHz'in
   10kHz'e katlanması) gösterilmesi — "önce filtrele, sonra downsample"
   kuralının neden zorunlu olduğu buradan çıktı.
3. **Bonus (`np.loadtxt`):** Yapılmadı — istenirse ileride kısa bir ek
   olarak dönülebilir.
---
 
## Hafta 3 — Matplotlib + Sinyal Üretimi ✅ Tamamlandı

**Konular:** `np.random.normal` ile AWGN üretimi, güç/SNR hesabı
(teorik vs ölçülen), `stem`, log eksenler, tek yanlı spektrum.

**Görev 3 — Gürültülü sinyal ve SNR analizi:**

1. **Isınma:** 3'te 2 doğru. Düzeltilen yanılgı: `np.random.normal`'ın
   `scale` parametresi **standart sapma**dır, varyans değil — güç
   σ² = scale²'dir. (Karıştırılsaydı hedeflenen 10 dB yerine ~23 dB
   çıkacaktı ve kod sessizce "çalışacaktı".)

2. **Ana görev (`week3.py`):** `add_awgn(signal, snr_db)` fonksiyonu
   yazıldı — σ, hedef SNR'dan kod içinde hesaplanıyor; gürültü ayrıca
   döndürülüyor. Ölçülen SNR ile hedef karşılaştırıldı (~10 dB ✓).
   Temiz/gürültülü sinyal zaman domeninde üst üste, spektrumlar
   Hafta 2'nin `plot_spectrum`'uyla çizildi. Bonus 1: SNR = 0/10/20 dB
   için `stem` karşılaştırması. Bonus 2: `plot_spectrum`'a `xscale`
   parametresi eklenerek log eksen + tek yanlı spektrum desteği kazandırıldı.

   **Yolda bulunup düzeltilen hatalar:**
   - `ax.title()` çağrısı — `title` metot değil `Text` nesnesi;
     doğrusu `ax.set_title(...)`.
   - `axes` parametresi alan fonksiyonda `plt.stem` kullanımı — çizim
     hep aktif eksene gitti, 3 panelden 2'si boş kaldı. **Kural:**
     fonksiyona `axes` veriliyorsa içeride `plt.` ile çizim yapılmaz.
   - Slicing'de `len(f)/2` — `/` float döndürür, dilim tamsayı ister;
     doğrusu `//`. (MATLAB'da bu ayrım yok.)
   - fftshift'li dizide `[:N//2]` **negatif** frekansları seçer —
     log eksen için gereken pozitif yarı `[N//2:]`.
   - `label`'ın `plot(...)`'a değil `set_label()`'a verilmesi —
     legend boş kaldı.
   - Döngüden artakalan `noisy_signal`'ın (son iterasyon, 20 dB)
     etiketsiz kullanımı — hata değil ama yanıltıcı grafik ürettiği
     için not edildi.

   **Kavramsal olarak pekiştirilenler:** Sinüs gücü = A²/2; dB↔lineer
   dönüşüm zinciri (SNR → Pn → σ); sonlu örneklemde ölçülen istatistiğin
   teorikten sapması; **işleme kazancı** — gürültü N bin'e yayılırken
   sinüs tek bin'de toplanır, bu yüzden 0 dB SNR'da bile spektrumda
   1 kHz tepesi net görünür (~10·log₁₀(N) dB avantaj) — Hafta 4'teki
   "filtreleme neden işe yarar" sorusunun temeli; log eksende nokta
   yoğunluğu yanılsaması (bin'ler eşit aralıklı, dekadlar değil);
   **frekans çözünürlüğü Δf = 1/T** — süreden gelir, örnekleme
   hızından değil.

3. **Hafta 4'e devreden:** `add_awgn` filtre karşılaştırmasında
   doğrudan kullanılacak; FIR grup gecikmesi sorusu açık bırakıldı.
 
---
 
## Hafta 4 — SciPy ile Telekom/DSP İşlemleri
 
> **Not:** `firwin` (fir1 karşılığı), `lfilter`, `freqz` zaten Hafta
> 2'de aktif olarak kullanıldı. Hafta 4, bu üçünü tekrar öğretmek yerine
> **yeni** SciPy araçlarına odaklanacak.
 
**Konular:** `scipy.signal.butter` (IIR filtre tasarımı — FIR'a göre
farkı), `filtfilt` (sıfır-fazlı filtreleme — Hafta 2'de gördüğümüz
filtre "transient"ını nasıl ortadan kaldırdığı), `welch` (güç spektral
yoğunluğu tahmini), `resample` (Hafta 2'de elle yazdığımız
`interpolate`/`decimate` fonksiyonlarıyla karşılaştırma fırsatı).
 
**Görev 4:** Hafta 3'teki gürültülü sinyale hem FIR (`firwin`+`lfilter`,
zaten bilinen) hem IIR (`butter`+`filtfilt`) alçak geçiren filtre
tasarlayıp uygulamak, ikisinin frekans cevabını ve transient
davranışını karşılaştırmak.
 
**Bonus:** Basit bir BPSK modülasyon/demodülasyon zinciri kurup BER vs
SNR eğrisi çıkarmak. *(`assiment.m`'deki upsample/downsample mantığı
artık Hafta 2'den hazır — `interpolation_decimation.py` doğrudan temel
alınabilir.)*
 
---
 
## Hafta 5 — Profesyonel Python Alışkanlıkları
 
**Konular:** sanal ortamlar (`venv`), `pip`, kodu modüllere bölme,
`pytest` ile birim test yazma, temel OOP (class'lar).
 
> Pytest burada özellikle önemli, çünkü VUnit'in test mantığına zihinsel
> hazırlık sağlıyor.
 
**Görev 5:** Hafta 2 ve 4'teki DSP fonksiyonlarını (`matlab_example.py`,
`interpolation_decimation.py`) bir modüle taşımak ve her fonksiyon için
pytest testleri yazmak (örn. "filtre çıkışının gücü girişten küçük
olmalı", "upsample sonrası uzunluk `m` katına çıkmalı" gibi assert'ler
— Hafta 2'de zaten elle sayısal olarak doğruladığımız şeylerin çoğu
buraya test olarak dökülebilir).
 
---
 
## Hafta 6 — VUnit'e Giriş
 
**Konular:** VUnit kurulumu, `run.py` yapısı, VHDL testbench'lerini
VUnit ile organize etme, `check` kütüphanesi, Python tarafından test
verisi üretip dosya üzerinden VHDL'e besleme.
 
**Görev 6 (final projesi):** Basit bir VHDL modülü (örn. sayaç veya FIR
filtre) için VUnit testbench'i kurmak. Test vektörlerini NumPy ile
üretmek, CSV'ye yazmak, VHDL'de okumak ve çıkışı Python'da doğrulamak.
Önceki 5 haftanın hepsini birleştiren kapanış görevi.
 
---
 
## Pratik Notlar
 
- NumPy öğrenirken resmi **"NumPy for MATLAB users"** karşılaştırma
  tablosunu yanında tut.
- **Spyder IDE**, MATLAB arayüzüne benzer (variable explorer, konsol),
  geçişi kolaylaştırabilir; uzun vadede **VS Code**'a geçmek önerilir —
  VUnit projelerinde daha rahat çalışılır.
- Her hafta sonunda kod + kısa notlar (ne çalıştı, ne çalışmadı, hangi
  hata alındı) paylaşılıp birlikte gözden geçiriliyor.
- **Hafta 2'den genel dersler:** (1) Python'da fonksiyon parametre
  adlarını, import edilen modül adlarıyla çakışmayacak şekilde seçmek
  gerekiyor (isim gölgeleme sessizce çalışıp beklenmedik yerde patlıyor).
  (2) "Örnek sayısı" (`len(x)`) ile "örnekleme hızı" (`Fs`, Hz) birbirine
  benzer görünse de tamamen farklı büyüklükler — biri diğerinin yerine
  kullanılırsa hata genellikle sessiz kalıp sadece eksen/etiket
  seviyesinde ortaya çıkıyor, bu da bulması en zor hata türü.