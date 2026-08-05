from pathlib import Path
import json
import numpy as np
from dsp import suppression_db

ROOT = Path(__file__).parent
VECTORS = ROOT / "vectors"

def read_vector(path: Path) -> np.ndarray:
    """Tek satirlik (save_csv) veya satir basina bir degerlik CSV'yi oku."""
    return np.loadtxt(path, dtype=np.int64, delimiter=",").ravel()

def add_project_sources(vu):
    vu.add_vhdl_builtins()
    lib = vu.add_library("lib")
    lib.add_source_files(ROOT / "hdl" / "src" / "*.vhd")
    lib.add_source_files(ROOT / "hdl" / "tb" / "*.vhd")

    tb = lib.test_bench("tb_fir_filter")
    tb.set_generic("input_csv",       (VECTORS / "input.csv").as_posix())
    tb.set_generic("expected_csv",    (VECTORS / "expected.csv").as_posix())
    tb.set_generic("input_dc_csv",    (VECTORS / "input_dc.csv").as_posix())
    tb.set_generic("expected_dc_csv", (VECTORS / "expected_dc.csv").as_posix())
    tb.test("cikis_ile_beklenen_ayni").set_post_check(check_spectrum)
    return lib

def check_spectrum(output_path):
    meta = json.loads((VECTORS / "meta.json").read_text())
    y = read_vector(Path(output_path) / "output.csv")
    x = read_vector(VECTORS / "input.csv")
    
    y_seg = y[meta["skip_samples"]:][:meta["analysis_len"]]
    x_seg = x[meta["skip_samples"]:][:meta["analysis_len"]]

    assert len(y_seg) == meta["analysis_len"], (
        f"cikis kisa: {len(y_seg)} ornek, {meta['analysis_len']} bekleniyordu"
    )
    assert len(x_seg) == meta["analysis_len"], (
        f"giris kisa: {len(x_seg)} ornek, {meta['analysis_len']} bekleniyordu"
    )

    olculen_passband_db  = suppression_db(y = y_seg, x= x_seg, fs= meta["fs"], tone_hz=meta["pass_tone_hz"])
    olculen_stopband_db = suppression_db(y = y_seg, x= x_seg, fs= meta["fs"], tone_hz=meta["stop_tone_hz"])


    # 1) donanim float referansla ayni mi?  (dar tolerans, 0.2 dB)

    assert abs(olculen_passband_db - meta["expected_passband_db"]) <= 0.2, (
        f"passband float referanstan sapti: olculen {olculen_passband_db:.3f} dB, "
        f"beklenen {meta['expected_passband_db']:.3f} dB"
    )

    assert abs(olculen_stopband_db - meta["expected_stopband_db"]) <= 0.2, (
        f"stopband float referanstan sapti: olculen {olculen_stopband_db:.3f} dB, "
        f"beklenen {meta['expected_stopband_db']:.3f} dB"
    )
    # 2) bastirma mutlak olarak yeterli mi? (> 40 dB, gorev sarti)
    
    assert olculen_stopband_db <= -40, (
        f"Stopband bastırma şartı saglanamadi! "
        f"Hedef: en az -40 dB (veya altı), Ölçülen: {olculen_stopband_db:.2f} dB. "
        f"Filtre bastırması yetersiz kalıyor."
    )

    assert olculen_passband_db >= -1, (
        f"Passband dalgalanma/kayıp şartı saglanamadi "
        f"Hedef: -1 dB veya üstü (daha az zayıflama), Ölçülen: {olculen_passband_db:.2f} dB. "
        f"Geçiş bandı kaybı çok yüksek."
    )

    return True