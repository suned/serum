from abc import abstractmethod, abstractstaticmethod, abstractclassmethod

from ._dependency import *
from ._environment import *
from ._functions import *
from ._inject import *
from ._named_dependency import *


def load_ipython_extension(_):
    try:
        from ipython_environment import environment  # type: ignore
        environment.__enter__()
    except ModuleNotFoundError:
        pass


def unload_ipython_extension(_):
    try:
        from ipython_environment import environment  #type: ignore
        environment.__exit__(None, None, None)
    except ModuleNotFoundError:
        pass
