# Hafta 4 — Görev 4: SciPy ile IIR Filtreleme, filtfilt ve Welch

## Hedef

Hafta 2'de FIR tarafını (`firwin`, `lfilter`, `freqz`) zaten aktif
kullandın — bu hafta **yeni** araçlara odaklanıyoruz:

- `scipy.signal.butter` ile **IIR** filtre tasarımı ve FIR'dan farkı,
- `filtfilt` ile **sıfır-fazlı** filtreleme (Hafta 3'te açık bırakılan
  "FIR grup gecikmesi" sorusunun cevabı burada),
- `welch` ile güç spektral yoğunluğu (PSD) tahmini,
- `resample` — Hafta 2'de elle yazdığın `interpolate`/`decimate` ile
  karşılaştırma fırsatı.

Hafta 3'teki `add_awgn` fonksiyonun bu görevin ana malzemesi.

## Kurulum

Yeni paket yok — `scipy` zaten kurulu. Sadece yeni fonksiyonları import
edeceksin:

```python
from scipy.signal import butter, filtfilt, lfilter, welch, resample, group_delay
```

## Bölüm 1 — Isınma

Aşağıdakileri **önce kağıt üzerinde tahmin et**, sonra çalıştırıp doğrula:

1. `b, a = butter(4, 0.2)` çağrısından dönen `b` ve `a` dizilerinin
   uzunlukları kaçtır? Hafta 2'deki `fir1(64, Wn)`'de `a` neydi?
   (İpucu: IIR'de "geri besleme" var — `a`'nın 1'den uzun olması ne
   anlama geliyor?)
2. 64 tap'lik lineer fazlı bir FIR filtrenin grup gecikmesi kaç
   **örnek**tir? `Fs = 50 kHz`'de bu kaç **mikrosaniye** eder?
   (Hafta 2'deki `y_filt` ile `y1` grafiğini üst üste çizdiğinde
   gördüğün kaymanın açıklaması bu.)
3. `filtfilt(b, a, x)` sinyali ileri + geri yönde iki kez filtreler.
   Bu durumda (a) faz gecikmesi ne olur, (b) genlik cevabı tek geçişe
   göre nasıl değişir? (dB cinsinden düşün.)
4. Aynı gürültülü sinyalin spektrumunu bir kez ham `|FFT|²` ile, bir
   kez `welch` ile çizsen, hangisi daha "dalgalı" (yüksek varyanslı)
   görünür ve neden?

> ⚠️ **Kritik fark:** `lfilter(b, a, x)` **nedensel** çalışır — gerçek
> zamanlı bir sisteme koyabilirsin ama gecikme ve transient kaçınılmaz.
> `filtfilt` sıfır-fazlıdır ama sinyalin **tamamını** ister — sadece
> offline analizde kullanılabilir. Donanımda (FPGA'de) karşılığı yoktur;
> bu ayrım telekom işinde önemli.

## Bölüm 2 — Ana Görev: FIR vs IIR Karşılaştırması

Hafta 3'teki senaryoyu temel al: `fc = 1 kHz` sinüs, `Fs = 50 kHz`,
`add_awgn` ile **SNR = 0 dB** gürültü ekle (işleme kazancını en net
göreceğin durum).

1. **İki filtre tasarla**, ikisinin de kesim frekansı ~2 kHz olsun:
   - FIR: `firwin(65, Wn)` — Hafta 2'den bildiğin yöntem.
   - IIR: `butter(4, Wn)` — 4. derece Butterworth.
2. **Frekans cevaplarını aynı grafikte** çiz (`freqz` her ikisi için de
   çalışır — IIR'de `freqz(b, a, ...)` olarak). Karşılaştır:
   - 65 tap'e karşı sadece 9 katsayı (b+a) ile Butterworth ne kadar
     dik bir geçiş veriyor?
   - Stopband bastırması hangisinde daha iyi?
3. **Gürültülü sinyali üç şekilde filtrele:**
   - `lfilter(b_fir, 1, x)`
   - `lfilter(b_iir, a_iir, x)`
   - `filtfilt(b_iir, a_iir, x)`
4. **Zaman domeninde** temiz sinyalle üst üste çiz (ilk ~5 periyot):
   - FIR çıkışındaki kaymanın Isınma-2'deki tahminle tutup tutmadığını
     **sayısal olarak** doğrula (`np.argmax` veya korelasyonla kaymayı
     ölç).
   - `filtfilt` çıkışında kayma var mı?
   - Her üçünün başlangıç transient'ini karşılaştır.
5. **SNR iyileşmesini ölç:** Filtre öncesi ve sonrası SNR'ı hesapla
   (Hafta 3'teki ölçüm yöntemin hazır). Beklenti: gürültü tüm banda
   yayılmıştı, filtre ~2/25'ini geçiriyor — kaç dB iyileşme beklersin,
   kaç dB ölçtün?
6. **Welch ile PSD:** Filtre öncesi/sonrası sinyalin PSD'sini `welch`
   ile çiz (log eksen — Hafta 3 bonusundaki `xscale` desteğin burada işe
   yarar). `nperseg` parametresiyle oyna: 256 vs 4096 — çözünürlük/varyans
   dengesini gözlemle ve Hafta 3'teki **Δf = 1/T** kuralıyla bağla.

## Bölüm 3 — `resample` vs Elle Yazdıkların

Hafta 2'deki `interpolate(y1, Fs, 2)` sonucunu
`scipy.signal.resample(y1, 2*len(y1))` ile karşılaştır:

- İki çıkışın spektrumlarını alt alta çiz — image bastırma açısından fark
  var mı?
- Zaman domeninde fark sinyalinin gücüne bak (`np.mean((a-b)**2)`).
- `resample`'ın FFT tabanlı çalıştığını bilerek: hangi durumda kendi
  FIR tabanlı `interpolate`'in tercih edilir? (İpucu: gerçek zamanlı /
  blok blok işleme.)

## Bonus — BPSK + BER vs SNR

Basit bir BPSK zinciri kur:

1. Rastgele bit üret (`np.random.randint(0, 2, N)`), `0→-1, 1→+1` eşle.
2. Her sembolü `m = 8` kat upsample et (Hafta 2'deki
   `interpolation_decimation.py` doğrudan temel alınabilir).
3. `add_awgn` ile farklı SNR'larda gürültü ekle (örn. 0–10 dB arası).
4. Alıcıda: filtrele → downsample → işaret kararı (`>0` mı?).
5. BER hesapla, SNR'a karşı **log ekseninde** çiz (`semilogy`).

Teorik eğriyle karşılaştırmak istersen: `0.5 * erfc(sqrt(snr_linear))`
(`scipy.special.erfc`). Ölçümün teoriye yaklaşması, bütün zincirin doğru
kurulduğunun en iyi kanıtı.

## Teslim

- Isınma tahminleri ve gerçek sonuçlar (kısa notlar yeterli)
- `week4.py` (FIR/IIR karşılaştırması + welch + resample)
- Ölçtüğün grup gecikmesi ve SNR iyileşmesi değerleri (beklentiyle
  karşılaştırmalı)
- Bonusu yaptıysan BER eğrisi

Takıldığın yerde takıldığın haliyle gönder — hata mesajıyla birlikte
gelirsen daha da iyi. 🚀
