from ._dependency import *
from ._context import *
from ._functions import *
from ._inject import *


def load_ipython_extension(_):
    try:
        from ipython_context import context  # type: ignore
        context.__enter__()
    except ModuleNotFoundError:
        pass


def unload_ipython_extension(_):
    try:
        from ipython_context import context  # type: ignore
        context.__exit__(None, None, None)
    except ModuleNotFoundError:
        pass
