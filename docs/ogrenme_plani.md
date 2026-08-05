# Python Öğrenme Planı — MATLAB'dan Python/NumPy'a Geçiş

## Genel Hedef

MATLAB'da alışkın olunan matris/vektör işlemlerini Python + NumPy ile
yapabilmek, telekomünikasyon temalı DSP işlemlerini Python'da tekrar
üretebilmek ve sonunda VUnit ile profesyonel VHDL testbench'leri
kurabilecek Python altyapısına sahip olmak.

**Sıra:** Python temelleri → NumPy → Matplotlib → SciPy (DSP) →
profesyonel alışkanlıklar (pytest, modüler kod) → VUnit.

**Durum: ✅ Tamamlandı (6/6 hafta).**

---

## Seviye Tespiti (yapıldı)

Program başında kısa bir quiz + mini kod görevi ile mevcut seviye
ölçüldü. Sonuç: **kod yazma pratiği teorik bilginin önündeydi.**

- Güçlü: fonksiyonlara bölme, docstring alışkanlığı, f-string,
  `if __name__ == "__main__"`, pip/venv kavramı.
- Boşluklar: slicing kuralları (bitiş dahil değil), dict mantığı,
  list/tuple farkı, list comprehension, dosya okuma/yazma.

Bu yüzden Hafta 1, sıfırdan anlatım yerine sadece bu boşluklara
odaklanacak şekilde daraltıldı.

---

## Hafta 1 — Python Temelleri (MATLAB Gözlüğüyle) ✅

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

## Hafta 2 — NumPy: MATLAB'ın Python'daki Karşılığı ✅

**Konular:** `np.array`, `zeros`, `ones`, `linspace`, `arange`, slicing,
broadcasting, matris çarpımı (`@` vs eleman bazlı `*` — MATLAB'ın tam
tersi), `A.T`.

**Görev 2 — MATLAB kodunu NumPy'a çevir:**

1. **Isınma:** Tahminlerin 5'te 3'ü ilk seferde doğruydu. İki kritik
   yanılgı düzeltildi: `linspace(0,1,5)` adım sayısını `N` değil `N-1`
   böler (`endpoint` mantığı); `A*B`/`A@B` MATLAB'ın tam tersi yönde
   karıştırılmıştı.
