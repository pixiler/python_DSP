# wave-lab — VUnit + NVC + Surfer / surver

Dalga formu zincirini öğrenmek için kurulan küçük proje. DUT bilerek
önemsiz (`edge_detect`); amaç tasarım değil, **araç zinciri**.

```
wave-lab/
├── hdl/
│   ├── src/edge_detect.vhd
│   └── tb/tb_edge_detect.vhd
├── run.py
├── .gitignore          # vunit_out/, *.fst, *.vcd
└── README.md
```

---

## 1. Sürüm haritası — önce burayı oku

Bu projedeki her karar VUnit sürümüne bağlı. Tek komutla öğren:

```powershell
python -c "import vunit; print(vunit.__version__)"
nvc --version
where.exe surfer
```

| | VUnit 4.7.1 | VUnit 5.0.0.dev |
|---|---|---|
| `--gui` ile viewer seçimi | **yok** — `gtkwave` sabit | `--viewer surfer` |
| Viewer bulunamazsa | `RuntimeError` | gtkwave → surfer sırasıyla denenir |
| Dalga formatı seçimi | — | `--viewer-fmt {fst,vcd}` |
| Sim option | — | `nvc.viewer.gui`, `nvc.viewer_script.gui` |
| `from_argv(compile_builtins=...)` | kabul ediliyor | **kaldırıldı** |

4.7.1'in NVC arayüzü `gtkwave` ismini iki yerde sabit tutuyor: `--gui`
verildiği anda PATH'te `gtkwave` aranır, bulunamazsa simülasyon
başlamadan hata verir; komut da `["gtkwave", ...]` olarak kurulur.
Yani **4.7.1'de `--gui` ile Surfer açılamaz.**

### surfer mi, surver mi?

`surver`, Surfer'ın sunucu tarafı. Ama ayrı binary'ye çoğu zaman gerek
yok: `surfer` binary'sinin kendisinde `server` alt komutu var.

```powershell
surfer server .\dalga.fst      # surver ile ayni protokol
```

Ayrı `surver` binary'si GUI kütüphanesi olmayan makineler için
(başsız sunucu, CI runner, çıplak WSL). Windows masaüstünde gerekmez.

Kurulum seçenekleri:

| Yol | Ne verir |
|---|---|
| surfer-project.org'dan Windows binary | `surfer` + `server` alt komutu |
| VS Code `surfer` eklentisi | Editör içinde dalga, remote URL desteği |
| `cargo install --locked --git https://gitlab.com/surfer-project/surfer.git surver` | Yalnız `surver`, Rust derleyicisi gerekir |

---

## 2. Dalga dosyası nasıl üretilir

VUnit **kendiliğinden dalga dosyası üretmez.** `--gui` verilmediğinde
NVC komut satırına `--wave` hiç eklenmez.

İki yol var ve aralarındaki fark, dosya yolunu kimin hesapladığıdır.

### Yol A — `--gui` (VUnit yolu hesaplar)

Dosya `vunit_out/test_output/<test>/nvc/<entity>.fst` altına, teste özel
dizine düşer. 4.7.1'de bu yol Surfer için kapalı.

### Yol B — `nvc.sim_flags` (yolu sen verirsin)

```python
tb = lib.test_bench("tb_edge_detect")
tb.set_sim_option("nvc.sim_flags", ["--wave=dalga.fst"])
```

> **TUZAK:** Göreli yol, simülatör sürecinin çalışma dizinine yazar —
> yani `run.py`'yi çalıştırdığın dizine, test çıktı dizinine değil.
> VUnit alt süreci başlatırken `cwd` değiştirmiyor. Beş test koşarsan
> **tek dosya** oluşur, son biten testin çıktısıyla. `-p 4` ile
> paralel koşarsan dört süreç aynı dosyaya yazar.

Çözüm — test başına ayrı dosya:

```python
for test in tb.get_tests():
    test.set_sim_option("nvc.sim_flags", [f"--wave={test.name}.fst"])
```

`test.name` **kısa** adı döndürür (`tek_cevrimlik_darbe_uretir`).
`tb.test("olmayan_isim")` ise `KeyError` fırlatır — yazım hatası sessiz
kalmaz, bu iyi.

---

## 3. `run.py` — post_run kancasıyla Surfer

`--gui`'nin yerine geçen ve ondan daha iyi davranan çözüm: yalnızca
**düşen** testlerin dalgasını aç.

