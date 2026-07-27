# Lambda-izer for making it easy to pass arguments with function calls
# without having to know what lambda does
from screeninfo import get_monitors
import sys
import os


def with_args(func_name, *args):
    return lambda: func_name(*args)


def set_callback(obj, attribute_name, fun, args=None):
    if fun is None:
        setattr(obj, attribute_name, lambda: None)
    else:
        if args is None:
            setattr(obj, attribute_name, fun)
        else:
            setattr(obj, attribute_name, lambda: fun(*args))


def get_monitor(display=1):
    monitors = get_monitors()
    if display > 1 and display <= len(monitors):
        return monitors[display - 1]
    return monitors[0]


def resource_path(relative_path):
    """
    The `resource_path` function returns the absolute path to a resource,
    taking into account whether  the script is running in development
    mode or as a PyInstaller executable.

    :param relative_path:  string that  represents the path to a resource
     file relative to the current working directory or the executable file's directory.
    :return: the absolute path to a resource.

    """
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    return os.path.join(os.path.abspath("."), relative_path)
