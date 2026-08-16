from vunit import VUnit
from pathlib import Path

ROOT = Path(__file__).parent

vu = VUnit.from_argv(compile_builtins=False)
vu.add_vhdl_builtins()

lib = vu.add_library("lib")
lib.add_source_files(ROOT / "hdl" / "src" / "*.vhd")
lib.add_source_files(ROOT / "hdl" / "tb" / "*.vhd")

vu.main()