```python
import subprocess
from pathlib import Path
from vunit import VUnit, VUnitCLI

ROOT = Path(__file__).parent

cli = VUnitCLI()
cli.parser.add_argument("--surfer", action="store_true",
                        help="Dusen testlerin dalga formunu Surfer ile ac")
args = cli.parse_args()

vu = VUnit.from_args(args)
vu.add_vhdl_builtins()

lib = vu.add_library("lib")
lib.add_source_files(ROOT / "hdl" / "src" / "*.vhd")
lib.add_source_files(ROOT / "hdl" / "tb" / "*.vhd")

tb = lib.test_bench("tb_edge_detect")
for test in tb.get_tests():
    test.set_sim_option("nvc.sim_flags", [f"--wave={test.name}.fst"])


def open_waves(results):
    if not args.surfer:
        return
    for full_name, result in results.get_report().tests.items():
        if result.status == "passed":
            continue
        wave = ROOT / f"{full_name.split('.')[-1]}.fst"
        if wave.exists():
            subprocess.Popen(["surfer", str(wave)])


vu.main(post_run=open_waves)
```

Bilinmesi gerekenler:

- `post_run`, testler **geçse de düşse de** çağrılır. Süzmeyi sen yaparsın.
- `status` değerleri: `"passed"`, `"failed"`, `"skipped"`.
- Rapordaki anahtar **tam** ad (`lib.tb_edge_detect.<test>`), `test.name`
  ise kısa ad. `split(".")[-1]` ikisini eşler.
- `Popen` bloklamaz; üç test düşerse üç pencere açılır.

> **Yapma:** PATH'e `@surfer %*` içeren bir `gtkwave.bat` koyup `--gui`'yi
> kandırmak. Çalışır, ama altı ay sonra gerçekten gtkwave kurduğunda
> hangisinin açıldığını kimse bilemez.

---

## 4. Komut özeti

```powershell
# Testler
python run.py -v                    # hepsi, detayli
python run.py --list                # listele, kosma
python run.py "*kacirmaz*"          # ada gore filtrele
python run.py --surfer              # dusenlerin dalgasini ac (yukaridaki kanca)

# Dalga dosyasini bul
Get-ChildItem -Recurse -Filter *.fst

# Yerel goruntuleme
surfer .\tek_cevrimlik_darbe_uretir.fst

# Istemci-sunucu (surver protokolu)
surfer server .\tek_cevrimlik_darbe_uretir.fst
surver .\tek_cevrimlik_darbe_uretir.fst        # ayri binary kuruluysa

# Uzaktan baglanma
ssh -L 8911:localhost:8911 kullanici@makine
surfer http://127.0.0.1:8911/<token>
```

Varsayılan port **8911**, varsayılan bağlanma adresi **127.0.0.1**.

---

## 5. surver / server modu

`surver dosya.fst` şunu yazar:

```
[INFO] Loaded header of counter.fst in 302.41µs
[INFO] Starting server on 127.0.0.1:8911. To use:
[INFO] 1. Setup an ssh tunnel: -L 8911:localhost:8911
[INFO] 2. Start Surfer: surfer http://127.0.0.1:8911/<token>
```

**Neden değerli:** sunucu dosyanın yalnızca **başlığını** (hiyerarşi +
sinyal listesi) okur, sinyal verisini istemci istedikçe gönderir. 2 GB'lık
bir FST'yi `scp` ile çekmek yerine birkaç yüz KB sinyal çekiyorsun.
Surfer'ın otomatik yeniden yükleme özelliğiyle döngü şu hale gelir:
pencere açık kalır, `run.py` tekrar koşar, pencere kendini tazeler.

**Güvenlik:** URL'deki token bir parola değil, **taşıyıcı yetki** —
elinde tutan içeri girer. Token'sız yayın, portu görebilen herkese tüm
sinyal hiyerarşini açar; bir tasarımda bu RTL'in yapısal dökümüne
eşdeğerdir. Asıl koruma `127.0.0.1`'e bağlanmakta: uzaktan erişim ssh
tüneli gerektirir, yani kimlik doğrulama ssh'a devredilmiştir.
`0.0.0.0`'a bağlayan bir bayrak görürsen kullanma. Token'ı CI log'una
düşürme.

Bağlanma seçenekleri: `surfer <url>`, tarayıcıda `app.surfer-project.org`,
veya VS Code Vaporview eklentisi (`> vaporview.openRemoteViewer`).

