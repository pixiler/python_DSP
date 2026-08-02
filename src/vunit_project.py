"""Projenin VUnit kaynak tanimi — tek gercegin kaynagi.

Hem `run.py` hem `generate_vhdl_ls.py` bu fonksiyonu kullanir, boylece
dosya listesi tek yerde durur. (pytest'teki `conftest.py` mantigi.)
"""

from pathlib import Path

ROOT = Path(__file__).parent


def add_project_sources(vu):
    """Proje kutuphanelerini ve kaynak dosyalarini VUnit nesnesine ekle.

    Args:
        vu: `VUnit.from_argv(...)` ile olusturulmus VUnit nesnesi.

    Returns:
        Olusturulan `lib` kutuphanesi.
    """
    vu.add_vhdl_builtins()

    lib = vu.add_library("lib")
    lib.add_source_files(ROOT / "hdl" / "src" / "*.vhd")
    lib.add_source_files(ROOT / "hdl" / "tb" / "*.vhd")
    return lib
