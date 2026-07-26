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
     düzeltildi. *(Not: bu düzeltme eksik kalmış, Hafta 4'te kalan kısmı
     ortaya çıktı — aşağıya bakınız.)*
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
   1 kHz tepesi net görünür (~10·log₁₀(N) dB avantaj); log eksende nokta
   yoğunluğu yanılsaması; **frekans çözünürlüğü Δf = 1/T** — süreden
   gelir, örnekleme hızından değil.

---

## Hafta 4 — SciPy ile Telekom/DSP İşlemleri ✅ Tamamlandı

**Konular:** `butter` (IIR tasarımı), `filtfilt` (sıfır-fazlı filtreleme),
`welch` (PSD tahmini), `resample`, `correlate`/`correlation_lags` ile
gecikme ölçümü, `group_delay`.

**Görev 4 — FIR vs IIR karşılaştırması (`week4.py`, `week4_bpsk.py`):**

1. **Isınma:** 4'te ~1,5 doğru — ama yanlışların hepsi haftanın hedef
   konularındaydı. Düzeltilenler:
   - `butter(4, ...)` hem `b` hem `a` için **5'er** katsayı döner
     (derece+1). `a`'nın 1'den uzun olması geri beslemenin varlığı
     demek; FIR'de `a = 1` olması geri beslemenin **yokluğu**
     (başlangıçta ters anlaşılmıştı).
   - Grup gecikmesi **(tap−1)/2 = 32 örnek**, "64/2+1 = 33" değil.
     Birim çevirisinde ciddi hata: 32 örnek @ 50 kHz = **640 µs**,
     "66 ms" değil (100 kat sapma).
   - `filtfilt` genlik cevabının **karesini** alır → dB cinsinden
     zayıflatma ikiye katlanır (−6 dB → −12 dB).
   - Periodogram/Welch varyans ilişkisi **ters** biliniyordu: ham
     periodogram yüksek varyanslıdır; Welch parçaları ortalayarak
     varyansı düşürür, bedeli çözünürlük kaybıdır.

