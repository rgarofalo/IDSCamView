import os


from distutils.core import setup
from Cython.Build import cythonize
from distutils.extension import Extension


# Definire la directory di output per le build
build_dir = "build"
output_dir = "output"
output_dir_c = "build_output_c"

os.makedirs(output_dir_c, exist_ok=True)
os.makedirs(output_dir, exist_ok=True)
os.makedirs(build_dir, exist_ok=True)


extensions = [Extension("*", ["src/*.py"])]

cythonize_opts = {"build_dir": output_dir_c}

setup(
    ext_modules=cythonize(extensions, **cythonize_opts),
    script_args=[
        "build_ext",
        "--build-lib",
        output_dir,
        "--build-temp",
        build_dir,
    ],
)
