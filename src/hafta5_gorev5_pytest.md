# Hafta 5 — Görev 5: Paket Yapısı, pytest ve Test Edilebilir Kod

## Hedef

Dört haftadır biriken DSP fonksiyonlarını dağınık script'lerden **paket**
haline getirmek ve her birine otomatik test yazmak.

Motivasyon soyut değil: Hafta 2–4'te bulduğumuz hataların çoğu tek
satırlık bir `assert` ile anında yakalanırdı. Örnekler:

| Hata | Yakalayacak test |
|---|---|
| `apply_filter` sıra hatası → 65 elemanlı çöp | `len(çıkış) == len(giriş)` |
| `interpolate` kesim frekansı `len(signal)`'a bağlı | aynı sinyali iki farklı sürede ver, çıkış genliği aynı olmalı |
| `freqz`'e `a` eklenince pozisyonel çağrıların bozulması | bilinen bir filtre için −6 dB noktası ~2 kHz olmalı |
| FFT normalizasyonunun unutulması | tek tonlu sinyalin tepe genliği ~A/2 olmalı |

Bu haftanın sonunda o hataların hiçbiri sessiz kalamayacak. Ayrıca
pytest'in mantığı (test keşfi, assert, fixture, parametrize) doğrudan
Hafta 6'daki VUnit yapısına eşleniyor.

## Kurulum

```bash
pip install pytest
pytest --version
```

## Bölüm 1 — Isınma

**Önce tahmin et, sonra çalıştır:**

1. `assert 0.1 + 0.2 == 0.3` — geçer mi, kalır mı? Neden? Kalıyorsa
   doğru yazım nedir?
