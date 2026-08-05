"""VUnit proje tanimi — kaynak listesi, generic'ler ve konfigurasyonlar.

`generate_vectors.py`'nin urettigi `vectors/configs.json` manifest'i okunur ve
her konfigurasyon icin `add_config` cagrilir. Bu, pytest'teki
`@pytest.mark.parametrize`'in VUnit karsiligi: ayni testbench, farkli
generic'lerle birden cok kez kosar.

Konfigurasyon eklemek icin bu dosya degistirilmez; `generate_vectors.py`
icindeki `CONFIG_ORDERS` listesine bir deger eklemek yeterlidir.
"""

import json
from pathlib import Path

import numpy as np

from dsp import suppression_db

ROOT = Path(__file__).parent
VECTORS = ROOT / "vectors"
MANIFEST = VECTORS / "configs.json"


def read_vector(path: Path) -> np.ndarray:
    """Tek satirlik (save_csv) veya satir basina bir degerlik CSV'yi oku."""
    return np.loadtxt(path, dtype=np.int64, delimiter=",").ravel()


def load_manifest() -> dict:
    """Uretilen konfigurasyon manifest'ini oku.

    Raises:
        FileNotFoundError: Vektorler henuz uretilmemisse, ne yapilmasi
            gerektigini soyleyen bir mesajla.
    """
    if not MANIFEST.exists():
        raise FileNotFoundError(
            f"{MANIFEST} yok. Once 'python generate_vectors.py' calistirin."
        )
    return json.loads(MANIFEST.read_text(encoding="utf-8"))


def make_spectrum_check(manifest: dict, cfg: dict):
    """Bir konfigurasyona bagli `post_check` fonksiyonu uret.

    Kapanis (closure) kullanilmasinin sebebi: VUnit `post_check`'e yalnizca
    `output_path` ve `output` isimli argumanlari gecirir. Konfigurasyona ozel
    beklentiler bu yuzden fonksiyonun icine kapatilir.
    """
    skip = manifest["skip_samples"]
    n = manifest["analysis_len"]
    fs = manifest["fs"]
    tol = manifest["reference_tol_db"]

    def check_spectrum(output_path):
        y = read_vector(Path(output_path) / "output.csv")
        x = read_vector(VECTORS / manifest["input_csv"])

        y_seg, x_seg = y[skip:][:n], x[skip:][:n]
        assert len(y_seg) == n, (
            f"[{cfg['name']}] cikis kisa: {len(y_seg)} ornek, {n} bekleniyordu"
        )
        assert len(x_seg) == n, (
            f"[{cfg['name']}] giris kisa: {len(x_seg)} ornek, {n} bekleniyordu"
        )

        passband_db = suppression_db(y_seg, x_seg, fs, manifest["pass_tone_hz"])
        stopband_db = suppression_db(y_seg, x_seg, fs, manifest["stop_tone_hz"])

        # 1) Donanim, float referansla ayni sonucu mu veriyor?
        #    (dar tolerans: olculen sapma tipik olarak ~0,01 dB)
        assert abs(passband_db - cfg["expected_passband_db"]) <= tol, (
            f"[{cfg['name']}] passband referanstan sapti: olculen "
            f"{passband_db:.3f} dB, beklenen {cfg['expected_passband_db']:.3f} dB"
        )
        assert abs(stopband_db - cfg["expected_stopband_db"]) <= tol, (
            f"[{cfg['name']}] stopband referanstan sapti: olculen "
            f"{stopband_db:.3f} dB, beklenen {cfg['expected_stopband_db']:.3f} dB"
        )

        # 2) Yaptigi sey sartnameyi sagliyor mu?
        #    Bu iddia referanstan bagimsizdir: Python yanlis bir filtre
        #    tasarlasaydi (1) gecerdi, bunu ancak (2) yakalar.
        assert stopband_db <= manifest["min_stopband_db"], (
            f"[{cfg['name']}] stopband yetersiz: olculen {stopband_db:.2f} dB, "
            f"en fazla {manifest['min_stopband_db']:.1f} dB olmali"
        )
        assert passband_db >= manifest["max_passband_loss_db"], (
            f"[{cfg['name']}] passband kaybi fazla: olculen {passband_db:.2f} dB, "
            f"en az {manifest['max_passband_loss_db']:.1f} dB olmali"
        )

        return True

    return check_spectrum


def add_project_sources(vu):
    """Kutuphaneleri, kaynaklari, generic'leri ve konfigurasyonlari ekle."""
    vu.add_vhdl_builtins()

    lib = vu.add_library("lib")
    lib.add_source_files(ROOT / "hdl" / "src" / "*.vhd")
    lib.add_source_files(ROOT / "hdl" / "tb" / "*.vhd")

    manifest = load_manifest()
    tb = lib.test_bench("tb_fir_filter")

    # Testbench geneli varsayilanlar: konfigurasyon eklenmeyen testler
    # (valid_dusukken..., tam_olcek_dc...) bunlari kullanir.
    default_cfg = manifest["configs"][manifest["default_config_id"]]
    tb.set_generic("config_id", manifest["default_config_id"])
    tb.set_generic("input_csv", (VECTORS / manifest["input_csv"]).as_posix())
    tb.set_generic("expected_csv", (VECTORS / default_cfg["expected_csv"]).as_posix())
    tb.set_generic("input_dc_csv", (VECTORS / manifest["input_dc_csv"]).as_posix())
    tb.set_generic("expected_dc_csv", (VECTORS / manifest["expected_dc_csv"]).as_posix())

    # Ana veri yolu testi her konfigurasyonda kosar.
    veri_yolu_testi = tb.test("cikis_ile_beklenen_ayni")
    for cfg in manifest["configs"]:
        veri_yolu_testi.add_config(
            name=cfg["name"],
            generics={
                "config_id": cfg["id"],
                "expected_csv": (VECTORS / cfg["expected_csv"]).as_posix(),
            },
            post_check=make_spectrum_check(manifest, cfg),
        )

    return lib
