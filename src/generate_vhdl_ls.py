"""VHDL-LS icin `vhdl_ls.toml` uret.

Dosya listesini elle yazmak yerine VUnit'in derleme sirasindan alir; boylece
`vunit_lib` icindeki VHDL-93/2002/2008 varyantlarindan yalnizca dogru olani
listelenir.

Kullanim:
    python generate_vhdl_ls.py

Kaynak dosya ekledikten veya VUnit surumunu degistirdikten sonra tekrar calistir,
ardindan VS Code'da "VHDL LS: Restart" komutunu ver.
"""

from pathlib import Path

from vunit import VUnit

from vunit_project import add_project_sources

ROOT = Path(__file__).parent
OUTPUT = ROOT / "vhdl_ls.toml"
STANDARD = "2008"


def collect_libraries() -> dict[str, list[str]]:
    """Kutuphane adi -> mutlak dosya yollari eslemesini derleme sirasindan cikar."""
    vu = VUnit.from_argv(argv=[], compile_builtins=False)
    add_project_sources(vu)

    libraries: dict[str, list[str]] = {}
    for source_file in vu.get_compile_order():
        path = Path(source_file.name).resolve().as_posix()
        libraries.setdefault(source_file.library.name, []).append(path)
    return libraries


def render_toml(libraries: dict[str, list[str]]) -> str:
    """Kutuphane eslemesini vhdl_ls.toml metnine cevir."""
    lines = [f'standard = "{STANDARD}"', "", "[libraries]"]
    for name, files in libraries.items():
        lines.append(f"{name}.files = [")
        lines += [f"    '{f}'," for f in files]
        lines.append("]")
        if name == "vunit_lib":
            # Kutuphane kodundaki "kullanilmayan tanim" uyarilarini sustur
            lines.append(f"{name}.is_third_party = true")
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    libraries = collect_libraries()
    OUTPUT.write_text(render_toml(libraries), encoding="utf-8")

    toplam = sum(len(files) for files in libraries.values())
    print(f"{OUTPUT.name} yazildi: {len(libraries)} kutuphane, {toplam} dosya")
    for name, files in libraries.items():
        print(f"  {name}: {len(files)}")


if __name__ == "__main__":
    main()