---

## 6. Dalga okurken öğrenilenler

### Delta cycle FST'de yoktur

`wait until rising_edge(clk); signal_in <= '0';` yazdığında atama, saat
kenarıyla **aynı simülasyon zamanında** ama bir delta sonra gerçekleşir.
FST'de delta kavramı olmadığı için ikisi aynı zaman damgasına yığılır ve
dalgada ayırt edemezsin.

Çözüm — her yerde tutarlı bir oturma payı:

```vhdl
constant C_SETTLE : time := 1 ns;

procedure next_cycle is
begin
  wait until rising_edge(clk);
  wait for C_SETTLE;
end procedure;
```

İki iş birden yapar: gerçekçi bir clock-to-out payı bırakır **ve** dalga
formunda "kenarda örneklendi" ile "kenardan sonra değişti" ayrımını
gözle görünür kılar.

Payı unutursan sessiz bir hata alırsın: `wait until rising_edge(clk)`
sonrası hemen okuma yaparsan DUT ile aynı delta'da uyanırsın ve
sinyalin **kenar öncesi** değerini okursun.

### İmleç ölçümü ≠ simülasyon

Surfer'ın imleci geçişlere değil piksele yapışır. `-978283 fs` gibi bir
sayı gördüysen: 1 ns = 1.000.000 fs; aradaki 21.717 fs farenin nereye
düştüğüdür. Eksi işareti de imleçleri hangi sırayla koyduğunla ilgilidir.

**Kural:** dalgada okuduğun sayıya güvenmeden önce kaynağının simülasyon
mu yoksa fare mi olduğunu ayır. Kesin ölçüm için geçişlerin üstüne
marker koy veya fark sıfıra yaklaşana kadar zoom yap.

### `'U'` ≠ `'X'`

`std_logic`'in varsayılan değeri `'U'` — hiç sürülmemiş.
`'X'` ise iki sürücünün çakışması. Çözümleri tamamen farklıdır:
`'U'` "kimse atamadı", `'X'` "iki kişi atadı" der.

### Variable'lar dalgada görünmez

NVC'nin dökümü yalnızca **sinyalleri** kapsar (kılavuzun bölüm adı bile
"SELECTING SIGNALS"). Sebep kavramsal: dalga formu bir olay listesidir,
variable'ın sürücüsü de olayı da yoktur — bir process çalışması sırasında
beş kez değişebilir ve bunların ayırt edilebilir zaman damgası olmaz.
Döngü indeksleri de aynı sebeple görünmez.

Üç seçenek:

1. **Ayna sinyal (önerilen).** Variable kalır, yanına gözlem sinyali
   konur: `dbg_edge_count <= edge_count;`. Semantik bozulmaz, ayna bir
   delta geriden gelir.
2. **Variable'ı sinyale çevirmek — dikkat.** Davranışı değiştirir:
   aynı process içinde yazıp hemen okuyan kod, sinyale çevrilince eski
   değeri okur. Gözlemek için yaptığın değişiklik gözlediğin şeyi bozar.
3. **Log.** Kontrol akışı değerleri için dalgadan iyidir:
   `info("cevrim " & to_string(i) & ": ...")`. Çıktı `output.txt`'ye
   düşer, `-v` ile ekrana gelir.

Ticari simülatörler (Questa/ModelSim) dalga penceresinde variable
gösterebilir — çünkü dosya okumaz, çekirdeğe doğrudan bağlıdır. Ama o
veriyi de VCD/FST'ye yazamaz.

### FIR'a dönerken

Dizi tipli sinyallerin dökümünde NVC'de `--dump-arrays` gibi ek bayraklar
devreye giriyor. Katsayı dizisini dalgada göremezsen ilk bakılacak yer
`nvc --help`. Ayrıca NVC varsayılan olarak tasarımdaki **her** sinyali
döker; büyük tasarımda `--include` / `--exclude` glob'larıyla daralt.

---

## 7. Testbench tasarımı — bu projede öğrenilenler

### Şartname tek yerde yaşar

```vhdl
constant C_LATENCY : natural := 1;   -- signal_in dustukten kac yukselen
                                     -- kenar sonra cikis '1' olur
```

Tasarımın gecikmesi değişirse tek satır değişir, testlerin gövdesi değil.
Gecikme sabiti yoksa bilgi testlerin içindeki `wait` sayılarında **örtük**
kalır; altı ay sonra hangi testi niye güncellediğini kimse anlamaz.

