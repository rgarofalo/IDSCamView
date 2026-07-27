import sys
import os


def is_pyinstaller():
    """Check if the script is running from PyInstaller"""
    return getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS")


if is_pyinstaller():
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "./output/src"))
    )
else:
    sys.path.insert(
        0, os.path.abspath(os.path.join(os.path.dirname(__file__), "./src"))
    )

from ids_camview import idsCamView
import argparse


def runMain():
    parser = argparse.ArgumentParser(description="")
    parser.add_argument(
        "--configPath",
        type=str,
        required=False,
        default="config.cfg",
        help="The path to the configuration file. Default is 'config.cfg'.",
    )
    parser.add_argument(
        "--typeView",
        type=str,
        required=False,
        default="Default",
        help="The type of view to use. Default is 'Default'.",
    )

    args = parser.parse_args()

    known_args, unknown_args = parser.parse_known_args()

    # Controlla se ci sono argomenti non previsti
    if unknown_args:
        raise ValueError(f"Unexpected arguments: {unknown_args}")

    idsCamView(args)


if __name__ == "__main__":
    try:
        runMain()
    except ValueError as e:
        print(e)
        sys.exit(1)
