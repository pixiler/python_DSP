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