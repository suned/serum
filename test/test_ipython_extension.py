import sys
from serum import Context, load_ipython_extension, unload_ipython_extension


class MockIpythonContext:
    context = Context()


def test_load_extension_no_ipython_environment():
    assert load_ipython_extension(None) is None


def test_load_extension():
    sys.modules['ipython_context'] = MockIpythonContext
    load_ipython_extension(None)
    assert MockIpythonContext.context is Context.current_context()
    unload_ipython_extension(None)
    assert MockIpythonContext is not Context.current_context()
    sys.modules['ipython_context'] = None


def test_unload_extension_no_ipython_environment():
    assert unload_ipython_extension(None) is None
