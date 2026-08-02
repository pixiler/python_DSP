# Hafta 6 — Görev 6: VUnit ile VHDL Testbench (Final Projesi)

## Hedef

Beş haftadır kurduğun Python altyapısını asıl amacına bağlamak: **VHDL
testbench'lerini Python'dan yönetmek.**

Hafta 5'te öğrendiğin her şeyin VUnit'te bire bir karşılığı var:

| pytest | VUnit |
|---|---|
| `pytest` komutu testleri keşfeder | `python run.py` testleri keşfeder |
| `test_*.py` dosya kuralı | `tb_*.vhd` testbench kuralı |
| `assert` | `check_equal`, `check_true` |
| `pytest -k "delay"` | `python run.py "*delay*"` |
| `conftest.py` (ortak kurulum) | `run.py` (kütüphane, kaynak listesi) |
| `parametrize` | `test.add_config(...)` |
| tolerans tablosu | **aynen geçerli** |

Fark şu: pytest'te test edilen şey Python fonksiyonu, burada **donanım**.
Ve donanımın Python'da olmayan bir boyutu var: **zaman**. Her `check`
belirli bir saat çevriminde yapılır; doğru sonuç yanlış çevrimde
gelirse hâlâ hatadır.

## Kurulum

Üç parça var. Sırayla kur, her adımda doğrula.

### 1. Simülatör

VUnit kendi başına simüle etmez — bir simülatörü sürer. Öğrenme için
ücretsiz iki seçenek:

- **NVC** — hızlı, modern VHDL desteği iyi, Windows binary'si var.
  <https://github.com/nickg/nvc/releases>
- **GHDL** — daha yaygın, dokümantasyonu bol.
  <https://github.com/ghdl/ghdl/releases>

Windows'ta ikisi de zip olarak indirilip `PATH`'e eklenebiliyor.
NVC ile başlamanı öneriyorum (kurulumu daha az sorunlu).

```powershell
nvc --version
```

> **Uzun vade notu:** Xilinx IP core'larını (FFT, DDS vb.) simüle etmek
> için ticari simülatör (Questa, Riviera-PRO) gerekiyor. Şimdilik gerek
> yok; ihtiyaç doğduğunda ücretsiz **Questa Starter** ile tanışıp,
> gerçek ihtiyaç çıkınca lisanslamak makul bir yol. Ara strateji:
> IP yerine davranışsal model (BFM) + VUnit'in AXI4-Stream doğrulama
> bileşenleri.

### 2. VUnit

```powershell
python -m pip install vunit_hdl
python -c "import vunit; print(vunit.__version__)"
```

VUnit **Python paketi** — yani `dsp/` paketinle aynı ortamda yaşayacak.
Bu tesadüf değil, projenin bel kemiği: test vektörlerini `dsp` üretecek.

### 3. Klasör yapısı

Kuruldu — repo kökü artık şöyle:

```
python_DSP/
├── dsp/                    # Hafta 5'ten, dokunulmuyor
├── tests/                  # Hafta 5'ten, dokunulmuyor
├── hdl/
│   ├── src/                # counter.vhd, fir_filter.vhd  ← sen yazacaksın
│   └── tb/                 # tb_counter.vhd, tb_fir_filter.vhd
├── vectors/                # üretilen CSV'ler (.gitignore'da)
├── docs/                   # bu dosya + öğrenme planı + eski görevler
├── weeks/                  # Hafta 1-4 script'leri (arşiv, dokunulmuyor)
├── generate_vectors.py     # dsp/ kullanarak test verisi üretir (iskelet)
├── run.py                  # VUnit giriş noktası
└── pytest.ini
```

Not: `run.py` `hdl/src` ve `hdl/tb` klasörleri boşken de çalışır —
ilk `.vhd` dosyanı yazana kadar hata vermez, sadece hiç test bulamaz.

## Bölüm 1 — Isınma

**Önce kağıt üzerinde tahmin et, sonra doğrula.**

