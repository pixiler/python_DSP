from vunit import VUnit
from vunit_project import add_project_sources

vu = VUnit.from_argv(compile_builtins=False)
add_project_sources(vu)
vu.main()