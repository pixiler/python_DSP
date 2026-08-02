"""VUnit giris noktasi — pytest'teki `conftest.py`nin karsiligi.

Kullanim:
    python run.py -v            # hepsi, detayli
    python run.py --list        # testleri listele, kosma
    python run.py "*tick*"      # ada gore filtrele
    python run.py --gui         # dalga formu (simulator destekliyorsa)

Detaylar: docs/hafta6_gorev6_vunit.md — Bolum 2.3
"""

from pathlib import Path

from vunit import VUnit

ROOT = Path(__file__).parent
HDL_SRC = ROOT / "hdl" / "src"
HDL_TB = ROOT / "hdl" / "tb"

vu = VUnit.from_argv()
vu.add_vhdl_builtins()

lib = vu.add_library("lib")
for hdl_dir in (HDL_SRC, HDL_TB):
    # Klasor bosken glob eslesmedigi icin VUnit hata veriyor; ilk .vhd
    # dosyasini yazana kadar bu kontrol run.py'yi calisir tutuyor.
    if any(hdl_dir.glob("*.vhd")):
        lib.add_source_files(hdl_dir / "*.vhd")

vu.main()
