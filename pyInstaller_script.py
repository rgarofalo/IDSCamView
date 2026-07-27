# fmt: off
import PyInstaller.__main__
import os

from get_import import find_imports_in_directory
from src.utils import resource_path


VERSION = "0.2.1"

find_imports = find_imports_in_directory("src",False)
find_imports.remove("os")
find_imports.remove("sys")
find_imports.remove("queue")
find_imports.remove("time")
find_imports.remove("screeninfo.get_monitors")
find_imports.remove("typing.Optional")
find_imports.remove("threading")






hidden_imports = []
for imp in find_imports:
    hidden_imports.extend(["--hidden-import", imp])


paths_source = resource_path("output/src")
data_source = resource_path("img")
distpath = resource_path("dist/"+VERSION)
paths_source_venv = resource_path(".venv/Lib/site-packages")


for path in [paths_source, data_source, paths_source_venv]:
    if not os.path.exists(path):
        # print(f"Error: Path {path} does not exist.")
        raise Exception("Path {path} does not exist.")

PyInstaller.__main__.run(
    [
        "run.py",
        "--paths", paths_source_venv,
        "--add-data", resource_path("img") + os.pathsep + "img",
        "--add-binary", paths_source + os.pathsep + "output/src",
        "--distpath", distpath,
        "--name", "IDSCamView",
        "--windowed",
        "--noconsole",
        "--onefile",
    ]
    + hidden_imports
)
