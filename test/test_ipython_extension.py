import unittest
import sys
from serum import Context, load_ipython_extension, unload_ipython_extension


class MockIpythonContext:
    context = Context()


class IPythonExtensionTests(unittest.TestCase):

    def test_load_extension_no_ipython_environment(self):
        self.assertEqual(load_ipython_extension(None), None)

    def test_load_extension(self):
        sys.modules['ipython_context'] = MockIpythonContext
        load_ipython_extension(None)
        self.assertIs(
            MockIpythonContext.context,
            Context.current_context()
        )
        unload_ipython_extension(None)
        self.assertIsNot(
            MockIpythonContext,
            Context.current_context()
        )
        sys.modules['ipython_context'] = None

    def test_unload_extension_no_ipython_environment(self):
        self.assertEqual(unload_ipython_extension(None), None)
