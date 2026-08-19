# AXI4-Stream — skid buffer ve VUnit doğrulaması

Bu belge, `axis_skid_buffer` üzerinden AXI4-Stream öğrenirken çıkan
kararların ve hataların kaydı. Amaç tasarım değil; **protokolü ve onu
doğrulayan testbench'i** oturtmak.

> Kök dizindeki `README.md`'yi ezmemek için ayrı ad verildi.
> `docs/axi_stream.md` olarak taşınabilir.

```
hdl/
├── src/axis_skid_buffer.vhd          # DUT
└── tb/
    ├── tb_axis_skid_buffer.vhd       # elle yazilan TB (cevrim seviyesi)
    └── tb_axis_skid_buffer_vc.vhd    # VUnit VC'li TB (veri + protokol)
```

---

## 1. Protokolün tek asimetrisi

AXI-Stream'de `tvalid` üreticiden, `tready` tüketiciden gelir. İkisi
simetrik **değildir**:

| | İzinli mi | Neden |
|---|---|---|
| Slave, `tvalid`'i görüp sonra `tready` kaldırır | **evet** | karar için veriye bakması gerekebilir |
| Master, `tready`'yi görüp sonra `tvalid` kaldırır | **hayır** | ikisi de beklerse bus sonsuza kadar kilitlenir |

Spec üreticiyi **koşulsuz** ilan ederek kilidi imkânsız kılıyor. Bunun
doğrudan sonucu şu kural:

> `tvalid = '1'` ve `tready = '0'` iken `tdata`, `tlast`, `tkeep`, `tid`…
> **değişemez**. `tvalid` de geri çekilemez; el sıkışma tamamlanana kadar
> asılı kalır.

İhlalin somut zararı:

```
        __    __    __    __
clk   _|  |__|  |__|  |__|  |__
tvalid ______/‾‾‾‾‾‾‾‾‾‾‾‾‾\____
tdata  --< A       >< B    >----      <-- IHLAL
tready ____________/‾‾‾‾‾\__________
                         ^ hangi veri transfer edildi?
```

A hiç transfer edilmeden kayboldu. Üstelik slave `tready`'yi A'ya bakarak
kaldırdıysa, **B için verilmiş bir izinle A'nın kararını** uygulamış oldu.

---

## 2. Skid buffer neden var

`tready`'yi aşağı akıştan yukarı akışa **kombinasyonel** geçirirsen iki
ayrı sorun doğar:

1. **Zamanlama.** `ready` yolu tipik bir AXI sisteminde en uzun kritik
   yoldur; on modül peş peşe bağlanırsa hepsinin mantığı üst üste biner.