2. **Asıl görev — `assiment.m`'in tam çevirisi:** `sine_wave`,
   `plot_signal`, `fir1`, `freqz`, `fft`, `fir_filter`, `plot_spectrum`
   fonksiyonlarından oluşan modüler bir yapı (`matlab_example.py`)
   kuruldu; upsample/downsample ayrı bir dosyada
   (`interpolation_decimation.py`) tamamlandı.

   **Yolda bulunup düzeltilen gerçek hatalar:**
   - `list + list` toplama değil **birleştirme** yapıyor.
   - `plt.subplots(2,2)` unpacking hatası — `axs[satır, sütun]` gerekiyor.
   - **İsim gölgeleme:** parametreyi `signal` diye adlandırmak
     `import scipy.signal as signal` modülünü gölgeliyor.
   - FFT genlik normalizasyonu eksikti (MATLAB'daki `/L` adımı).
   - `len(signal)` ile gerçek örnekleme hızı `Fs` karıştırılmıştı.
     *(Bu düzeltme eksik kaldı, Hafta 4'te ortaya çıktı.)*
   - `decimate()`'de filtrelenmiş ama downsample edilmemiş sinyal yanlış
     örnekleme hızıyla çizdiriliyordu.

   **Kavramsal olarak pekiştirilenler:** `-6 dB` kesim noktasını
   interpolasyonla bulup grafikte işaretleme; upsample sonrası oluşan
   *image*'in bastırılmasının sayısal doğrulaması; **aliasing**'in somut
   örnekle gösterilmesi (filtresiz downsample'da 15 kHz'in 10 kHz'e
   katlanması) — "önce filtrele, sonra downsample" kuralı buradan çıktı.
3. **Bonus (`np.loadtxt`):** Yapılmadı.

---

## Hafta 3 — Matplotlib + Sinyal Üretimi ✅

**Konular:** `np.random.normal` ile AWGN üretimi, güç/SNR hesabı
(teorik vs ölçülen), `stem`, log eksenler, tek yanlı spektrum.

**Görev 3 — Gürültülü sinyal ve SNR analizi:**

1. **Isınma:** 3'te 2 doğru. Düzeltilen yanılgı: `np.random.normal`'ın
   `scale` parametresi **standart sapma**dır, varyans değil.

2. **Ana görev (`week3.py`):** `add_awgn(signal, snr_db)` yazıldı,
   ölçülen SNR hedefle karşılaştırıldı (~10 dB ✓). Bonus 1: SNR =
   0/10/20 dB için `stem`. Bonus 2: `plot_spectrum`'a `xscale`.

   **Yolda bulunup düzeltilen hatalar:**
   - `ax.title()` — `title` metot değil `Text` nesnesi.
   - `axes` alan fonksiyonda `plt.stem` kullanımı — çizim aktif eksene
     gitti. **Kural:** fonksiyona `axes` veriliyorsa içeride `plt.` yok.
   - `len(f)/2` — `/` float döndürür, dilim tamsayı ister; `//` gerekir.
   - fftshift'li dizide `[:N//2]` **negatif** frekansları seçer.
   - `label`'ın `plot(...)`'a değil `set_label()`'a verilmesi.

   **Kavramsal olarak pekiştirilenler:** Sinüs gücü = A²/2; dB↔lineer
   dönüşüm zinciri; **işleme kazancı** (~10·log₁₀(N) dB); **frekans
   çözünürlüğü Δf = 1/T** — süreden gelir, örnekleme hızından değil.

---

## Hafta 4 — SciPy ile Telekom/DSP İşlemleri ✅

**Konular:** `butter`, `filtfilt`, `welch`, `resample`,
`correlate`/`correlation_lags`, `group_delay`.

**Görev 4 — FIR vs IIR karşılaştırması (`week4.py`, `week4_bpsk.py`):**

1. **Isınma:** 4'te ~1,5 doğru; yanlışların hepsi haftanın hedef
   konularındaydı. Düzeltilenler: `butter(4, ...)` **5'er** katsayı
   döner; grup gecikmesi **(tap−1)/2 = 32 örnek** ve 32 örnek @ 50 kHz =
   **640 µs** (birim çevirisinde 100 kat sapma yapılmıştı); `filtfilt`
   genlik cevabının **karesini** alır; ham periodogram Welch'ten
   **yüksek** varyanslıdır.

2. **Ana görev — ölçülen sonuçlar:**

   | | SNR (çıkış) | Gecikme | Sinyal kaybı | Oturma |
   |---|---|---|---|---|
   | FIR `lfilter` | ~11,2 dB | 32 örnek | −0,3 dB | ~48. örnek |
   | IIR `lfilter` | ~10,6 dB | 11 örnek | −0,02 dB | ~37. örnek |
   | IIR `filtfilt` | ~10,9 dB | 0 örnek | −0,03 dB | ~7. örnek |

   Beklenen iyileşme 10·log₁₀(25/2) ≈ 11 dB — ölçüm tuttu.

   **Yolda bulunup düzeltilen hatalar:**
   - **`freqz` sarmalayıcısına `a` eklenmesi** — imzanın ortasına
     parametre eklemek pozisyonel çağrıları sessizce bozdu.
   - **`apply_filter` çağrı sırası** — `filtfilt` hata verdi ama iki
     `lfilter` çağrısı **sessizce çöp döndürdü**.
   - **SNR ölçümünde superposition eksikliği.**
   - **Korelasyonda periyodiklik belirsizliği** (32 ≡ −18, mod 50).
   - **Transient ölçümünde gürültülü sinyal kullanımı.**
   - **`measure_delay`'in farklı örnekleme hızlarıyla çağrılması.**
   - **Hafta 2'den kalan kesim frekansı hatası:** `len(signal)/2` yerine
     **`Fs/2`** olmalıydı. Hatanın şiddeti sinyal uzunluğuna bağlıydı:
     0,01 s → 250 Hz, 0,1 s → 2,5 kHz, 1,0 s → 25 kHz (tesadüfen doğru).

   **Kavramsal olarak pekiştirilenler:** stopband tanımı ve FIR/IIR'in
   bölgeye göre üstünlüğü; **katsayı başına performans** (65 tap'e karşı
   9 katsayı — FPGA'de her tap bir çarpma); sonlu vs sonsuz impuls cevabı;
   `filtfilt` transient'i kenarlara dağıtır; **MSE hizalamaya aşırı
   duyarlıdır**; Welch `nperseg` takası.

3. **Bonus — BPSK + BER vs SNR:** Tamamlandı, ölçüm teorik
   `0.5·erfc(√(Eb/N0))` ile üç ondalık mertebe boyunca çakıştı.
   **Kritik dönüşüm:** Eb/N0 = m·SNR/2. **Uyumlu filtre kazancı:** m kat.
   **Ölçüm istatistiği:** BER belirsizliği ≈ 1/√k; sabit bit sayısı
   yerine sabit hata hedefi (nokta başına ~100 hata) ile simüle et.

---

## Hafta 5 — Profesyonel Python Alışkanlıkları ✅

**Konular:** paket yapısı, `pytest`, `pytest.approx`, `np.testing`,
`parametrize`, `fixture`, `pytest.raises`, `default_rng`, `dataclass`,
temel OOP, `pytest-cov`.

1. **Isınma:** 5'te 5 doğru istikamet, ikisi yarımdı. Ortaya çıkan zihin
   modeli düzeltmesi: seed bir "değer" değil, **global bir imlecin
   başlangıç noktası**.

2. **Paket yapısı (`dsp/`):** `signals.py`, `filters.py`, `analysis.py`,
   `resampling.py`, `plotting.py` + açık listeli `__init__.py`.
   `freqz` üçe bölündü: `frequency_response` / `find_cutoff` /
   `plot_frequency_response`. Kontrol sorusu: *"bu çizim fonksiyonunu
   silsem hangi sayı kaybolur?"* → "hiçbiri" olmalı.

3. **Test seti (~30 test):** Kapsam `plotting.py` dışında **%100**.
   **Kırmızı-yeşil döngüsü fiilen yaşandı** (`interpolate` kesim
   frekansı hatası: RMS 0,506 vs 0,653 → düzeltme → geçti).

   **Yolda bulunup düzeltilen gerçek hatalar:** `import *` sızıntısı;
   `len(b) - 1 // 2` operatör önceliği; `order=64` ile IIR'in sayısal
   çöküşü; **hiçbir şey ölçmeyen iki test**; `assert assert_allclose(...)`
   (`None` döndürür); `Wn`'in `Fs`'e göre normalize edilmesi; işaret yönü
   ters `zayiflatma_db <= 1`; `fft()` tuple'ının tek değişkene atanması;
   Parseval'de fazladan `/N`; `decimate` uzunluğunda `ceil` vs `//`;
   Butterworth kesiminin −3 dB olması; `argmax`'ın fftshift'li dizide
   negatif frekansı seçmesi *(bu tespit eren tarafından yapıldı)*.

4. **Tasarım kararları:** `add_awgn(..., rng=None)` — gizli çıktı
   yaratmamak; `InterpolationResult` dataclass'ı; `LowPassFilter` sınıfı
   ve `group_delay_samples` (FIR) ile `group_delay_at(freq_hz)` (IIR)
   ayrımı.

---

## Hafta 6 — VUnit ile VHDL Testbench (Final Projesi) ✅

**Konular:** NVC simülatörü, VUnit kurulumu, `run.py` yapısı, `check`
kütüphanesi, `add_config`, `post_check`, CSV ile Python↔VHDL veri
alışverişi, Q1.15 sabit noktalı aritmetik, CI.

### 1. Isınma — 5'te 4 tam

Doğru bilinenler: bit genişliği ve indeksleme yönü; Q1.15 çevrim
formülü (`float × 2¹⁵`, ters yönde `/2¹⁵`); Q1.15 × Q1.15 = Q2.30 ve
guard bitinin 1 olması; `check`'in yükselen kenarda yapılması ve
setup/hold ile delta cycle ayrımı *(bu cevap VHDL tarafında acemi
olunmadığını gösterdi)*.

**Düzeltilen:** Hiç `check` çağırmayan bir testbench VUnit'te **PASS**
sayılır — `test_runner_cleanup`'a hatasız ulaşmak yeterlidir. Hafta 5'teki
"hiçbir şey ölçmeyen test" tuzağının donanım hali.

**Eklenen:** Guard bit sayısı tap sayısından değil **katsayıların mutlak
toplamından** türetilir: `max|acc| ≤ max|x| · Σ|h|`. Ölçüm 17 tap / 2 kHz
için `Σ|h| = 1,0` verdi (bütün katsayılar pozitif); 65 tap'te 1,24'e
çıkıyor. "log₂(65) ≈ 7 bit" refleksi 8 kat fazla kaynak isterdi.

### 2. Sayaç — VUnit mekaniği

Üç isimli test (`reset_sayaci_sifirlar`, `enable_dusukken_sayac_durur`,
`maksimumda_tick_uretir`) yazıldı, kırmızı-yeşil döngüsü uygulandı.

**Yolda bulunup düzeltilen hatalar:**
- `to_unsigned(2**32-1, 32)` — ara hesap **VHDL integer'ında** yapılıyor,
  üst sınır 2³¹−1. Genişlikten bağımsız yazım `(others => '1')`.
- **Sensitivity list'siz process başa döner:** `rst <= '0'` atandıktan
  sonra process yukarı sarıp `rst <= '1'` yazıyordu; aynı delta'da son
  atama kazanır → reset hiç düşmedi. Python'da karşılığı olmayan bir hata
  sınıfı.
- Testbench'te `test_runner_setup`/`test_suite`/`run()` yapısı hiç yoktu;
  VUnit her şeyi tek anonim test (`.all`) saydı.
- `ena = '0'` sayacı sıfırlıyordu — şartname "durur" diyor. **Durmak ile
  sıfırlanmak aynı şey değil.**
- C_DATA_WIDTH = 32 ile sayaç 2³² çevrimde taşar; testbench'te küçük
  genişlik (4 bit) kullanılmalı. Parametrik tasarımın amacı bu.
- `wait until MAX_COUNT = count_out` — **sonsuz döngü.** Mutasyon sayacı
  14'te sardırınca çıkış koşulu hiç sağlanmadı ve watchdog'a düşüldü.
  Ders: **zaman referansı DUT'un çıkışından değil şartnameden gelmeli.**

**Zamanlama dersi:** `tick <= '1'` ile `count <= 0` aynı kenarda
planlanıyor; `count_out` 15 okurken `tick` hâlâ '0', bir sonraki çevrimde
`count_out` 0 ve `tick` '1'. **Doğru değer, yanlış çevrim** — haftanın
merkez kavramı.

### 3. FIR filtre — beş haftanın birleşmesi

**3.1 Vektör üretimi (`generate_vectors.py`):**

- Q1.15 çevrimi, doygunluk ve taşma kontrolü.
- İki tonlu giriş Q1.15'e sığmıyordu (genlik 2) → tonlar 0,4 ile
  ölçeklendi. *Ölçeksiz tepe 1,9333 çıktı, tam 2,0 değil — tepeler örnek
  ızgarasında çakışmıyor (Hafta 5'teki sinüs tepesi dersi).*
- **Beklenen çıkış dekuantize değerlerden hesaplandı.** Katsayı ve giriş
  kuantizasyonu iki tarafta da aynı olduğu için karşılaştırma
  **bit-birebir** yapılabildi; tolerans 0.

  | Referans | Tamsayı modelden sapma |
  |---|---|
  | Saf float | 1 LSB |
  | **Dekuantize** | **0 LSB** |

- `np.array2string` **CSV değildir** — ekran için string üretir, uzun
  dizileri `...` ile kırpar. `np.savetxt(..., fmt='%d')` gerekiyordu.
- Ölçek seçimi 2¹⁵ (32768), 32767 değil: donanımda 15 bit sağa kaydırma
  2¹⁵'e bölmektir; 32767 ile kodlamak ~3·10⁻⁵ sistematik kazanç farkı
  bırakırdı.
- **Üreteç idempotent yapıldı** (`write_if_changed`): aynı içerikle
  yeniden yazmak mtime'ı ilerletiyor ve NVC "derlenmiş birim kaynaktan
  eski" uyarısı veriyordu. VUnit içeriğe, NVC zaman damgasına bakıyor.
- Katsayılar `fir_coeffs_pkg.vhd` olarak **üretiliyor** — CSV ile VHDL'in
  ayrışması imkânsız hale geldi.

**3.2 `fir_filter.vhd` — transpoze yapı:**

- Transpoze seçildi (kritik yol bir çarpma + bir toplama). Python'da
  birebir modellenip `np.convolve` ile doğrulandı; pipeline gecikmesi
  **1 çevrim** ve `valid_q <= valid_in` ile tam hizalı.
- **Kırpma negatif bias verir**, pozitif değil: iki'nin tümleyeninde alt
  bitleri atmak *floor*'dur. Ölçüm: kırpma −0,48 LSB, yuvarlama
  −0,0005 LSB. *(Gerekçe başlangıçta ters biliniyordu.)*
- Yuvarlama iki yeni taşma riski yaratıyor: toplamanın kendisi (bir bit
  geniş çalışılarak çözüldü) ve dilimin işaret bitini atması (doygunlukla
  çözüldü). Python `np.clip` ile doyuyordu, VHDL sarıyordu — **iki model
  kenar durumda ayrışıyordu.**
- Elaborasyon zamanı assert: `Σ|h| < 2^(MULT_WIDTH − DATA_WIDTH)`.
  Eşitsizlik bu biçimde yazılmalı, çünkü `2^(MULT_WIDTH−1)` VHDL
  integer'ına sığmaz. Python'daki `check_accumulator_width` ile aynı iddia.
- `acc_reg`/`valid_q` başlangıç değeri verildi → `NUMERIC_STD."="
  metavalue` uyarıları 2'den 0'a indi.

**3.3 Testbench — 3 test, bit-birebir:**

- `feed_range` / `drain` / `check_next_output` prosedürleriyle tekrar
  kaldırıldı; prosedürler process değişkenlerine erişiyor.
- **`check_equal(compared, length(expected_data))`** — testin gerçekten
  ölçtüğünün tek kanıtı. Reset sınırında bir örnek yutulduğunda bunu
  yalnızca o satır yakalayabiliyordu.
- Reset sırasında `valid_in` düşük tutulmalı, reset bırakıldıktan sonra
  bir boş çevrim beklenmeli — yoksa ilk örnek yutuluyor.
- `check_equal`'ın `max_diff` parametresi **yalnızca `real` tipinde** var;
  tamsayıda tolerans elle yazılır. *(Görev dosyasındaki örnek yanlıştı.)*
- Sinyal (`<=`) vs değişken (`:=`): `count_pre <= count_out` sonrası aynı
  satırda okumak **eski** değeri verir. Anlık kopya için `variable` şart.
- İzleyici process **düşen kenara** taşındı: süren ve ölçen kod aynı
  zaman adımını paylaşmamalı.
- Üçüncü test (`tam_olcek_dc_de_doyar`) doygunluk dalını çalıştırıyor.
  Doygunluk kaldırıldığında `Got -32768. Expected 32767.` — sarmanın
  imzası. Diğer iki test bu mutasyonda **geçmeye devam etti**.

**3.4 Doğrulama zinciri — `post_check`:**

- Testbench çıktıyı `output_path(runner_cfg)` altına yazıyor, Python
  spektrumu alıyor. `assert` patlarsa VUnit testi temiz şekilde `fail`
  sayıyor ve traceback'i basıyor.
- **Toplam RMS oranı bu iş için ölçüm aracı değil.** İki tonlu sinyalde
  −3,62 dB ölçüldü ve bu sayı, mükemmel bir filtrede bile −3,01 dB'nin
  altına inemez (geçen ton payı duruyor). `<= -40 dB` iddiası hiçbir
  filtreyle sağlanamazdı.
- Çözüm: `tone_amplitude(x, fs, tone_hz)` ilkeli (`2|X[k]|/N`) + üzerine
  kurulu `suppression_db(y, x, fs, tone_hz)`.
- **Koherent örnekleme:** ton tam bin merkezine düşmeli. 500 örnekte
  1 kHz → bin 10 ✓, ama transient için 17 örnek atınca N = 483 ve bin
  9,66 → sızıntı. Pencere **tam periyot sayısı** olacak şekilde seçildi
  (100 atla, 400 ölç).
- Ölçüm fonksiyonu `dsp/analysis.py`'ye kondu ve **kendisine 17 pytest
  testi yazıldı** — doğrulama aletinin kendisi doğrulanmadan ölçüme
  güvenilemez. Test yazarken gerçek bir hata bulundu: `amp_in == 0.0`
  karşılaştırması, FFT yuvarlama artığı (~1e−16) yüzünden hiç tutmuyor ve
  fonksiyon +250 dB gibi anlamsız bir sayı döndürüyordu. Eşik sinyalin
  kendi ölçeğine göre kondu.
- **İki bağımsız iddia:** (1) donanım float referansla aynı mı
  (`abs=0,2 dB`, ölçülen sapma 0,009 dB), (2) sonuç şartnameyi sağlıyor mu
  (`stopband ≤ −40 dB`, `passband ≥ −1 dB`). İlki tek başına **kapalı
  devre**dir.

### 4. Bonuslar ✅

**Bonus 1 — `add_config` (parametrize'ın VUnit karşılığı):**

- **Dizi generic engeli:** `add_config` yalnızca skaler ve string
  geçirebiliyor; `COEFFS` elaborasyon sabiti olduğu için dosyadan da
  okunamıyor. Çözüm: bütün katsayı setleri tek pakete (en uzuna göre
  sıfırla doldurulmuş), Python yalnızca `config_id` gönderiyor.
- Entity'de `COEFFS : coef_array_type(0 to NUM_TAPS - 1)` — generic'in
  sonraki generic'e bağlanması entity'yi gerçekten parametrik yaptı.
- `post_check` konfigürasyona **kapanış (closure)** ile bağlandı.

  | config | tap | gecikme | passband | stopband |
  |---|---|---|---|---|
  | tap17 | 17 | 8 | −0,47 dB | −50,12 dB |
  | tap33 | 33 | 16 | −0,28 dB | −68,08 dB |
  | tap65 | 65 | 32 | +0,04 dB | −70,37 dB |

- **Her tap sayısı şartnameyi sağlamıyor.** 2 kHz kesimde 33 tap
  passband'de −1,26 dB veriyordu. Sebep Hamming geçiş bandı genişliği
  ≈ 3,3/N: 33 tap'te 5 kHz eder ve 1 kHz geçiş bölgesinin **içinde**
  kalır. Kesim 3 kHz'e taşındı — **test gevşetilmedi, tasarım düzeltildi.**
  `verify_spec` bunu artık üretim anında yakalıyor.
- DC doygunluk testinin kırılganlığı somutlaştı: tetikleyen tek şey
  katsayı yuvarlamasından gelen 1 LSB fazla DC kazancı. 3 kHz kesimde
  yalnızca 33 tap doyuyor. Üretece açık bir assert kondu.

**Bonus 2 — Kapsam:**

- Python: `pytest --cov=dsp --cov-report=term-missing`.
- VHDL: **VUnit'in NVC arayüzü kapsamı desteklemiyor**
  (`supports_coverage()` → `False`); GHDL'de gcov tabanlı destek var.
  NVC ile `nvc.elab_flags` üzerinden elle sürülebilir, birleştirme
  `post_run` kancasında yapılır.
- Asıl ders zaten yaşandı: doygunluk dalı derleniyordu, sentezlenirdi ve
  **hiçbir test onu çalıştırmıyordu.** Kapsam çalıştırılan satırı ölçer,
  doğrulanan davranışı değil.

**Bonus 3 — CI (GitHub Actions):**

- Adımlar: GHDL kur → bağımlılıklar → `generate_vectors.py` → `pytest`
  → `run.py`. **Sıra `.gitignore` yüzünden zorunlu:** üretilen dosyalar
  depoda yok.
- Geliştirmede NVC, CI'da GHDL → **iki simülatörde birden** doğrulama.
- `if: always()` ile simülasyon çıktıları artifact olarak yükleniyor;
  düşen bir testin log'unu okumanın tek yolu bu.
- Kapsam eşiği (`--cov-fail-under`) bilinçli olarak eklenmedi: kapsam
  kör nokta bulucudur, KPI değil.

---

## Pratik Notlar

- NumPy öğrenirken resmi **"NumPy for MATLAB users"** tablosunu yanında
  tut.
- **Spyder** MATLAB arayüzüne benzer; VUnit projelerinde **VS Code**
  daha rahat.
- **VHDL-LS kurulumu:** `vhdl_ls.toml` elle yazılmaz — dosya listesi
  `vu.get_compile_order()`'dan üretilir (`generate_vhdl_ls.py`). VUnit
  hangi VHDL-93/2002/2008 varyantını seçtiğini bilir; joker ile hepsini
  vermek çift tanım üretir. `vunit_lib` için `is_third_party = true`.
- **Üretilen dosyalar sürüm kontrolüne girmez:** `vhdl_ls.toml`,
  `vectors/`, `vunit_out/`, `hdl/src/fir_coeffs_pkg.vhd`. `.gitignore`
  yalnızca **takip edilmeyen** dosyalara etki eder; daha önce commit
  edilmişse `git rm --cached` gerekir. Sondaki `/` işareti deseni
  yalnızca dizinlere daraltır.
- **Çalıştırma sırası** (README'ye yazıldı):
  ```
  python generate_vectors.py   # katsayi paketi + test vektorleri
  python generate_vhdl_ls.py   # LSP icin dosya listesi
  pytest                       # Python testleri
  python run.py -v             # VHDL testleri
  ```
- **Git commit disiplini (Hafta 5'te acı deneyimle öğrenildi):**
  çalışır hale gelen her şey için commit at. Ölçüt: mesajda "ve" demek
  zorunda kalıyorsan commit ikiye bölünmeliydi. Mesaj formülü:
  *"Bu commit uygulandığında kod şunu yapacak: ___"*

### Tolerans seçim tablosu

Tolerans keyfi bir sayı değil, **hata kaynağından türetilir.**

| Hata kaynağı | Tolerans | Örnek |
|---|---|---|
| Float aritmetiği (özdeşlikler) | `rel=1e-9` … `1e-12` | Parseval |
| Sonlu örnekleme (istatistik) | √(2/N)'den hesapla | SNR ölçümü ~0,09 dB |
| Izgara çözünürlüğü | `abs = Δf` veya `2Δf` | FFT tepesi, kesim frekansı |
| Tamsayı yuvarlama | `abs=1` örnek | gecikme ölçümü |
| Atanmış (hesaplanmamış) değerler | tolerans **yok**, `==` | `up_sample` sıfırları |
| **Referans model bit-doğruysa** | **tolerans yok, `==`** | FIR çıkışı vs `expected.csv` |
| **Spektral ölçüm (donanım vs float)** | **`abs=0,2 dB`** | ölçülen sapma 0,009 dB |
| **Kuantizasyon (bit-doğru olmayan referans)** | `abs = 1–2 LSB` | kırpma/yuvarlama belirsizliği |

**Logaritmik birimlerde (dB) tolerans her zaman mutlaktır.** Beklenen
değer sıfıra yakınsa `rel × 0 = 0` → sıfır tolerans; bu tuzağa Hafta 5'te
**üç kez** düşüldü.

**Referans modelini donanımın gördüğü değerlerden kurarsan toleransı
sıfıra indirebilirsin.** Hafta 6'nın en verimli tek kararı buydu ve aynı
numara spektral ölçümde de işe yaradı: ölçüm yönteminin kendi sapması iki
tarafta da aynı olduğu için birbirini götürüyor.

### Tekrar eden hata kalıpları (6 hafta boyunca biriken)

1. **İsim gölgeleme** — parametre adlarını import edilen modül/yerleşik
   adlarla çakıştırma (`signal`, `filter`, `welch`, `input`).
2. **Örnek sayısı ≠ örnekleme hızı** — `len(x)` ile `Fs` karıştırıldığında
   hata sessiz kalır ve **girdinin uzunluğuna göre** bazen doğru sonuç
   verir. Program boyunca **üç kez** karşımıza çıktı.
3. **Pozisyonel argüman kayması** — imzanın ortasına parametre eklemek
   mevcut çağrıları sessizce bozar. **Kural: ikiden fazla parametreli
   kendi fonksiyonlarını anahtar kelimeyle çağır.**
4. **Birim çevirisi** — ms/µs, örnek/saniye, Q formatı ölçeği.
   640 µs yerine 66 ms yazmak gerçek bir link bütçesini batırır.
5. **Dizi vs skaler** — `if dizi > 0` MATLAB refleksi.
6. **Karşılaştırmadan önce hizala** — MSE/fark metrikleri gecikmeye aşırı
   duyarlı. *İstisna: genlik büyüklüğü fazdan bağımsızdır, spektral
   ölçümde hizalama gerekmez.*
7. **Zaman tabanı kontrolü** — iki sinyali karşılaştırmadan önce refleks
   olarak `len()` ve `Fs` değerlerini yan yana koy.
8. **`pytest.approx`'un ikinci pozisyonel argümanı `rel`'dir, `abs`
   değil.** Hafta 5'te **dört kez** yapıldı.
9. **Fonksiyonun ne döndürdüğünü kontrol etmemek** — `fft` tuple,
   `argmax` indeks, `assert_allclose` `None`, **`np.array2string` ekran
   string'i** döndürür. Refleks: `print(type(x), np.shape(x), x[:3])`.
10. **Operatör önceliği** — `len(b) - 1 // 2` ≠ `(len(b) - 1) // 2`.
11. **Hiçbir şey ölçmeyen test** — her assert'ten sonra sor: *"bu iddia
    hangi durumda kalır?"* Sadece **kaldığını gördüğün** bir test gerçekten
    bir şey ölçtüğünü kanıtlar.
12. **Test edilmeyen kod, çalıştığı varsayılan koddur.** Kapsam
    **çalıştırılan satırı** ölçer, doğrulanan davranışı değil.
13. **Bağımlılıkları imzaya taşı** — gizli girdi/çıktı test
    edilebilirliğin bir numaralı düşmanı. Bir fonksiyona test yazmak
    zorlaşıyorsa sebep genellikle **tasarımın** kendisidir.
14. **Sinyal (`<=`) vs değişken (`:=`)** — VHDL'de sinyal ataması process
    bir `wait`'e gelene kadar görünmez. Anlık kopya `variable` ister.
    Aynı delta'da iki atama varsa **son atama kazanır**.
15. **Doğru değer, yanlış çevrim** — donanımda bir iddia hem değeri hem
    zamanı içerir. "Kenardan sonra oku, kenardan sonra sür" gibi tek bir
    konvansiyon seç ve dosyanın başına yaz.
16. **Testbench'te sınırsız bekleme yazma** — her `loop` ve `wait until`
    bir üst sınır ve anlamlı bir mesaj taşımalı. Watchdog son savunma
    hattıdır, ilk savunma değil. Zaman referansın **şartnameden** gelsin,
    DUT'un çıkışından değil.
17. **Üretilen dosyaya elle dokunma** — mutasyon her zaman *gerçeğin
    kaynağına* uygulanır. Üreteç, elle yapılan değişikliği sessizce geri
    yazar.
18. **Kapalı devre doğrulama** — referans ile DUT aynı hatayı paylaşabilir.
    "Beklenen değere eşit mi?" sorusunun yanına mutlaka bağımsız bir
    "sonuç şartnameyi sağlıyor mu?" sorusu koy.
19. **Float'ı tam sıfırla karşılaştırma** — FFT'de bulunmayan bir
    frekansın genliği 0 değil ~1e−16'dır. Eşik sinyalin kendi ölçeğine
    göre konur.
20. **Koherent olmayan pencere** — spektral ölçümde ton tam bin merkezine
    düşmeli, yoksa sızıntı sonucu sessizce bozar. Pencere uzunluğunu
    tonun tam periyot sayısına eşitle.

---

## Program Kapanışı

Altı haftada gidilen yol: MATLAB scriptini NumPy'a çeviren birinden,
**Python'dan sürülen, iki simülatörde koşan, CI'a bağlı, kendi ölçüm
aletini de test eden bir VHDL doğrulama zinciri** kuran birine.

Son durumda çalışan sistem:

```
generate_vectors.py  ──► fir_coeffs_pkg.vhd  (katsayilar)
                     ──► vectors/*.csv        (giris, beklenen)
                     ──► configs.json         (manifest)
                              │
run.py ──► VUnit ──► NVC/GHDL ──► tb_fir_filter ──► check_equal (bit)
                                        │
                                   output.csv
                                        │
                              post_check ──► dsp/ ──► spektrum (dB)
```

**Sayılarla:** 5 VUnit testi (3 konfigürasyon), ~47 pytest testi, FIR
çıkışı Python referansıyla **bit-birebir**, stopband bastırması üç
konfigürasyonda −50/−68/−70 dB.

### Bundan sonra nereye

Sırayla değil, ihtiyaç doğdukça:

1. **AXI4-Stream** — `valid`/`ready` tam el sıkışması ve geri basınç.
   VUnit'in AXI doğrulama bileşenleri (VC) hazır geliyor. Isınma-4'te
   `tvalid`'den bahsetmiştin; sıradaki doğal adım bu.
2. **Xilinx IP simülasyonu** — ticari simülatör (Questa, Riviera-PRO)
   gerektiriyor. Ücretsiz **Questa Starter** ile tanışmak, gerçek ihtiyaç
   çıkınca lisanslamak makul. Ara strateji: IP yerine davranışsal model
   (BFM) + VUnit AXI VC'leri.
3. **Sabit noktalı tasarımı derinleştirme** — `ieee.fixed_pkg`
   (`sfixed`/`ufixed`) Q formatını tip sistemine taşır; ölçek hataları
   derleme zamanında yakalanır. Bu haftaki elle kaydırma/doygunluk
   işlerinin yerini alır.
4. **Kapsam ve rastgele doğrulama** — NVC kapsam raporunu VUnit
   akışına bağlamak; ileride kısıtlı rastgele uyaran (constrained random)
   ve tarama (scoreboard) kavramları.
5. **Sentez tarafı** — bu FIR şu ana kadar yalnızca simüle edildi.
   Zamanlama kapanışı, DSP48 eşlemesi ve kaynak raporu, "65 tap'e karşı
   9 katsayı" tartışmasını somut sayılara bağlar.