2. **Ana görev:** 0 dB SNR'lı 1 kHz sinüs, ~2 kHz kesimli FIR (65 tap)
   ve 4. derece Butterworth ile filtrelendi; `lfilter` (her ikisi) ve
   `filtfilt` (IIR) çıkışları karşılaştırıldı.

   **Ölçülen sonuçlar:**

   | | SNR (çıkış) | Gecikme | Sinyal kaybı | Oturma |
   |---|---|---|---|---|
   | FIR `lfilter` | ~11,2 dB | 32 örnek | −0,3 dB | ~48. örnek |
   | IIR `lfilter` | ~10,6 dB | 11 örnek | −0,02 dB | ~37. örnek |
   | IIR `filtfilt` | ~10,9 dB | 0 örnek | −0,03 dB | ~7. örnek |

   Beklenen SNR iyileşmesi 10·log₁₀(25/2) ≈ 11 dB — ölçüm tuttu.
   Gürültü eşdeğer bant genişliği hesabıyla daha kesin: FIR ~1,7 kHz,
   IIR ~2,1 kHz.

   **Yolda bulunup düzeltilen hatalar:**
   - **`freqz` sarmalayıcısına `a` eklenmesi** — imzanın ortasına
     parametre eklenince mevcut pozisyonel çağrılar sessizce bozuldu
     (`a = 1024`, `fs = 2` oldu; FIR eğrisi 60 dB aşağı kayıp
     görünmez hale geldi).
   - **`apply_filter` / `apply_filtfilt` çağrı sırası** — sarmalayıcı
     `(input_signal, b, a)`, çağrı SciPy sırasıyla `(b, a, x)` yapıldı.
     `filtfilt` `padlen` hatası verdi ama **iki `lfilter` çağrısı
     sessizce çalışıp 65 ve 5 elemanlı çöp döndürdü.**
   - **SNR ölçümünde superposition eksikliği** — pay filtrelenmiş
     *karışım*, payda filtrelenmemiş gürültüydü. Doğrusu: temiz sinyali
     ve gürültüyü ayrı ayrı aynı filtreden geçirip güçlerini oranlamak.
   - **Korelasyonda periyodiklik belirsizliği** — saf sinüste kayma
     periyot modunda belirsiz (32 ≡ −18, mod 50). Arama aralığı
     `[0, P)` ile sınırlandırılarak çözüldü.
   - **Transient ölçümünde gürültülü sinyal kullanımı** — gürültü
     periyodik olmadığı için `x[n] − x[n+P]` metriği asla sıfıra inmedi
     (taban ~0,165'te takıldı). Transient filtrenin özelliğidir, temiz
     sinyalle ölçülür. Ayrıca zarf alınması ve eksenin kırpılması gerekti.
   - **`measure_delay`'in farklı örnekleme hızlarındaki sinyallerle
     çağrılması** — `y_up` (100 kHz, 10000 örnek) ile `y` (50 kHz,
     5000 örnek) korelasyonu anlamsız; sonuç 0 çıktı. Doğru çift
     `y_up` ↔ `y_resample`.
   - **Hafta 2'den kalan kesim frekansı hatası:**
     `interpolation_decimation.py` içinde
     `b_i = factor * fir1(64, (len(signal)/2) / (Fs_new/2))` —
     `len(signal)/2` yerine **`Fs/2`** olmalıydı. Kesim 25 kHz yerine
     2,5 kHz hesaplanıyordu. Hatanın şiddeti **sinyal uzunluğuna**
     bağlı: 0,01 s → 250 Hz (sinyali öldürür), 0,1 s → 2,5 kHz
     (%8 zayıflatır), 1,0 s → 25 kHz (tesadüfen doğru).

   **Kavramsal olarak pekiştirilenler:**
   - **Stopband tanımı** ve FIR/IIR'in bölgeye göre üstünlüğü: kesime
     yakında FIR ezici (4 kHz'te −53 vs −24 dB), uzakta Butterworth
     (24 dB/oktav ile durmadan iner). "Hangisi daha iyi" sorusunun
     cevabı hangi frekans bölgesinin önemli olduğuna bağlı.
   - **Katsayı başına performans:** 65 tap'e karşı 9 katsayı — FPGA'de
     her tap bir çarpma demek olduğu için bu oran donanım tasarım
     kararının kendisi.
   - **Sonlu vs sonsuz impuls cevabı görselleştirmesi:** transient
     zarfı log eksende çizilince FIR 65. örnekte uçurumdan düşüp
     1e−16'ya iniyor, IIR düz bir eğimle (üstel) sonsuza kadar
     azalıyor, `filtfilt` aynı eğimde ama iki kademe aşağıdan başlıyor.
   - **`filtfilt` transient'i yok etmez, kenarlara dağıtır** — sinyalin
     sonunda ~%7 sapma ölçüldü. Gerçek zamanlı sistemde "sinyalin sonu"
     olmadığı için kullanılamaz.
   - **`resample` vs elle FIR interpolasyonu:** ham fark gücü 1,31
     çıktı ama bunun %99,8'i grup gecikmesinden (32 örnek = 115° faz).
     Hizalandıktan sonra 3e−3, kesim hatası da düzeltilince 6,6e−7.
     **MSE hizalamaya aşırı duyarlıdır — karşılaştırmadan önce hizala.**
   - **Welch `nperseg` takası:** 256 → çok ortalama, pürüzsüz ama kaba;
     4096 → ince çözünürlük, dalgalı taban. Δf = 1/T_parça.

3. **Bonus — BPSK + BER vs SNR (`week4_bpsk.py`):** Tamamlandı.
   Bit üretimi → `np.repeat` ile dikdörtgen NRZ darbe → `add_awgn` →
   uyumlu filtre (sembol başına m örneğin ortalaması) → işaret kararı →
   BER. Ölçüm teorik `0.5·erfc(√(Eb/N0))` eğrisiyle üç ondalık mertebe
   boyunca çakıştı.

   **Kritik dönüşüm:** `add_awgn`'in SNR tanımı ile Eb/N0 aynı şey
   değil — **Eb/N0 = m·SNR/2**, m = 8 için +6 dB kaydırma. Atlanırsa
   eğri paralel ama ayrık çıkar.

   **Uyumlu filtre kazancı:** sembol başına m örneği toplamak, tek
   örnek almaya göre m kat (8 için 9 dB) kazanç sağlıyor — sinyal
   tutarlı toplanır (güç m²), gürültü bağımsız toplanır (güç m).
   Hafta 3'teki işleme kazancının zaman domenindeki karşılığı.

   **Ölçüm istatistiği dersi:** yüksek SNR'da ölçümün teoriden sapması
   hata değil. BER tahmininin göreli belirsizliği ≈ 1/√k (k = toplanan
   hata sayısı): −8 dB'de 26016 hata → %0,6; +2 dB'de 37 hata → %16,4.
   Farklı seed'lerle yayılma sırasıyla %1 ve %30 ölçüldü.
   **Profesyonel pratik:** sabit bit sayısı yerine sabit hata hedefi
   (nokta başına ~100 hata) ile simüle etmek.

---

## Hafta 5 — Profesyonel Python Alışkanlıkları ⏳ Sırada

**Konular:** paket yapısı (`__init__.py`), `pytest` ile birim test,
`pytest.approx` ve `np.testing`, `parametrize`, `fixture`, tekrarlanabilir
rastgelelik (`default_rng(seed)`), temel OOP.

> Pytest burada özellikle önemli, çünkü VUnit'in test mantığına zihinsel
> hazırlık sağlıyor. Ayrıca Hafta 2–4'te bulduğumuz hataların **çoğu**
> tek satırlık assert'lerle yakalanabilirdi — bu haftanın motivasyonu
> doğrudan o hata listesi.

**Görev 5:** Detaylar `hafta5_gorev5_pytest.md` dosyasında.

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
- **Spyder IDE**, MATLAB arayüzüne benzer; uzun vadede **VS Code**'a
  geçmek önerilir — VUnit projelerinde daha rahat çalışılır.
- Her hafta sonunda kod + kısa notlar paylaşılıp birlikte gözden
  geçiriliyor.

### Tekrar eden hata kalıpları (4 hafta boyunca biriken)

1. **İsim gölgeleme** — parametre adlarını import edilen modül adlarıyla
   çakıştırmamak (`signal`, `filter`, `welch`, `group_delay`).
2. **Örnek sayısı ≠ örnekleme hızı** — `len(x)` ile `Fs` karıştırıldığında
   hata sessiz kalıyor ve **girdinin uzunluğuna göre** bazen doğru bazen
   yanlış sonuç veriyor. Bu program boyunca **üç kez** karşımıza çıktı.
3. **Pozisyonel argüman kayması** — imzanın ortasına parametre eklemek
   mevcut çağrıları sessizce bozar. İki taraflı sıra hatası Python'da
   neredeyse hiç hata mesajı üretmez. **Kural: ikiden fazla parametreli
   kendi fonksiyonlarını anahtar kelimeyle çağır.**
4. **Birim çevirisi** — ms/µs, örnek/saniye. 640 µs yerine 66 ms yazmak
   gerçek bir link bütçesini batırır. Çeviri zincirini açık yaz.
5. **Dizi vs skaler** — `if dizi > 0` MATLAB refleksi;
   NumPy'da eleman bazlı maske kullanılır.
6. **Karşılaştırmadan önce hizala** — MSE/fark metrikleri gecikmeye
   aşırı duyarlı.
7. **Zaman tabanı kontrolü** — iki sinyali karşılaştırmadan önce
   refleks olarak `len()` ve `Fs` değerlerini yan yana koy.
