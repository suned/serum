from ._context import Context
from ._dependency import dependency, singleton
from ._functions import mock, match
from ._inject import inject

__all__ = [
    'Context', 'dependency', 'singleton', 'inject', 'mock', 'match',
    'load_ipython_extension', 'unload_ipython_extension',
]


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
