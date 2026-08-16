# VUnit ile HDL Doğrulama — Pratik Rehber

Bu doküman, VUnit tabanlı bir doğrulama akışının kurulması sırasında ortaya çıkan
tasarım kararlarını toplar. Python/NumPy tarafında altın model (golden model)
üretip VHDL tarafını buna karşı doğrulama yaklaşımını temel alır.

---

## İçindekiler

1. [Satıcı IP'leri ve açık kaynak simülatörler](#1-satıcı-ipleri-ve-açık-kaynak-simülatörler)
2. [Katmanlı doğrulama stratejisi](#2-katmanlı-doğrulama-stratejisi)
3. [Stub ile IP izolasyonu](#3-stub-ile-ip-izolasyonu)
4. [Altın model: bit-exact vs. istatistiksel](#4-altın-model-bit-exact-vs-istatistiksel)
5. [Parametrizasyon: `add_config`](#5-parametrizasyon-add_config)
6. [Parametrizasyon: manifest döngüsü](#6-parametrizasyon-manifest-döngüsü)
7. [Hangisini ne zaman? Karar rehberi](#7-hangisini-ne-zaman-karar-rehberi)
8. [Test vektörü üretme stratejileri](#8-test-vektörü-üretme-stratejileri)
9. [State sızıntısı: soğuk ve sıcak döngüler](#9-state-sızıntısı-soğuk-ve-sıcak-döngüler)
10. [Paralelleştirme ve hız](#10-paralelleştirme-ve-hız)
11. [Docker: ne zaman, ne için](#11-docker-ne-zaman-ne-için)
12. [Uzak sunucuda çalıştırma](#12-uzak-sunucuda-çalıştırma)
13. [Waveform: dökme, görüntüleme, debug akışı](#13-waveform-dökme-görüntüleme-debug-akışı)
14. [Öğrenme sırası](#14-öğrenme-sırası)

---

## 1. Satıcı IP'leri ve açık kaynak simülatörler

### Sorun

Satıcı IP'lerinin (Xilinx XFFT, CORDIC, DDS, FIR Compiler vb.) simülasyon
modelleri **IEEE P1735** standardıyla şifrelenmiş gelir. Bu modeller NVC veya
GHDL gibi açık kaynak simülatörlerde derlenemez.

### Neden

P1735 şifrelemesi şöyle işler: satıcı, modelin kaynağını rastgele bir simetrik
anahtarla şifreler. Sonra o simetrik anahtarı, desteklediği **her simülatör
satıcısının açık anahtarıyla ayrı ayrı** şifreleyip dosyanın başına bir liste
olarak koyar:

```
`protect key_keyowner="Mentor Graphics" ... <şifreli oturum anahtarı>
`protect key_keyowner="Synopsys"        ... <şifreli oturum anahtarı>
`protect key_keyowner="Aldec"           ... <şifreli oturum anahtarı>
`protect key_keyowner="Xilinx"          ... <şifreli oturum anahtarı>
`protect data_block                      ... <şifreli kaynak kod>
```

Ticari simülatör çalıştığında listede kendi adını bulur, gömülü **özel
anahtarıyla** oturum anahtarını çözer, kaynağı çözer, belleğe derler ve içeriği
kullanıcıdan gizler.

### Bu neden aşılamaz

Açık kaynak bir simülatörün o listede satırı yok — olsa bile karşılığı olan özel
anahtarı taşıyamaz. Özel anahtar binary'de veya repoda bulunursa çıkarılabilir
hale gelir; çıkarıldığı an dünyadaki bütün satıcıların şifreli IP'leri açılabilir.
Yani **P1735 anahtarı taşımak, açık kaynak olmakla mantıksal olarak bağdaşmıyor.**

Ayrıca satıcı olmanın şartları sadece anahtar tutmak değil: korumalı bölgeye
dalga formu probu atılmasını engellemek, çözülmüş kaynağı diske yazmamak gibi
"rights management" yükümlülükleri de denetleniyor.

> **Sonuç:** NVC bunu yapmıyor değil, **yapamaz**. Beklemeye veya çözüm aramaya
> gerek yok.

### Ticari simülatör seçenekleri

| Simülatör | Maliyet | VUnit desteği | Not |
|---|---|---|---|
| **XSim** | Vivado ile bedava | ❌ Yok | Düz TB yazılır, IP'yi sorunsuz simüle eder |
| **Questa Starter** | Bedava (satır limitli) | ✅ Var | Tek IP için limit genelde yeterli |
| Questa / VCS / Riviera | Ticari | ✅ Var | Gerçek ihtiyaç doğduğunda |

Sıra: XSim ile başla → VUnit'i gerçek IP üzerinde koşturmak istersen Questa
Starter'a bak → ticari lisans en son.

### Az bilinen kaçış yolu (genelde önerilmez)

Şifreli olan **davranışsal model**. Vivado post-synthesis functional netlist
üretebilir:

```tcl
write_vhdl -mode funcsim netlist.vhd
```

Bu netlist şifreli değildir; UNISIM primitiflerinden (LUT, FDRE, DSP48E2,
RAMB36E2) oluşur. UNISIM modelleri Vivado kurulumunda **açık kaynak VHDL** olarak
durur:

```
<Vivado>/data/vhdl/src/unisims/primitive/*.vhd
```

Bunları NVC'de bir kütüphaneye derleyip netlist'i simüle etmek teorik olarak
mümkündür.

**Pratik sıkıntılar:** RTL'e göre 10–100x yavaş; netlist bazen Verilog çıkar
(NVC VHDL-only, karma dil yok); bazı primitiflerin VHDL modeli eksik olabilir;
IP her yeniden konfigüre edildiğinde netlist yeniden üretilmeli.

Günlük regresyon için uygun değil. "Gerçek IP'yi bir kez açık kaynak simülatörde
görmek istiyorum" senaryosu için denenebilir.

---

## 2. Katmanlı doğrulama stratejisi

Kısıtlama aslında **doğru mimariyi dayatıyor**. Satıcı IP'sini kendi
testbench'inde doğrulamak zaten senin işin değil — satıcı onu doğrulamış.
Doğrulaman gereken şey kendi yazdığın mantık.

| Katman | Ne doğrulanır | Nerede | Sıklık |
|---|---|---|---|
| **A** | Kendi wrapper mantığın: protokol el sıkışma, `tlast` yerleşimi, backpressure, frame sayacı, yeniden sıralama | VUnit + açık kaynak sim + stub | Her commit |
| **B** | Sayısal doğruluk: algoritma referansla tutuyor mu, ölçekleme doğru mu | Python (NumPy) | Her commit |
| **C** | Gerçek IP entegrasyonu: IP'nin gerçek latency'si, event sinyalleri | XSim / Questa, düz TB | IP config değiştiğinde |

Katman C seyrek koşulur. **Günlük regresyon A + B'de yaşar.**

Bunun ek faydası: her şeyi bir arada koşturmak testleri yavaşlatır ve hata
bulunduğunda "IP mi ben mi" belirsizliği yaratır. İzolasyon debug alanını daraltır.

---

## 3. Stub ile IP izolasyonu

### Bağlama yöntemi

IP'yi **component olarak** instantiate et (entity instantiation değil). O zaman
bağlama isme göre yapılır ve hangi mimarinin derleneceği senin kontrolünde olur.

```
hdl/
├── src/
│   └── my_wrapper.vhd        # IP'yi component olarak çağırır
├── sim_models/
│   └── vendor_ip_stub.vhd    # entity vendor_ip — SADECE VUnit akışında derlenir
└── tb/
    └── tb_my_wrapper.vhd
```

```python
lib.add_source_files(ROOT / "hdl" / "src" / "*.vhd")
lib.add_source_files(ROOT / "hdl" / "sim_models" / "*.vhd")   # gerçek IP burada yok
lib.add_source_files(ROOT / "hdl" / "tb" / "*.vhd")
```

### Port listesi

Stub'ın port listesini **IP'nin ürettiği instantiation template'inden birebir
kopyala** (`.vho` dosyası veya IP Sources → Instantiation Template).

Portlar konfigürasyona göre değişir: config word genişliği, `tuser` içeriği, event
sinyallerinin varlığı hep seçilen ayarlara bağlıdır. Elle yazmak sessiz hata
üretmenin en kolay yoludur.

### Stub'ın davranış seviyeleri

**Seviye 1 — CSV replay (başlangıç için önerilen):**
Stub girişi yutar, çıkışa Python'ın hesapladığı altın vektörü protokole uygun
şekilde basar. Sayısal doğruluğu test *etmez* — o zaten satıcının sorumluluğu.
Wrapper'ın protokolü doğru sürüp sürmediğini test eder.

**Seviye 2 — davranışsal model:**
`ieee.math_complex` veya fixed-point aritmetikle IP'nin işlevini kabaca modelle.
Küçük N için hesap maliyeti önemsizdir (N=64 için O(N²) = 4096 çarpım simülasyonda
hiçbir şey). Herhangi bir girişe cevap verir, ölçekleme davranışı da modellenebilir.

Önce Seviye 1'i çalıştır; Seviye 2'ye ihtiyaç doğarsa geç.

### Stub'la test edilebilecekler

Gerçek IP olmadan, sadece kendi mantığın üzerinde:

- Backpressure: VC'nin `stall` konfigürasyonuyla `tready` düşür — veri kayboluyor mu?
- `tlast` bilerek erken/geç gönder — hata yolu doğru ele alınıyor mu?
- Ardışık iki frame — ikinci frame'de config yeniden yazılıyor mu?
- Frame ortasında config yazması — kabul mü, bekletme mi?

Gerçekte bug'ların çıktığı yer burasıdır.

---

## 4. Altın model: bit-exact vs. istatistiksel

Bir tasarımın "doğru mu" sorusunun **iki ayrı cevabı** vardır ve bunlar farklı
yerlerde doğrulanır:

| Soru | Yöntem | Nerede |
|---|---|---|
| Donanım, modelin yaptığını birebir yapıyor mu? | **Bit-exact**, tolerans yok | VHDL testbench |
| Model yeterince iyi mi? (RMSE vs SNR, hata payı, capture range) | İstatistiksel, binlerce koşu | Python |

**İkincisini HDL simülasyonunda asla yapma.** 1000 Monte Carlo koşusu Python'da
saniyeler, HDL simülatöründe saatler sürer.

### Fixed-point altın model

Bit-exact karşılaştırma için gereken şey, **float bir referans değil**, VHDL'in
yaptığı aritmetiği birebir taklit eden bir Python modeli: kelime genişlikleri,
yuvarlama modu, saturasyon, taşma davranışı.

Bunu doğru yaparsan testbench'te hiçbir tolerans gerekmez — iki tamsayı
karşılaştırırsın. **Tolerans girdiğin an**, "acaba tolerans mı geniş, yoksa
gerçekten bug mu var" belirsizliğine düşersin.

### İki zincirli doğrulama

```
float referans  ──(toleranslı, pytest)──►  fixed-point model
                                                  │
                                          (bit-exact, VUnit)
                                                  ▼
                                             VHDL DUT
```

Fixed-point model için de pytest testleri yaz. Böylece hata çıktığında hangi
katmanda olduğunu ayırt edebilirsin.

### Eşleşmesi gereken klasik noktalar

Satıcı IP'leri veya kendi aritmetik bloklarınla çalışırken bug'ların yoğunlaştığı
yerler:

- **İteratif algoritmalar (CORDIC vb.):** iterasyon sayısı, kazanç faktörü,
  quadrant ön-döndürmesi. Kütüphane fonksiyonuyla (`np.arctan2` gibi)
  karşılaştırırsan asla tutmaz. Sınır açıları (±π civarı) mutlaka test vektörüne
  girsin — sarma hataları orada saklanır.
- **Magnitude yaklaşımları:** donanım `sqrt(I²+Q²)` yerine `|I|+|Q|` veya
  alpha-max-beta-min kullanıyorsa, model de kullanmalı. Argmax sonucu buna bağlı
  değişebilir.
- **Argmax eşitlik davranışı:** VHDL'de `>` mu `>=` mi kullandığın, iki değer eşit
  olduğunda farklı indeks verir. `np.argmax` ilk maksimumu döner. Eşit tepe
  içeren yapay vektörle bilerek test et.
- **Çıkış sırası:** IP bit-reversed çıkış veriyorsa, yeniden sıralamayı kim
  yapıyor? Altın vektörü **doğrudan tanımdan** üret, donanımın yaptığını taklit
  ederek değil — yoksa aynı yanlış varsayım iki tarafta da bulunur ve test geçer.
- **İşaret konvansiyonu:** sadece `abs()` kontrol eden testler işaret hatasını
  geçirir. Simetrik çiftler koy: `+x` ve `−x`, ikisi de zorunlu.

### Köşe vakaları

Rastgele vektör üretmeden önce bunları elle koy:

- Sıfır giriş → sahte kilit/çıktı üretmemeli
- Full-scale giriş → akümülatör taşıyor mu
- Tam sınır değeri → hâlâ doğru
- Sınırın hemen dışı → nazikçe hata, `valid` bayrağı ne yapıyor?
- Nötr değer (kazanç=1, offset=0) → çıktı girişe *tam* eşit olmalı, "yaklaşık" değil

Gürültülü vektör HDL testbench'ine **girmesin** — orada bit-exact eşleşme
aranır, gürültü sadece istatistiksel katmanda anlamlıdır.

---

## 5. Parametrizasyon: `add_config`

### pytest paraleli

| Ne değişiyor | pytest | VUnit |
|---|---|---|
| Test içindeki veri | `@parametrize` | `add_config` + generic |
| Yapısal parametre (port genişliği, derinlik) | — | `add_config` + generic |
| Test öncesi/sonrası iş | fixture | `pre_config` / `post_check` |
| Ortak yardımcılar | `conftest.py` | VHDL package / VC'ler |

**En kritik fark:** `add_config` her konfigürasyon için **ayrı bir elaboration**
üretir. pytest'te parametrizasyon ucuzdur (aynı fonksiyon, farklı argüman).
VUnit'te her config ayrı derleme + elaborate + koşudur. İzolasyon mükemmel,
maliyet yüksek.

### Üç uygulama seviyesi

```python
tb = lib.test_bench("tb_fifo")

# Seviye 1: testbench'teki TÜM testlere uygulanır
for depth in [8, 16, 64]:
    tb.add_config(name=f"depth={depth}", generics=dict(G_DEPTH=depth))

# Seviye 2: sadece tek bir test'e
test = tb.test("tam doluyken yazma reddedilir")
test.add_config(name="dar", generics=dict(G_WIDTH=1))

# Seviye 3: kütüphane geneli (nadiren)
lib.set_generic("G_CLK_PERIOD_NS", 10)
```

Seviye 1 ve 2 **çarpılır**: testbench'te 3 config, o test'te 2 config varsa o test
6 kez koşar, diğerleri 3'er kez.

### Kartezyen çarpım

VUnit'in özel bir mekanizması yok — sadece bir `for` döngüsü:

```python
from itertools import product

for depth, width, mode in product([8, 64], [8, 32], ["sync", "async"]):
    tb.add_config(
        name=f"d{depth}_w{width}_{mode}",
        generics=dict(G_DEPTH=depth, G_WIDTH=width, G_MODE=mode),
    )
```

**İsimlendirme önemli.** VUnit test adını şöyle kurar:

```
lib.tb_fifo.d64_w8_sync.tam doluyken yazma reddedilir
```

Sonra filtreleyebilirsin:

```bash
python run.py "*d64*"
```

Anlamlı isim ver; `config_17` deme.

### VHDL tarafı

Generic'ler entity'de tanımlı olmalı ve **varsayılan değeri olmalı** — yoksa
`add_config` verilmediğinde elaborate edilemez:

```vhdl
entity tb_fifo is
  generic (
    runner_cfg : string;
    G_DEPTH    : positive := 16;
    G_WIDTH    : positive := 8
  );
end entity;
```

`runner_cfg` zorunludur, VUnit onu kendisi geçer.

```vhdl
test_runner : process
begin
  test_runner_setup(runner, runner_cfg);

  while test_suite loop
    if run("bos fifo okunamaz") then
      -- ...
    elsif run("tam doluyken yazma reddedilir") then
      -- G_DEPTH burada kullanılabilir
    end if;
  end loop;

  test_runner_cleanup(runner);
end process;
```

`while test_suite` döngüsü her yinelemede **tek bir** test koşar ve VUnit süreci
sonlandırır. Testler gerçekten izoledir — bir sonraki test için simülasyon
yeniden başlar. pytest'in fonksiyon-başına-taze-state garantisiyle aynı.

### `pre_config` ve `post_check` — asıl fixture karşılığı

`add_config`'in en değerli ama en çok gözden kaçan kısmı. Python callback'leri:

```python
def make_hooks(depth, width):
    def pre_config(output_path):
        # Simülasyon BAŞLAMADAN önce çalışır.
        # Test vektörünü burada üret — VHDL'e gömme, Python'da hesapla.
        data = np.random.default_rng(0).integers(0, 2**width, depth)
        np.savetxt(Path(output_path) / "input.csv", data, fmt="%d")
        return True   # False dönerse test fail sayılır

    def post_check(output_path):
        # Simülasyon BİTTİKTEN sonra çalışır.
        actual = np.loadtxt(Path(output_path) / "output.csv")
        expected = golden_model(data)
        return np.array_equal(actual, expected)   # bool dönmeli

    return pre_config, post_check

pre, post = make_hooks(64, 8)
tb.add_config(
    name="d64_w8",
    generics=dict(G_DEPTH=64, G_WIDTH=8),
    pre_config=pre,
    post_check=post,
)
```

`output_path` her config için **ayrı bir dizindir** — VUnit sağlar, çakışma olmaz,
paralel koşuda güvenlidir. Testbench'in dosyaları nerede bulacağını bilmesi için
`tb_path` veya kendi generic'inle yolu VHDL'e de geçebilirsin.

Bu yapının asıl gücü: **karşılaştırma mantığı Python'da kalır.** NumPy'ın tamamı
elinin altındadır. VHDL sadece çıktıyı dosyaya döker; doğrulamayı Python yapar.

### Generic mi, dosya mı?

- **Yapıyı değiştiren** (port genişliği, bellek derinliği, pipeline aşaması) →
  **generic** olmalı, başka yolu yok, elaboration zamanı bilgisidir
- **Sadece veri olan** (test vektörü, beklenen çıktı, konfigürasyon kelimesi) →
  **dosya** tercih et

İkincisi için generic kullanmak cazip görünür ama her değer yeni elaboration
demektir. 300 farklı config word'ü generic'le geçirirsen 300 elaboration ödersin;
dosyadan okursan 1.

### `run.py` iskeleti

```python
from pathlib import Path
from vunit import VUnit

ROOT = Path(__file__).parent

vu = VUnit.from_argv()
vu.add_vhdl_builtins()              # check, log, run kütüphaneleri
vu.add_verification_components()    # AXI-S, Avalon vb. VC'ler
vu.add_osvvm()                      # rastgele sayı, coverage (isteğe bağlı)

lib = vu.add_library("lib")
lib.add_source_files(ROOT / "src" / "*.vhd")
lib.add_source_files(ROOT / "tb" / "*.vhd")

tb = lib.test_bench("tb_fifo")
for depth in [8, 64]:
    tb.add_config(name=f"d{depth}", generics=dict(G_DEPTH=depth))

vu.main()
```

`vu.main()` argümanları kendisi işler:

| Argüman | İşlev |
|---|---|
| `-p 8` | 8 paralel süreç |
| `-v` | Ayrıntılı çıktı |
| `--list` | Test listesini göster, koşma |
| `--compile` | Sadece derle |
| `"*pattern*"` | Test filtresi (pozisyonel) |

---

## 6. Parametrizasyon: manifest döngüsü

### Sorun

Konfigürasyon bir veri yolu üzerinden (örneğin bir config port'una yazılan
tek-atımlık kelime) geliyorsa ve yüzlerce kombinasyon varsa, her biri için ayrı
`add_config` yazmak 300 elaboration demektir. Yapı değişmediği halde.

### Çözüm

Vaka sayısı kadar dosya değil, **vaka sayısı kadar satır** üret:

```
case_id, config_word, input_file,       expected_file
0,       0x0041,      pool/rand_00.csv, exp/000.csv
1,       0x0042,      pool/rand_00.csv, exp/001.csv
2,       0x0081,      pool/rand_01.csv, exp/002.csv
```

**Dikkat:** giriş verisi tekrar kullanılıyor. Config değişiyor ama aynı girişi
besliyorsan, 300 vaka için 5–10 giriş dosyası yeter. Sadece beklenen çıktılar
farklıdır. Bu tek başına dosya sayısını ciddi biçimde düşürür.

Testbench manifest'i satır satır okur, döngüde işler. Yeni vaka eklemek = Python
tarafında bir satır, VHDL'e dokunmadan.

### Config paketleme

Konfigürasyonu Python'da yapılandırılmış tut:

```python
@dataclass(frozen=True)
class Config:
    mode: int
    scale: int
    threshold: int

    def to_word(self) -> int:
        """VHDL'e giden bit paketi."""
        return (self.threshold << 8) | (self.scale << 4) | self.mode
```

`to_word` için **ayrı pytest yaz** (bilinen config → bilinen hex değer). VHDL
tarafı paketi kendi field tanımlarıyla açar; iki taraf uyuşmazsa test patlar — ama
hangi tarafın yanlış olduğunu bilmek için Python tarafının bağımsız testi gerekir.

### Config uzayını küçültmek

"Yüzlerce vaka" genellikle alanların kartezyen çarpımıdır. Önce ayrıştır:

**Hangi alanlar birbirini etkiliyor?** Bazı alanlar birbirine bağlıdır (boyut →
aşama sayısı → ölçekleme genişliği). Bazıları tamamen bağımsızdır (threshold ile
yön bayrağı). Bağımsız alanları çaprazlamak boşa koşudur.

Etkileşimi olmayan alanlar için **pairwise (all-pairs)** yeterlidir. Mantığı:
bug'ların ezici çoğunluğu tek bir parametre değerinden veya *iki* parametrenin
belirli kombinasyonundan çıkar; 3+ yönlü etkileşim nadirdir. Tüm 2'li
kombinasyonları kapsayan küme çok daha küçüktür — 4 alan × 5'er değer = 625 yerine
~25 vaka.

Python'da `allpairspy` kullanılabilir. Etkileşimli alan gruplarını tam çaprazla,
gruplar arasını pairwise bağla.

### Kapsama takibi

Hangi alan değerlerinin gerçekten koşulduğunu Python tarafında say:

```python
from collections import Counter
c = Counter(cfg.scale for cfg in cases)
# scale: 12 farklı değer tanımlı, 8'i test edildi → eksik olan hangileri?
```

HDL tarafında functional coverage aramaya gerek yok; manifest'i sen ürettiğin için
kapsama zaten Python'da bilinebilir bir şeydir.

### Manifest'in yakalayamayacağı şeyler

Bunlar ayrı, elle yazılmış testler olmalı — bug yoğunluğu bakımından genellikle
300 geçerli config'ten daha verimlidir:

- **Geçersiz/rezerve config değeri** → DUT ne yapıyor? Bayrak mı kaldırıyor,
  kırpıyor mu, sessizce garip mi davranıyor? Tanımlı davranış yoksa spec eksiktir.
- **Frame ortasında config yazması** → kabul mü, frame bitene kadar bekletme mi?
- **Config hiç yazılmadan veri gelmesi** → reset sonrası varsayılan var mı?
- **Arka arkaya iki config, arada veri yok** → ikincisi birinciyi eziyor mu?
- **Aynı config'in iki kez yazılması** → idempotent mi?
- **Config yazması sırasında backpressure** → `tready` düşükken ne oluyor?

---

## 7. Hangisini ne zaman? Karar rehberi

| Yapı | Elaboration | Paralellik | İzolasyon |
|---|---|---|---|
| Ayrı test case'ler (`add_config`) | N adet | ✅ Tam | ✅ Tam |
| `run_all_in_same_sim` | 1 | ❌ Yok | ❌ Yok |
| Manifest döngüsü + shard | Shard sayısı | ✅ Var | ❌ Yok (içeride) |

> **Önemli:** Paralellik ile state izolasyonu **bağımsız iki konudur.** Biri
> diğerini gerektirmez. Manifest döngüsü izolasyonu kaybettirir ama paralelliği
> kaybettirmez.

### VUnit'in izolasyon birimi

VUnit için atomik birim **test case**'dir: bir `run()` bloğu × bir config. Her test
case kendi simülatör sürecinde, kendi `output_path`'inde koşar. `-p N` bu
granülerlikte paralelleştirir.

Test case'in *içinde* ne olduğu VUnit'i ilgilendirmez. Tek bir test case içinde 300
kez döngü kurmuşsan, VUnit bunu tek bir iş olarak görür.

### Manifest'i paralelleştirme (sharding)

Manifest'i bölerek paralellik geri kazanılır:

```python
N_SHARD = 8

def make_manifest_writer(shard, n_shard):
    def pre_config(output_path):
        my_cases = all_cases[shard::n_shard]      # her shard'a ~1/8
        write_manifest(Path(output_path) / "manifest.csv", my_cases)
        return True
    return pre_config

for shard in range(N_SHARD):
    tb.add_config(
        name=f"shard{shard}",
        generics=dict(G_SHARD_ID=shard),
        pre_config=make_manifest_writer(shard, N_SHARD),
    )
```

Sonuç: 8 elaboration, 8 paralel süreç, her biri ~37 vaka döngüsü. 300 elaboration
yerine 8.

Shard sayısı çekirdek sayısıyla eşleşsin.

### Seçim kuralı

**`add_config` kullan:**
- Yapısal parametre (generic) değişiyorsa — zorunlu
- Testlerin tam izolasyonu gerekiyorsa
- Bir test'in çökmesi diğerlerini etkilememeliyse
- Vaka sayısı düşükse (onlarca)

**Manifest döngüsü kullan:**
- Sadece veri/config değişiyorsa, yapı sabitse
- Çok sayıda vaka varsa (yüzlerce)
- Elaboration süresi simülasyon süresinden uzunsa

**Pratikte çoğu proje ikisini karıştırır:** `add_config` ile birkaç yapısal varyant
(örn. 3 farklı genişlik veya 8 shard), her varyantın içinde manifest'ten okunan
yüzlerce veri vakası.

---

## 8. Test vektörü üretme stratejileri

"Her vaka için ayrı CSV" ölçeklenmez. Alternatifler:

### Alternatif 1 — Manifest + veri havuzu

Yukarıda anlatıldı. Giriş dosyalarını paylaş, sadece beklenen çıktıları ayrı tut.

**Ne zaman:** karmaşık modüller, tam doğrulama şart.

### Alternatif 2 — Girişi VHDL'de üret

Girişin *içeriği* önemli değilse (deterministik ve tekrarlanabilir olması
yeterliyse), CSV'den okuma:

```vhdl
process
  variable lfsr : std_logic_vector(15 downto 0) := x"ACE1";
begin
  -- ...
  lfsr := lfsr(14 downto 0) &
          (lfsr(15) xor lfsr(13) xor lfsr(12) xor lfsr(10));
```

Aynı LFSR'ı Python'da da uygularsın (10 satır), böylece altın model aynı veriyi
görür. **Giriş CSV'si tamamen ortadan kalkar**; sadece beklenen çıktı dosyadan
gelir.

OSVVM'in `RandomPkg`'i de var (`vu.add_osvvm()`), ama Python'da birebir taklidi
zordur — LFSR daha kontrollüdür.

**Ne zaman:** giriş içeriği önemsiz, sadece deterministik olması yeterli.

### Alternatif 3 — Self-checking (dosyasız)

Soru: **çıktının doğruluğunu, tam değerini bilmeden kontrol edebilir misin?**

Çoğu durumda kısmen evet:

```vhdl
check_equal(out_count, in_count, "çıkış örnek sayısı");
check(out_valid_when_tlast, "tlast ile valid hizalı");
check(abs(signed(dout)) <= max_expected, "saturasyon aşılmadı");
```

Bunlara **property check** denir. Tam sonucu doğrulamaz ama:
- Protokol hatalarını yakalar (eksik örnek, yanlış `tlast`, kayıp `valid`)
- Sıfır dosya gerektirir
- Her config'de otomatik çalışır

Bazı modüllerde **tam** self-checking mümkündür: ters işlem varsa
(interpolate→decimate, encode→decode, ileri→geri dönüşüm), çıktıyı geri
dönüştürüp girişle karşılaştırırsın. Dosya gerekmez.

**Ne zaman:** her zaman, geniş kapsama için. Tek başına yeterli değil.

### Alternatif 4 — Tek dosyada tüm vakalar

Vaka başına dosya yerine tek dosya:

```
# expected_all.csv — her satır bir vaka
case_id, sample_0, sample_1, ..., sample_N
0,       123,      -45,      ...
1,       67,       89,       ...
```

Testbench dosyayı bir kez açar, satır satır ilerler. Dosya sistemi yükü sıfıra
yakındır.

**Ne zaman:** çıktı uzunluğu sabit, config'e göre değişmiyor. En az sürtünmeli yol.

### Karar tablosu

| Durum | Yöntem |
|---|---|
| Çıktı uzunluğu sabit | Alt. 4 — tek dosya |
| Giriş içeriği önemsiz | Alt. 2 — LFSR |
| Modülün ters işlemi var | Alt. 3 — round-trip |
| Karmaşık, tam doğrulama şart | Alt. 1 — manifest |
| **Çoğu gerçek proje** | **Alt. 3 (geniş) + Alt. 1 (dar)** |

### Önerilen birleşim

Tüm config'lerde property check koş (dosyasız), seçilmiş 15–20 config'de bit-exact
karşılaştırma yap (dosyalı). Bug'ların çoğu ilkinde çıkar; ikincisi aritmetiği
çiviler.

### Vektörleri nerede üretmeli

`generate_vectors.py`'yi tek bir `main()` değil, `run.py`'nin çağırdığı bir
fonksiyon yap:

```python
from generate_vectors import build_vectors

def pre_config(output_path):
    build_vectors(output_path, cases=CASES)
    return True
```

Böylece vektörler her koşuda taze üretilir, git'e girmez, `output_path` sayesinde
paralel koşuda çakışmaz.

> **Üretilebilir şeyler versiyon kontrolüne girmemeli.** Üretici script'i commit
> et, çıktıyı değil.

---

## 9. State sızıntısı: soğuk ve sıcak döngüler

### Ne zaman gerçekleşir

Manifest döngüsünde her yinelemede DUT'a reset atmıyorsan, vaka N+1 şunları miras
alır:

- **Boşalmamış pipeline** — önceki frame'in son örnekleri hâlâ içeride yolda
- **Boşalmamış FIFO/buffer** — özellikle önceki vaka `tlast` almadan bittiyse
- **Sayaçlar** — frame sayacı, örnek indeksi, adres pointer'ları
- **Kısmi config** — yeni config word tüm alanları yazmıyorsa, yazılmayanlar
  eskiden kalır
- **Akümülatörler** — DC offset takibi, ortalama hesabı gibi durum tutan bloklar
- **Testbench tarafı** — slave VC'nin kuyruğunda okunmamış veri kaldıysa, sonraki
  vaka onu kendi verisi sanır

Son madde özellikle sinsidir: hata testbench'tedir ama DUT hatası gibi görünür.

### Ne zaman gerçekleşmez

- Her yinelemenin başında açıkça reset atılıyorsa (birkaç saat çevrimi, neredeyse
  bedava)
- DUT frame'ler arası durum tutmuyorsa
- Her yineleme `tlast` ile tam kapanıyor ve pipeline boşalıyorsa

### Pratik reçete

```vhdl
for i in 0 to n_cases-1 loop
    -- 1. temizle
    reset_dut;
    -- 2. boşaldığını doğrula
    check_false(m_axis_tvalid, "reset sonrası bekleyen veri yok");
    -- 3. vakayı koş
    apply_config(manifest(i).cfg);
    stream_data(manifest(i));
    collect_and_dump(i);
end loop;
```

İkinci adım kritiktir: sızıntıyı **oluştuğu anda** yakalar, üç vaka sonra garip bir
sonuç olarak değil.

### Soğuk ve sıcak döngü — ikisi de gerekli

Sızıntıyı tamamen ortadan kaldırmak her zaman istenen şey değildir. Reset atmadan
arka arkaya config değiştirmek, gerçek kullanımda olacak şeydir — ve **yeniden
konfigürasyon bug'ları** ancak böyle yakalanır.

| Döngü | Reset | Ne doğrular |
|---|---|---|
| **Soğuk** | Her vakada | Aritmetiği; hata izole edilebilir |
| **Sıcak** | Yok | Yeniden konfigürasyon sağlamlığını |

Aynı manifest, iki farklı config:

```python
for mode, reset_each in [("cold", True), ("warm", False)]:
    tb.add_config(name=mode, generics=dict(G_RESET_EACH=reset_each))
```

**Debug refleksi:** hata çıktığında aynı vakayı soğuk döngüde koştur.
- Geçiyorsa → bug state yönetiminde
- Geçmiyorsa → bug hesaplamada

Debug alanını ikiye böler.

---

## 10. Paralelleştirme ve hız

### Asıl kaldıraç

```bash
python run.py -p 8
```

VUnit her test case'i ayrı süreçte, ayrı çıktı dizininde koşturur — çakışma olmaz.
Tek çekirdekten 8'e çıkmak kabaca 8x'e yakın kazanç verir.

**Bellek sınırına dikkat:** her simülatör süreci kendi elaborated tasarımını
tutar. 16 çekirdekli ama 8 GB RAM'li bir makinede `-p 16` swap'e düşürebilir.

### Diğer kaldıraçlar

**Dalga formu dökümünü kapat.** Varsayılan kapalı olsun; sadece hata ayıklarken
aç. Yüzlerce koşuda FST/VCD yazımı toplam sürenin büyük kısmını yiyebilir.

**Elaboration maliyetini hesapla.** 300 konfigürasyonun hepsi aynı testbench'se ve
her biri 50 ms simüle ediliyorsa, elaboration süresi simülasyon süresini gölgede
bırakır → manifest döngüsüne geç.

**Vektörleri küçük tut.** Bit-exact karşılaştırmada küçük N yeter; büyük N aynı
aritmetik yolu kullanır, ek bilgi vermez.

### `run_all_in_same_sim` hakkında

```python
tb.set_attribute(".run_all_in_same_sim", None)
```

Aynı testbench'teki tüm test case'leri tek simülasyonda koşturur. Elaboration'ı
teke indirir **ama paralelliği de öldürür** ve testler izole olmaz; bir çökme
tümünü düşürür.

Manifest döngüsü + sharding genellikle daha iyi bir dengedir.

---

## 11. Docker: ne zaman, ne için

### Hız kazandırmaz

Container bir sanal makine değil, aynı kernel üzerinde izole edilmiş bir süreçtir.
Simülatör container içinde de dışında da **aynı hızda** koşar.

Windows'taysan WSL2 üzerinden koşar ve **dosya sistemi sınırını geçerse yavaşlar**:
`/mnt/c/...` üzerinden çalışmak ciddi I/O cezasıdır. Tüm projeyi WSL'in kendi
dosya sisteminde tut.

### Asıl faydası: tekrarlanabilirlik

- Sunucuda ve yerel makinede **birebir aynı simülatör sürümü** — "bende geçiyor,
  CI'da patlıyor" durumunun büyük kısmı sürüm farkından çıkar
- Bir yıl sonra eski bir commit'e dönüldüğünde aynı ortamı yeniden kurabilmek
- Sunucuya simülatör + Python + VUnit kurma zahmetinin ortadan kalkması
- Yeni bir simülatör sürümünü, mevcut kurulumu bozmadan denemek (iki tag paralel
  dursun)

### Karar

| Ortam | Docker? |
|---|---|
| CI / sunucu | ✅ Evet |
| Günlük yerel geliştirme | ❌ Gereksiz sürtünme |

Yerelde `pip install vunit_hdl` + sistem simülatörü ile çalış; sunucuda container
kullan.

### Kendi imajın

Resmi imaj VUnit'i içermiyorsa üç satır yeterlidir:

```dockerfile
FROM ghcr.io/<simulator-image>:<tag>
RUN pip install --no-cache-dir vunit_hdl numpy
WORKDIR /work
```

Tag'i sabitle (`:latest` kullanma) — tekrarlanabilirliğin bütün amacı bu.

---

## 12. Uzak sunucuda çalıştırma

### Baştaki çelişki

"Kaynak kod bende kalsın ama sunucuda çalıştırayım" — bu ikisi aynı anda mümkün
değil. Simülatör kodu derlemek zorundadır, dolayısıyla **kod bir şekilde sunucuya
gidecektir.**

Doğru soru: *"nasıl ve ne kadar kalıcı?"* Niyet genellikle "tek doğru kopya bende
olsun, sunucu geçici çalışma alanı olsun" — bu tamamen makuldür.

### Seçenekler

**rsync + SSH (en basit, en öngörülebilir):**

```bash
rsync -az --delete --exclude 'vunit_out' ./ user@server:/tmp/work/
ssh user@server 'cd /tmp/work && python run.py -p 16'
rsync -az user@server:/tmp/work/vunit_out/ ./vunit_out/
```

Üç satırlık script. Sunucudaki kopya geçicidir (`/tmp`), iş bitince silinebilir.
Git geçmişi, branch'ler, her şey sende kalır.

**VS Code Remote-SSH:** Editör yerelde görünür ama dosyalar sunucuda durur. Konfor
iyidir ama "kod bende kalsın" hedefine terstir — asıl kopya sunucuda olur.

**Git tabanlı:** Sunucuda bare repo, `git push` sonrası hook tetikler. Daha
temizdir ama kurulumu uzundur.

**sshfs / NFS mount:** ❌ **Kullanma.** Derleme binlerce küçük dosya I/O'su yapar;
ağ dosya sistemi üzerinde felaket yavaş olur. rsync'ten kat kat kötüdür.

### Önemli detay

**Test vektörlerini sunucuda üret.** `generate_vectors.py`'yi `run.py`'nin
öncesinde (veya `pre_config` içinden) koştur. Yüz megabaytlık CSV'yi ağ üzerinden
taşımanın anlamı yok; NumPy zaten orada saniyede üretir.

---

## 13. Waveform: dökme, görüntüleme, debug akışı

### Yanlış anlaşılan nokta

Açık kaynak simülatörlerin (NVC, GHDL) **waveform üretme özelliği vardır** —
olmayan şey, gömülü bir GUI'dir. Simülatör dosyayı döker, görüntülemeyi ayrı bir
araç yapar. Ticari simülatörlerde bu ikisi tek pakette olduğu için "waveform yok"
izlenimi doğar.

### Formatlar

| Format | Not |
|---|---|
| **FST** | Varsayılan. Binary, sıkıştırılmış, küçük ve hızlı. Tercih edilen. |
| **VCD** | Çok yaygın ama HDL tiplerini temsil etmekte sınırlı ve yavaş. Sadece FST desteklemeyen bir araca çıktı vermen gerekiyorsa. |
| **GHW** | GHDL'e özgü. NVC desteklemez. |

NVC komut satırında:

```bash
nvc -r --wave=out.fst --format=fst tb_top
```

Dosya adı verilmezse top-level birimin adı kullanılır.

### Görüntüleyici: Surfer

Modern, açık kaynak dalga formu görüntüleyicisi. VCD, FST ve GHW okur. Windows,
macOS ve Linux'ta native çalışır; ayrıca **tarayıcıda** ve **VS Code eklentisi**
olarak da kullanılabilir. Klavye odaklı bir komut paleti arayüzü vardır (VS
Code'daki Ctrl-P mantığı).

GTKWave da bir alternatiftir; FST için 3.3.79 veya sonrası gerekir.

**Kurulum:**

```bash
cargo install --git https://gitlab.com/surfer-project/surfer surfer
# macOS:
brew install surfer
# veya VS Code'da "surfer" eklentisi
```

Hızlı denemek için kurulum bile gerekmez: tarayıcı sürümüne dosya sürükleyip
bırakabilirsin.

### VUnit entegrasyonu

VUnit'in açık kaynak simülatörler için hazır bayrakları var:

| Bayrak | İşlev |
|---|---|
| `--viewer-fmt {vcd,fst,ghw}` | Hangi formatta dökülecek (NVC'de ghw yok) |
| `--viewer` | Hangi görüntüleyici çalıştırılacak |
| `--viewer-args` | Görüntüleyiciye geçirilecek argümanlar |
| `-g` / `--gui` | Testi koştur, dök, görüntüleyiciyi aç |

`run.py` içinde kalıcı ayar:

```python
lib.set_compile_option("nvc.viewer", "surfer")
```

Bu verilmezse VUnit sistemde gtkwave veya surfer'ı kendisi arar. Komut
satırındaki `--viewer` her zaman önceliklidir.

### Hızlı debug akışı — tek bir config patladığında

**1. Tam test adını al.** VUnit hata çıktısında zaten yazar:

```
fail (1/312) lib.tb_dut.shard3.config_id=47
```

**2. Sadece o testi, dalga dökümüyle yeniden koştur:**

```bash
python run.py "lib.tb_dut.shard3.config_id=47" --viewer-fmt fst -g
```

> **Filtre olmadan `-g` kullanma** — 312 test için 312 pencere açmaya kalkar.

**3. Zaman damgasına atla.** Burası en çok zaman kazandıran adım. VUnit'in
`check_equal` hatası sana **tam simülasyon zamanını** verir:

```
1234 ns - check_equal failed! Got 42. Expected 37.
```

Görüntüleyicide doğrudan o zamana git (Surfer'da komut paletinden `goto`). Baştan
sona tarama yapma.

### Dosya boyutunu kontrol etme

Varsayılan olarak **tüm hiyerarşi** dökülür. Büyük tasarımlarda bu gereksiz
yavaşlıktır. NVC glob tabanlı sinyal seçimi sunar:

```python
tb.set_sim_option("nvc.sim_flags", [
    "--include=*dut*",        # sadece DUT hiyerarşisi
    "--exclude=*vc_*",        # VC iç sinyalleri gereksiz
])
```

**Diziler için ayrı not:** `--dump-arrays` verilmezse dizi sinyalleri dökülmez.
Test vektörünü tutan bir dizi sinyalini görmek istiyorsan bu bayrak gerekir — ama
dosyayı ciddi şişirir. Sadece ihtiyaç anında aç.

### Uzak sunucu senaryosu

Bölüm 12'deki akışa doğrudan oturur. Surfer'ı waveform'un bulunduğu makinede
sunucu modunda başlatıp başka bir makineden bağlanabilirsin — **dosyayı
kopyalamana gerek kalmaz**:

```bash
# sunucuda:
surfer server --file waveform.fst
# veya stand-alone sunucu versiyonu (surver):
surver waveform.fst
```

Sonra yerelden bağlanırsın. 500 MB'lık bir FST'yi rsync'lemek yerine bu yolu
kullan — büyük dosyalarda fark ciddidir.

### Ne zaman waveform'a bakmamalısın

**Bu bölümün en önemli kısmı.** Bit-exact CSV karşılaştırma akışında waveform
genellikle **ikinci** adımdır, birinci değil.

Bir vaka patladığında ilk hamle Python olmalı:

```python
diff = np.nonzero(actual != expected)[0]
print(f"ilk sapma: index {diff[0]}, got {actual[diff[0]]}, exp {expected[diff[0]]}")
print(f"toplam {len(diff)}/{len(expected)} örnek yanlış")
```

Bu tek çıktı hatanın karakterini söyler:

| Desen | Muhtemel sebep | Waveform gerekli mi? |
|---|---|---|
| Sadece ilk N örnek yanlış | Latency / pipeline hizalama | ❌ Hayır |
| Hepsi sabit offset kadar kaymış | İndeksleme hatası | ❌ Hayır |
| Tek bir örnek yanlış | Köşe durumu | ⚠️ Sadece o zamana git |
| Ortadan itibaren hepsi bozuk | State sızıntısı veya taşma | ⚠️ Sapma noktasına git |
| Rastgele dağılmış | Protokol / handshake sorunu | ✅ **Vazgeçilmez** |

İlk iki durumda waveform açmak zaman kaybıdır. Son durumda vazgeçilmezdir.

Ayrıca: bazen **property check** daha da hızlıdır. `check_equal(out_count,
in_count)` gibi bir kontrol, "hangi örnek yanlış" sorusundan önce "kaç örnek
geldi" sorusunu cevaplar ve çoğu protokol bug'ını waveform'a hiç bakmadan yakalar.

### Alışkanlık

Dalga dökümünü **hiçbir zaman varsayılan açık bırakma.** Regresyonda kapalı olsun;
sadece hata ayıklarken, tek test için aç. Yüzlerce vaka koşarken FST yazımı toplam
sürenin büyük kısmını yiyebilir (bkz. bölüm 10).

`run.py`'ye bir kısayol koymak işe yarar:

```python
# python run.py --debug-case 47   şeklinde kullanım için
if args.debug_case is not None:
    # sadece o vakayı içeren tek bir config üret, dump açık
```

Böylece "47 numaralı vakayı incele" tek komuta iner.

---

## 14. Öğrenme sırası

VUnit'in yüzey alanı geniştir; hepsini birden öğrenmeye çalışma.

| # | Konu | Not |
|---|---|---|
| 1 | `run.py` + tek testbench + `run()` blokları | Koşuyor mu? |
| 2 | `check_equal`, `check_true` | `assert` yerine bunlar — VUnit sayar ve raporlar |
| 3 | `add_config` + generic | Parametrizasyon |
| 4 | `pre_config` / `post_check` | **Python'a bağlanma — asıl değerli kısım** |
| 5 | `integer_array_pkg` + `load_csv` | Dosyadan veri |
| 6 | Verification components (AXI-S master/slave) | Protokol sürme |
| 7 | `log()`, `set_log_level`, logger hiyerarşisi | Debug ergonomisi |
| 8 | `--viewer-fmt` + `-g` + Surfer | Waveform debug — ama önce Python diff (bkz. bölüm 13) |

İlk üçü bir günde oturur. 4–5 Python/NumPy tabanlı bir akış için asıl değerli
kısımdır. 6, protokol testine geçildiğinde gelir.

### Kaynaklar

VUnit'in kendi kaynak deposundaki **`examples/vhdl/`** dizini en iyi
dokümantasyondur. Özellikle:

- `array_axis_vcs` — CSV veri + AXI-Stream VC kombinasyonu
- `com` — mesajlaşma tabanlı testbench mimarisi
- `generate_tests` — `add_config` kullanım örnekleri

---

## Özet: temel prensipler

1. **Satıcı IP'sini doğrulamak senin işin değil** — izole et, kendi mantığını test
   et. Kısıtlama doğru mimariyi dayatıyor.
2. **Bit-exact ve istatistiksel doğrulama ayrı katmanlardır.** İkincisi HDL
   simülasyonuna girmez.
3. **Tolerans girdiğin an belirsizlik başlar.** Fixed-point altın model yaz,
   tamsayı karşılaştır.
4. **Karşılaştırma mantığı Python'da kalsın.** VHDL döker, Python doğrular.
5. **Yapısal parametre → generic. Veri → dosya.**
6. **Paralellik ve izolasyon bağımsızdır.** Manifest izolasyonu kaybettirir,
   paralelliği değil.
7. **Soğuk ve sıcak döngü ikisi de gerekli.** Biri aritmetiği, diğeri state
   yönetimini doğrular.
8. **Üretilebilir şeyler git'e girmez.** Script'i commit et, vektörü değil.
9. **Waveform son çare değil ama ilk çare de değil.** Önce Python'da fark
   desenine bak; waveform'u ancak desen protokol sorununa işaret ettiğinde aç.