2. `assert np.array([1, 2]) == np.array([1, 2])` — ne olur?
   (İpucu: Hafta 4'te `if karar > 0` ile aynı aile.)
3. pytest bir fonksiyonu test olarak **hangi kurallara göre** bulur?
   Dosya adı, fonksiyon adı, klasör — hangisi zorunlu?
4. `add_awgn`'e test yazacaksın. Fonksiyon içinde rastgele sayı
   üretiliyor. Test her koşuda aynı sonucu versin diye ne yapman
   gerekir, ve bunu fonksiyonu **değiştirmeden** yapabilir misin?
5. Bir testin adı `test_filter_uzunlugu` mu olmalı yoksa
   `test_lfilter_cikis_uzunlugu_girise_esit` mi? Neden?

> ⚠️ **Kritik fark:** Float karşılaştırmasında `==` kullanmak neredeyse
> her zaman hatadır. Skalerde `pytest.approx`, dizide
> `np.testing.assert_allclose` kullanılır. `assert_allclose`'un
> `rtol`/`atol` ayrımını öğren — DSP'de sıfıra yakın değerler için
> `atol` şart, yoksa `rtol` anlamsızlaşır.

## Bölüm 2 — Ana Görev: Paket Yapısı

Şu an her şey yan yana duran script'ler halinde. Bunu bir pakete taşı:

```
proje/
├── dsp/
│   ├── __init__.py
│   ├── signals.py      # sine_wave, add_awgn
│   ├── filters.py      # fir1, butter, apply_filter, apply_filtfilt
│   ├── analysis.py     # fft, measure_delay, snr_olc
│   └── resampling.py   # up_sample, down_sample, interpolate, decimate
├── tests/
│   ├── test_signals.py
│   ├── test_filters.py
│   ├── test_analysis.py
│   └── test_resampling.py
└── week4.py            # artik sadece "kullanan" taraf
```

**Taşırken uyulacak kural:** çizim kodunu hesap kodundan ayır.
`plot_signal`, `plot_spectrum`, `welch` gibi fonksiyonlar `axes` alıp
çizim yapıyor — bunlar `dsp/plotting.py`'ye gitsin ve **test edilmesin**.
Test edilecek olan, sayı döndüren fonksiyonlar. Hafta 4'te `freqz`'i
"hesapla, çiz, döndür" diye ayırırken bu ilkeye zaten yaklaşmıştın;
şimdi tamamla: `freqz` iki fonksiyona bölünsün — biri `w, h` hesaplayıp
döndürsün, diğeri onu çizsin.

## Bölüm 3 — Testleri Yaz

En az şu testleri yaz. Her biri geçmiş bir hataya karşılık geliyor:

**`test_filters.py`**
1. FIR çıkışının uzunluğu girişe eşit (`lfilter` sıra hatası).
2. `fir1(64, Wn)` **65** katsayı döndürür (tek sayıya yuvarlama).
3. Lineer fazlı FIR'ın grup gecikmesi `(len(h)-1)/2` — `measure_delay`
   ile ölç, tam sayı eşitliği bekle.
4. `filtfilt` gecikmesi 0.
5. Bant dışı bir ton (örn. 10 kHz) filtreden geçince gücü en az 40 dB
   düşer; bant içi ton (1 kHz) ise en fazla 1 dB kaybeder.

**`test_resampling.py`**

6. `up_sample(x, 2)` uzunluğu `2*len(x)`, tek indisler sıfır.
7. `interpolate` çıkışının genliği girişinkiyle aynı (±%1) —
   *`m` ile genlik telafisi doğru mu?*
8. **Uzunluk bağımsızlığı testi:** aynı 1 kHz sinüsü 0,01 s ve 0,1 s
   süreyle üret, ikisini de `interpolate(x, Fs, 2)`'den geçir, çıkış
   genlikleri aynı olmalı. *Bu test Hafta 2'den kalan kesim frekansı
   hatasını yakalar — önce hatalı kodla çalıştırıp testin
   **kaldığını** gör, sonra düzelt ve **geçtiğini** gör.*
9. `decimate` çıkış uzunluğu `len(x)//K`.

**`test_signals.py`**

10. `sine_wave` uzunluğu `int(Fs*T)`, tepe genliği 1, ortalaması ~0.
11. `add_awgn(x, snr_db)` ölçülen SNR'ı hedefe ±0,5 dB yaklaşır
    (tekrarlanabilirlik için seed gerekli — Isınma-4'ün cevabı burada
    işe yarayacak).
12. `add_awgn(x, 0)` ile gürültü gücü sinyal gücüne eşit (±%5).

**`test_analysis.py`**

13. Tek tonlu sinyalin FFT'sinde tepe **doğru bin**'de (Δf = Fs/N
    kuralı) ve genliği ~A/2.
14. Parseval: zaman domeni gücü ile frekans domeni gücü eşit.

### Kullanman istenen pytest özellikleri

- **`pytest.approx`** — skaler float karşılaştırmaları.
- **`np.testing.assert_allclose`** — dizi karşılaştırmaları.
- **`@pytest.mark.parametrize`** — aynı testi farklı SNR / farklı `m` /
  farklı filtre derecesi ile koştur. En az iki testte kullan.
- **`fixture`** — tekrar eden test sinyalini (1 kHz, 50 kHz, 0,1 s) her
  testte yeniden üretme; bir fixture yaz ve `conftest.py`'ye koy.
- **`pytest.raises`** — hatalı girdide fonksiyonun düzgün hata vermesini
  test et (örn. `Wn >= 1` verilince `ValueError`).

Çalıştırma:

```bash
pytest -v                    # hepsi, detayli
pytest tests/test_filters.py # tek dosya
pytest -k "delay"            # adinda 'delay' gecen testler
pytest -x                    # ilk hatada dur
```

## Bölüm 4 — Temel OOP

Fonksiyonlar iyi çalışıyor ama her çağrıda `b`, `a`, `Fs` üçlüsünü
taşıyorsun. Bunu bir sınıfa topla:

```python
class LowPassFilter:
    def __init__(self, cutoff_hz, fs, order=4, kind="iir"): ...
    def apply(self, x): ...            # lfilter
    def apply_zero_phase(self, x): ...  # filtfilt
    @property
    def group_delay_samples(self): ...
    def response(self, worN=1024): ...  # w, h döndürür (çizmez)
```

Sonra `test_filters.py`'deki testlerin bir kısmını bu sınıf üzerinden
tekrar yaz. Amaç OOP'yi derinlemesine öğrenmek değil — **durumu
(state) bir arada tutmanın** ne kazandırdığını görmek. Hafta 6'da
VUnit'te benzer bir yapı göreceksin.

> MATLAB'dan gelen not: burada `classdef`'in Python karşılığını
> öğreniyorsun ama Python'da `self`'in **açıkça** ilk parametre olarak
> yazıldığına dikkat et — MATLAB'daki gizli `obj` değil.

## Bonus

1. **Kapsam ölçümü:** `pip install pytest-cov`, sonra
   `pytest --cov=dsp --cov-report=term-missing`. Hangi satırlar hiç
   test edilmemiş? Genelde en çok hata orada saklanır.
2. **Regresyon testi:** Hafta 4'te ölçtüğün değerleri (FIR gecikmesi 32,
   SNR iyileşmesi ~11 dB) test olarak sabitle. İleride kodu
   değiştirdiğinde bu sayılar kayarsa test seni uyarır — VUnit'te
   yapacağın şeyin aynısı.
3. **`pytest.ini`** dosyası ekleyip varsayılan seçenekleri
   (`-v`, `--strict-markers`) sabitle.

## Teslim

- Isınma tahminleri ve gerçek sonuçlar
- Paket yapısı (klasör ağacı + `__init__.py` içerikleri)
- `tests/` altındaki test dosyaları
- `pytest -v` çıktısı (kaç test geçti/kaldı)
- **Özellikle 8 numaralı test:** hatalı kodla kalıp düzeltilmiş kodla
  geçtiğini gösteren iki çıktı
- `LowPassFilter` sınıfı ve onu kullanan testler

Takıldığın yerde takıldığın haliyle gönder — hata mesajıyla birlikte
gelirsen daha da iyi. 🚀