### Saymak yer ölçmez

`edge_count = 1` demek "beş çevrimde toplam bir darbe var" demektir.
DUT'un çıkışını bir çevrim geciktir — sayı yine 1 çıkar, test **geçer**.
Bu kör noktayı `wait for 1 ns` eklemek de kapatmaz; sorun okuma anında
değil, ölçülen büyüklükte.

Doğrusu, yeri ve genişliği aynı döngüde doğrulamak:

```vhdl
for i in 1 to C_OBSERVE_CYCLES loop
  next_cycle;
  if i = C_LATENCY then
    check_equal(edge_detected, '1', "darbe " & to_string(C_LATENCY) & ". cevrimde bekleniyordu");
  else
    check_equal(edge_detected, '0', to_string(i) & ". cevrimde beklenmeyen darbe");
  end if;
end loop;
```

### Ara kontrol olmadan "kaçırmaz" iddiası boştur

İki `check_equal(edge_detected, '1')` arka arkaya. Çıkışı `'1'`'de takılı
kalan bir DUT bu testi **geçer**. Aradaki çevrimde `'0'`'a döndüğünü de
kontrol et.

### Negatif test ekle

`sabit_giriste_darbe_uretmez` — hiç kenar yokken çıkış kıpırdamamalı.
Ucuzdur ve sahte darbe sınıfını tek başına kapatır.

### Testin adı, düştüğünde nereye bakacağını söyleyen tek belgedir

`arka_arkaya_kenar_kacirmaz` bozuk (gecikmeli) DUT'ta kırmızıya döndü —
ama yaratılan hata bir *kaçırma* değil bir *gecikme* hatasıydı. Test
yakaladı, iyi; ama yanlış yeri işaret etti. Adının kapsamadığı bir iddiayı
sessizce taşıyan test, o iddiayı ayrı bir teste çıkarmalı
(`bir_cevrim_gecikmeyle_yanit_verir`).

### Watchdog

```vhdl
test_runner_watchdog(runner, 1 ms);
```

Bir `wait until` hiç tamamlanmazsa simülasyon sonsuza kadar döner.
Lokalde Ctrl+C'lersin, CI'da runner'ı saatlerce meşgul eder.

### Saatin ilk değeri

`signal clk : std_logic := '0';` + `clk <= not clk after C_PERIOD/2;`
İlk değer verilmezse `clk` başlangıçta `'U'`'dur ve `'U' → '1'` geçişi
`rising_edge` saymaz — ilk kenarın nerede olduğu belirsizleşir.

---

## 8. Tuzak listesi (özet)

1. `--gui` yoksa dalga dosyası da yok.
2. Göreli `--wave` yolu test çıktı dizinine değil, çalışma dizinine yazar
   — testler birbirini ezer.
3. `--gui` post-mortem'dir: simülasyon biter, *sonra* viewer açılır.
   Beş test = beş pencere. Dalgaya bakarken tek teste filtrele.
4. Delta cycle FST'de temsil edilmez; oturma payı koymazsan geçişler
   üst üste biner ve kenar öncesi değeri okursun.
5. Dalgadaki sayı fareden gelmiş olabilir — ölçümün kaynağını ayır.
6. Variable'lar dökülmez; ayna sinyal veya log kullan.
7. Her koşu diski doldurur. `.gitignore`'a `*.fst`. Daha önce commit
   edildiyse `git rm --cached` gerekir.
8. Token'ı log'a düşürme; `0.0.0.0`'a bağlama.
9. VUnit 5'e geçerken `from_argv(compile_builtins=...)` patlar.
10. Öğrenme projesi için ayrı `.venv` aç — ön sürüm VUnit üretim
    projesini bozmasın.

---

## 9. Çalıştırma sırası

```powershell
python run.py --list        # testleri gor
python run.py -v            # kos
python run.py --surfer      # dusenlerin dalgasini ac
```

## 10. Sonraki adımlar

- DUT'u AXI4-Stream skid buffer ile değiştir, geri basınç uygula.
  Assertion testin düştüğünü söyler; `ready`'nin **hangi çevrimde**
  düştüğünü ancak dalgada görürsün.
- VUnit 5.0.0.dev + `--viewer surfer` ile `--gui` yolunu dene.
- Bu zinciri FIR projesine taşı: `--include` ile sinyal seçimi,
  `--dump-arrays`, akümülatör için ayna sinyal.