2. **Doğruluk.** Slave `tready`'yi `tvalid`'e bakarak kaldırabiliyordu
   (bölüm 1'deki izin). Sen de `tvalid`'i `tready`'ye kombinasyonel
   bağlarsan → `tvalid → tready → tvalid` **kombinasyonel loop**.

Çözüm `ready`'yi register'lamak. Ama o anda "duramam" haberi yukarı akışa
bir çevrim geç ulaşır — ve yukarı akış o çevrimde bir beat daha
göndermiştir. Onu koyacak bir yer gerekir. Adı buradan geliyor: frene
bastıktan sonra aracın kaydığı mesafeyi soğuran tampon.

**Neden tam iki kayıt:** `m_axis_tready` çevrim N'de düşerse, çevrim N'de
`s_axis_tready` hâlâ `'1'`dir → bir beat skid'e girer. Çevrim N+1'de
`s_axis_tready = '0'` olur → üçüncü beat gelemez. Üçüncü bir kayıt hiçbir
zaman yazılmazdı.

---

## 3. Tasarımın tamamı dört durumda

| `reg` | `skid` | `s_axis_tready` | `m_axis_tvalid` | çıkış boşalıyorsa kenarda ne olur |
|---|---|---|---|---|
| boş | boş | `1` | `0` | girişten gelen beat → `reg` |
| dolu | boş | `1` | `1` | girişten gelen beat → `reg` (tam hız) |
| dolu | dolu | **`0`** | `1` | `skid` → `reg`, skid boşalır |
| boş | dolu | — | — | **ulaşılamaz** |

Son satır önemli: `skid`'e ancak `reg` doluyken yazılır ve `skid` yalnızca
`reg`'e boşalır. Bu değişmez sayesinde `m_axis_tvalid` sadece `reg_valid`
olabiliyor.

Kombinasyonel çıkışlar yalnızca **kayıtlara** bakar — ne `s_axis_tvalid`
ne `m_axis_tready` bu ifadelerde geçer:

```vhdl
s_axis_tready <= not skid_valid;

m_axis_tvalid <= reg_valid;
m_axis_tdata  <= reg_data;
m_axis_tlast  <= reg_last;
```

Kenarda sorulan tek soru: **"çıkış yuvası bu kenarda boşalıyor mu?"**

```vhdl
elsif reg_valid = '0' or m_axis_tready = '1' then     -- (a) bosaliyor
  if skid_valid = '1' then
    reg_data <= skid_data; ... ; skid_valid <= '0';   -- SIRA BURADA KORUNUR
  elsif s_axis_tvalid = '1' then
    reg_data <= s_axis_tdata; ...                     -- skid bos => tready '1'
  else
    reg_valid <= '0';
  end if;
else                                                   -- (b) tikali
  if s_axis_tvalid = '1' and skid_valid = '0' then
    skid_data <= s_axis_tdata; ... ; skid_valid <= '1';
  end if;
end if;
```

### Yapılan hata: çıkışta mux

İlk sürümde çıkış şöyleydi:

```vhdl
-- YANLIS
m_axis_tdata <= skid_data when skid_valid = '1' else reg_data;
```

`reg` **önce** dolar (eski beat), `skid` **sonra** dolar (yeni beat). Mux
skid'e öncelik verince yeni beat eskisinden önce çıkar:

| çevrim | `m_tready` | `s_tdata` | kenarda ne olur | çevrim başı çıkış |
|---|---|---|---|---|
| 1 | 0 | A | `reg <= A` | — |
| 2 | 0 | B | `skid <= B` | `A` |
| 3 | 1 | — | `skid_valid <= '0'` | **`B`** ← A'dan önce |
| 4 | 1 | — | `reg_valid <= '0'` | `A` |

Çıkış sırası **B, A**. Veri kaybı yok, **sıra bozuk** — sayım tabanlı bir
testin göremediği hata sınıfı. Doğrusu: çıkışta mux yok, `skid` çıkışa
değil `reg`'e boşalır.

---

## 4. Testbench örnekleme konvansiyonu

Bu dosyaların en önemli tek kuralı.

```vhdl
wait until rising_edge(clk);
-- burada okunan degerler, kenarin GORDUGU (kenar oncesi) degerlerdir
```

| Ne okuyorsun | Ne zaman |
|---|---|
| **El sıkışma** (`tvalid`/`tready`) ve transfer edilen `tdata` | `wait until rising_edge(clk)` sonrası, **gecikmesiz** |
| Kenarın **ürettiği** kayıtlı çıkış | `wait for 1 ns` sonrası |

Döngü iskeleti:

```vhdl
-- 1) bu cevrimin uyaranini sur
-- 2) wait until rising_edge(clk);
-- 3) el sikismalari degerlendir, check yap
```

> **TUZAK:** `wait for 1 ns` ekleyip el sıkışma okumak, kenarın *sonucunu*
> okumak demektir — bir çevrim ileri kayarsın ve henüz gerçekleşmemiş bir
> transferi olmuş sayarsın.

Bu hata bu projede şöyle tezahür etti: çıkış el sıkışması bir çevrim erken
sayıldığı için `rx_index`, `tx_index`'e yetişti; stall koşulu
`tx_index > rx_index` **hiçbir zaman** doğru olmadı; `geri_basinc...` adlı
test hiç geri basınç uygulamadı.

### Testbench'in kendisi de protokole uymak zorunda

Master sürücüsü rastgele `tvalid` toggle edemez — asılı bir beat'e
dokunulmaz. Kabarcık yalnızca beat'ler **arasına** konur:

```vhdl
if not tx_active and tx_index <= C_BEATS then
  rand_bool(0.75, do_it);
  if do_it then
    s_axis_tdata  <= beat_value(tx_index);
    s_axis_tvalid <= '1';
    tx_active     := true;      -- artik dokunulmaz
  end if;
end if;
```

Protokolü ihlal eden bir testbench, DUT'u haksız yere suçlar.

---

## 5. Ölçmeyen test kalıpları (hepsi bu projede yakalandı)

### Totoloji — kendi sürdüğün sinyali kontrol etmek

```vhdl
s_axis_tdata <= std_logic_vector(to_unsigned(i, 8));
wait until rising_edge(clk);
check_equal(to_integer(unsigned(s_axis_tdata)), i, "...");   -- YANLIS
```

DUT tamamen sökülse bu test geçer. Refleks soru: **bu check'i geçmek için
DUT'un var olması gerekiyor mu?**

### Vakumda geçen test — döngüye hiç girmemek

```vhdl
while s_axis_tready = '0' loop      -- s_axis_tready = not skid_valid = '1'
  check_equal(...);                 -- hic calismaz
end loop;
```

Sıfır `check` çağıran test **geçer**. Doğru koşul çıkış tarafındaydı:

```vhdl
while m_axis_tvalid = '1' and m_axis_tready = '0' loop
```

### Hatayı şartname olarak kodlamak

```vhdl
m_axis_tready <= '0';
check_equal(m_axis_tvalid, '0', "...");   -- protokol ihlalini "dogru" ilan eder
```

`tready` düşükken `tvalid` **'1' kalmalı**. Test tam tersini bekliyordu.

### DUT çıkışını sürmek

```vhdl
m_axis_tvalid <= '1';    -- bu bir DUT OUTPUT'u
m_axis_tdata  <= x"42";
```

`std_logic` çözümlü olduğu için simülasyon patlamaz, sessizce `'X'`
üretir. Kural: testbench yalnızca `in` portlarını sürer, `out` portlarını
okur.

### İsim vaadi

`geri_basinc_altinda_veri_kaybetmez` adlı test hiçbir veriyi geri
okumuyordu. İddiayı ölçmenin tek yolu: N beat gönder, stall uygula,
çıkıştan N beat topla, **diziyi** karşılaştır.

---

## 6. Sürekli protokol denetçisi (elle)

Testlerden bağımsız, her çevrimde koşar. Tek kural denetler:

```vhdl
protocol_checker : process
  variable prev_valid : std_logic := '0';
  variable prev_ready : std_logic := '0';
  variable prev_data  : std_logic_vector(C_DATA_WIDTH-1 downto 0);
begin
  wait until rising_edge(clk);
  if reset = '1' then
    prev_valid := '0';
  else
    if prev_valid = '1' and prev_ready = '0' then
      check_equal(m_axis_tvalid, '1', "PROTOKOL: el sikisma olmadan tvalid geri cekildi");
      check_equal(m_axis_tdata, prev_data, "PROTOKOL: el sikisma beklenirken tdata degisti");
    end if;
    prev_valid := m_axis_tvalid;
  end if;
  prev_ready := m_axis_tready;
  prev_data  := m_axis_tdata;
end process;
```

VUnit'in `axi_stream_protocol_checker`'ının yaptığı işin en küçük hali.
Önce bunu yazmak, VC kırmızıya döndüğünde mesajın ne dediğini anlamayı
sağlıyor.

---

## 7. VUnit Verification Component'ları

### Kurulum

```python
def add_project_sources(vu):
    vu.add_vhdl_builtins()
    vu.add_verification_components()   # VC'ler BUNSUZ derlenmez
```

VHDL tarafı:

```vhdl
library vunit_lib;
context vunit_lib.vunit_context;
context vunit_lib.com_context;      -- `net` sinyali buradan gelir
use vunit_lib.axi_stream_pkg.all;
use vunit_lib.stream_master_pkg.all;
use vunit_lib.stream_slave_pkg.all;
use vunit_lib.sync_pkg.all;
```

> **TUZAK:** `use vunit_lib.stall_pkg.all;` **yazma.** Ayrı bir `stall_pkg`
> yok; `stall_config_t` ve `new_stall_config` zaten `axi_stream_pkg`
> üzerinden görünür. Yazarsan `design unit STALL_PKG not found` alırsın.
>
> Hata `stall_pkg`'yi işaret ediyorsa VC'ler derlenmiş demektir — `use`
> sırasında ondan önceki `axi_stream_pkg` geçmiş olur. Hangi paketin nerede
> olduğunu bulmak için:
> ```powershell
> $vu = python -c "import vunit, pathlib; print(pathlib.Path(vunit.__file__).parent)"
> Select-String -Path "$vu\vhdl\verification_components\src\*.vhd" -Pattern "new_stall_config"
> ```

### Kullanım

```vhdl
constant axis_master : axi_stream_master_t := new_axi_stream_master(
  data_length => C_DATA_WIDTH, stall_config => master_stall);

-- ...

push_axi_stream(net, axis_master, beat_value(i), tlast => '0');
check_axi_stream(net, axis_slave, beat_value(i), tlast => '0',
                 msg => "beat " & integer'image(i));
```

`push_axi_stream` **bloklamaz** — 64 beat anında kuyruğa girer, VC onları
kendi uydurduğu zamanlamayla sürer.

VC'ler **aktif-düşük** reset ister: `areset_n <= not reset;`

### Stall neden generic olmak zorunda

```vhdl
constant master_stall : stall_config_t := new_stall_config(
  stall_probability => g_master_stall_prob, ...);
```

`stall_config` VC'ye **elaborasyon zamanında** gömülür — bir `constant`,
bir mesaj değil. Çalışma zamanında değiştirilemez. Testten teste değişmesi
gerekiyorsa generic + `add_config` yolundan geçmek zorunda:

```python
veri_testi = lib.test_bench("tb_axis_skid_buffer_vc").test("veri_butunlugu")
for name, m_prob, s_prob in [("kesintisiz", 0.0, 0.0),
                             ("hafif_stall", 0.2, 0.2),
                             ("agir_stall",  0.6, 0.8)]:
    veri_testi.add_config(name=name,
                          generics={"g_master_stall_prob": m_prob,
                                    "g_slave_stall_prob": s_prob})
```

Katsayı paketi meselesindeki kuralın aynısı: **yapıyı değiştiren
parametre → `add_config`; sabit yapı, değişen veri → manifest döngüsü.**

---

## 8. İşbölümü — iki testbench neden ikisi de duruyor

| | elle yazılan TB | VC'li TB |
|---|---|---|
| Ne doğrular | çevrim seviyesi yapı | veri bütünlüğü + protokol |
| Örnek test | `her_iki_kayit_doluyken_sira_korunur` | `veri_butunlugu` × 3 config |
| Güçlü yanı | hatanın **yerini** söyler | binlerce zamanlama senaryosu bedava |
| Yapamadığı | hacim | "skid tam bu çevrimde dolar" diyemez |

VC zamanlamayı kendi uydurduğu için çevrim sayan iddialar VC'lerle ifade
edilemez. VC'li TB'de tam hız ancak dolaylı ölçülüyor:

```vhdl
t_start := now;
-- 64 beat push + check
check(t_end - t_start <= (C_BEATS + 5) * C_PERIOD, "tam hiz saglanmiyor: ...");
```

Bu, %50 throughput hatasını yakalar ama tek çevrimlik bir boşluğu
yakalamaz. Kural: **yapı elle, hacim VC ile.**

---

## 9. Mutasyon kontrolü

"Hepsi yeşil" tek başına bilgi değil. Her testin **hangi** hata sınıfını
yakaladığını bir kez kanıtla:

| Mutasyon (`axis_skid_buffer.vhd`) | Kırmızıya dönmesi gereken |
|---|---|
| `m_axis_tdata <= skid_data when skid_valid = '1' else reg_data;` | `her_iki_kayit_doluyken_sira_korunur`, `veri_butunlugu.agir_stall` |
| `s_axis_tready <= '1';` | protokol denetçisi + veri kaybı |
| `s_axis_tready <= not (skid_valid or reg_valid);` | `tam_hiz_zamanlamasi` |

Üçüncüsü özellikle öğretici: bu mutasyon **veri kaybetmez, sırayı bozmaz,
protokolü ihlal etmez** — sadece yavaştır. Yakalayan tek şey zamanlama
testi.

Bir mutasyon hiçbir testi kırmıyorsa, o hata sınıfı için testin yok.

---

## 10. Tuzak listesi

1. `use vunit_lib.stall_pkg.all;` diye bir paket yok.
2. `add_verification_components()` çağrılmazsa `axi_stream_pkg` bulunamaz.
3. VC'ler `areset_n` (aktif-düşük) ister; DUT senkron aktif-yüksek `reset`
   kullanıyorsa `areset_n <= not reset;`.
4. El sıkışma okurken `wait for 1 ns` **koyma** — bir çevrim kayarsın.
5. Testbench yalnızca `in` portlarını sürer; `out` sürmek sessiz `'X'`
   üretir.
6. Master sürücüsü asılı bir beat'in payload'ını değiştiremez.
7. Çıkışta skid'e öncelik veren mux sırayı bozar, hem de sessizce.
8. Sıfır `check` çağıran test geçer.
9. `stall_config` elaborasyon zamanlı — runtime'da değiştirilemez.
10. Yeni `.vhd` eklendikten sonra `python generate_vhdl_ls.py` çalıştır.
11. `add_project_sources` içindeki `load_manifest()` koşulsuz çağrılıyor;
    `vectors/configs.json` yoksa **FIR'le ilgisi olmayan** skid testleri de
    koşmaz. İleride gevşetilecek.

---

## 11. Komut özeti

```powershell
python generate_vectors.py            # manifest yoksa once bu
python generate_vhdl_ls.py            # yeni .vhd eklendiyse
python run.py --list "*axis_skid*"    # veri_butunlugu 3 kez gorunmeli
python run.py "*axis_skid*" -v
python run.py "*veri_butunlugu*agir_stall*" -v --log-level debug
```

---

## 12. Sıradaki adım — AXI4-Lite

Hedef: `fir_filter`'daki statik `config_id` generic'ini **çalışma zamanı**
register'ına taşımak.

### Beş kanal

| Kanal | Yön | Taşıdığı |
|---|---|---|
| **AW** | master → slave | yazma adresi |
| **W** | master → slave | yazma verisi + `wstrb` |
| **B** | slave → master | yazma yanıtı |
| **AR** | master → slave | okuma adresi |
| **R** | slave → master | okuma verisi + yanıt |

Her kanal kendi `valid`/`ready` çiftine sahip ve **bağımsız**. Stream'de
öğrenilen kural her kanalda ayrı ayrı geçerli. Asıl tuzak: **AW ile W
arasında sıra garantisi yoktur.** W, AW'den önce gelebilir.

### Planlanan register haritası

| Ofset | Ad | Erişim | İçerik |
|---|---|---|---|
| `0x00` | `ID` | RO | sabit imza, örn. `0x5C1D_0001` |
| `0x04` | `CTRL` | RW | bit0 `enable` |
| `0x08` | `CONFIG` | RW | `config_id` |
| `0x0C` | `STATUS` | RO | bit0 `busy` |
| `0x10` | `SCRATCH` | RW | serbest, yalnızca testbench için |

`ID` bus'ın hiç çalışmadığını ilk okumada söyler; `SCRATCH` register
bank'ı DUT'un geri kalanına dokunmadan test etmeye yarar.

### Cevaplanacak sorular

1. Slave "önce `awvalid`, sonra `wready`" derse hangi master'la kilitlenir?
2. `bvalid` ne zaman kaldırılmalı — AW kabulünde mi, W kabulünde mi,
   register'a işlendikten sonra mı?
3. Tüm `wstrb` bitleri `'0'` gelirse ne olmalı, yanıt ne olmalı?
4. RO register'a yazma: `OKAY` mı `SLVERR` mı — hangi gerekçeyle?
5. Haritada olmayan adres: `DECERR` yerine `OKAY`+sıfır dönmenin bedeli
   hangi hata sınıfını sessizleştirir?
6. `awvalid` asılıyken master `awaddr`'ı değiştirebilir mi?
7. **Asıl soru:** FIR akış ortasındayken `CONFIG` register'ına yazılırsa
   yeni katsayılar hemen mi devreye girsin, `tlast`'a kadar mı beklesin?
   Delay line'da eski konfigürasyonla işlenmiş örnekler var.

### VUnit tarafı

`axi_stream_pkg` yerine **`bus_master_pkg`** — AXI'ye özel olmayan soyut
bir bus master arayüzü. Protokolü `axi_lite_master` entity'si sağlar.

```vhdl
use vunit_lib.bus_master_pkg.all;
use vunit_lib.axi_pkg.all;                -- axi_resp_t, axi_resp_okay ...

constant regs_bus : bus_master_t := new_bus(data_length => 32,
                                            address_length => 32);
-- write_bus / read_bus / check_bus
```

İki uyarı:

- `axi_lite_master` entity'sinin **reset portu yok**; reset'i DUT'a sen
  verirsin.
- VC, AW ve W'yi **birlikte** sürer. "W, AW'den önce gelir" senaryosu VC
  ile test **edilemez** — elle yazılmış bir teste kalır. Bölüm 8'deki
  işbölümünün aynısı.