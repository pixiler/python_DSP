from pathlib import Path
ROOT = Path(__file__).parent
VECTORS = ROOT / "vectors"

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
    return lib