1. VHDL'de `signal x : std_logic_vector(15 downto 0);` kaç bit? En
   anlamlı bit hangi indekste? (MATLAB/Python'da `x[0]` ilk elemandı —
   burada indeksleme neye göre?)

2. Python'da `0.7071` yazıyorsun. Bunu 16 bitlik işaretli sabit noktalı
   (Q1.15) formatta VHDL'e vereceksin. Hangi tamsayı olur? Ters çevirme
   formülü nedir? **Bu haftanın "birim çevirisi" tuzağı bu** — hata
   kalıpları listendeki 4 numara, yeni kılıkta.

3. Bir FIR filtrenin katsayıları Q1.15, girişi Q1.15. Çarpım kaç bitlik
   ve hangi formatta? 65 tap toplanınca taşmayı önlemek için kaç bit
   büyüme payı (guard bit) gerekir?

4. `check_equal(got, expected)` bir testbench'te **hangi anda**
   çalışmalı — saat kenarında mı, kenardan sonra mı? Yanlış anda
   yapılırsa ne görürsün?

5. pytest'te bir test fonksiyonu sessizce biterse "geçti" sayılıyordu.
   VUnit'te bir testbench hiç `check` çağırmadan biterse ne olur? Bu
   iyi mi kötü mü? (Hafta 5'teki "hiçbir şey ölçmeyen test" dersini
   hatırla.)

> ⚠️ **Kritik fark:** Python'da `assert` yanlışsa program **durur**.
> VHDL'de simülasyon zamanı akmaya devam eder; `check` başarısız olsa
> bile sonraki çevrimler işlenir. Bu yüzden bir testbench yüzlerce
> hata basabilir. `run.py`'de ilk hatada durdurma seçeneğini bilmek
> (`--exit-0`, severity ayarları) işini kolaylaştırır.

## Bölüm 2 — İlk Adım: Sayaç

Amaç VUnit mekaniğini öğrenmek; DSP burada değil.

### 2.1 Tasarım

`hdl/src/counter.vhd` — parametrik genişlikte, senkron reset'li,
enable'lı yukarı sayaç. Taşınca (`max` değerine ulaşınca) sıfırlansın
ve bir `tick` darbesi üretsin.

### 2.2 Testbench iskeleti

```vhdl
library vunit_lib;
context vunit_lib.vunit_context;

entity tb_counter is
  generic (runner_cfg : string);
end entity;

architecture tb of tb_counter is
  -- sinyaller, saat üretimi
begin
  main : process
  begin
    test_runner_setup(runner, runner_cfg);

    while test_suite loop
      if run("reset_sayaci_sifirlar") then
        -- ...
      elsif run("enable_dusukken_sayac_durur") then
        -- ...
      elsif run("maksimumda_tick_uretir") then
        -- ...
      end if;
    end loop;

    test_runner_cleanup(runner);
  end process;
end architecture;
```

Dikkat: `run("...")` içindeki isim **test adı** — Hafta 5'teki
adlandırma kuralı burada da geçerli. `test_1` değil,
`enable_dusukken_sayac_durur`.

### 2.3 `run.py`

```python
from pathlib import Path
from vunit import VUnit

ROOT = Path(__file__).parent

vu = VUnit.from_argv()
vu.add_vhdl_builtins()

lib = vu.add_library("lib")
lib.add_source_files(ROOT / "hdl" / "src" / "*.vhd")
lib.add_source_files(ROOT / "hdl" / "tb" / "*.vhd")

vu.main()
```

Çalıştır:

```powershell
python run.py -v            # hepsi, detayli
python run.py --list        # testleri listele, kosma
python run.py "*tick*"      # ada gore filtrele
python run.py --gui         # dalga formu (simulator destekliyorsa)
```

### 2.4 Kırmızıyı gör

Hafta 5'teki refleksi burada da uygula: sayaçta bir şeyi bilerek boz
(örneğin `tick`'i bir çevrim geç üret), testin **kaldığını** gör, sonra
düzelt. Zaman boyutu olan bir testin gerçekten zamanı kontrol ettiğini
başka türlü bilemezsin.

## Bölüm 3 — Asıl Proje: FIR Filtre

Şimdi beş haftanın hepsi birleşiyor.

### 3.1 Katsayıları Python üret

`generate_vectors.py`:

```python
from dsp import fir1, sine_wave, add_awgn
import numpy as np

FS, FC, NUMTAPS = 50_000, 1_000, 16   # 65 tap donanimda buyuk, 16 ile basla
```

Yapılacaklar:
1. `fir1` ile katsayıları üret.
2. Q1.15'e çevir (`np.round(h * 32767).astype(np.int16)`) — **taşma
   kontrolü yap**, katsayı 1,0'a çok yakınsa kırpılır.
3. Giriş sinyali üret: 1 kHz + 10 kHz toplamı (Hafta 2'deki senaryo),
   yine Q1.15.
4. **Beklenen çıkışı Python'da hesapla** — ama dikkat: `apply_filter`
   float ile çalışır, donanım tamsayı ile. İkisi birebir tutmaz.
   Ya sabit noktalı bir referans modeli yaz, ya da toleranslı
   karşılaştır (tolerans tablosu: kuantizasyon hatası kaynağı,
   ~1 LSB mertebesi).
5. Üçünü ayrı CSV'ye yaz.

### 3.2 VHDL tarafı

`fir_filter.vhd` — transpoze veya direct-form FIR. Katsayılar generic
veya paketten gelsin. Taşma payını Isınma-3'teki hesaba göre ayarla.

### 3.3 Testbench

VUnit'in `csv_file_pkg` / `integer_array_pkg` ile CSV oku:

```vhdl
variable data : integer_array_t;
...
data := load_csv(input_path);
```

Her örneği besle, çıkışı topla, beklenenle karşılaştır:

```vhdl
check_equal(got, expected, max_diff => 2);
```

**Grup gecikmesi tuzağı:** donanım çıkışı `(NUMTAPS-1)/2` örnek gecikmeli
ve ayrıca pipeline gecikmesi var. Karşılaştırmadan önce **hizala** —
hata kalıpları listendeki 6 numara, bu sefer VHDL'de.

### 3.4 Doğrulama zinciri

Testbench çıktıyı bir CSV'ye yazsın, Python tarafında oku ve
`dsp/analysis.py` ile spektrumunu al. 10 kHz bileşeninin bastırıldığını
**sayısal olarak** doğrula — Hafta 2'de gözle yaptığın işi artık test
olarak yapıyorsun.

## Bonus

1. **`add_config` ile parametrize:** aynı testbench'i farklı tap sayısı
   veya farklı veri genişliğiyle koştur. `@pytest.mark.parametrize`'ın
   VUnit karşılığı.
2. **Kapsam:** simülatör destekliyorsa satır/dal kapsamı al. Hangi VHDL
   dalları hiç çalışmadı?
3. **CI:** `run.py` bir komutla koştuğu için GitHub Actions'a bağlanabilir.
   Her commit'te testler otomatik koşar.

## Teslim

- Isınma tahminleri ve gerçek sonuçlar
- Simülatör + VUnit sürüm çıktıları
- `counter.vhd` + `tb_counter.vhd` + `run.py`, `python run.py -v` çıktısı
- Sayaçta bilerek bozup **kırmızı gördüğün** çıktı
- `generate_vectors.py`, `fir_filter.vhd`, `tb_fir_filter.vhd`
- FIR testinin geçtiği çıktı + spektrum doğrulaması
- Q1.15 çevrim hesabın ve seçtiğin tolerans (hangi hata kaynağından?)

Takıldığın yerde takıldığın haliyle gönder — hata mesajıyla birlikte
gelirsen daha da iyi. VHDL derleyici hataları Python'unkinden daha
kriptiktir, ilk birkaçında birlikte okuruz. 🚀
