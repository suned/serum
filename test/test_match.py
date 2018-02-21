import unittest
import os

from serum import Environment, match
from serum.exceptions import UnknownEnvironment


class MatchTests(unittest.TestCase):
    def tearDown(self):
        if 'TEST_ENV' in os.environ:
            del os.environ['TEST_ENV']

    def test_match_returns_correct_env(self):
        env1 = Environment()
        env2 = Environment()
        os.environ['TEST_ENV'] = 'ENV1'
        env = match(environment_variable='TEST_ENV', ENV1=env1, ENV2=env2)
        self.assertIs(env, env1)
        os.environ['TEST_ENV'] = 'ENV2'
        env = match(environment_variable='TEST_ENV', ENV1=env1, ENV2=env2)
        self.assertIs(env, env2)

    def test_match_gets_default(self):
        default = Environment()
        env1 = Environment()
        env = match(environment_variable='TEST_ENV', default=default, ENV1=env1)
        self.assertEqual(env, default)

    def test_match_fails_when_no_default_and_no_env(self):
        env1 = Environment()
        with self.assertRaises(UnknownEnvironment):
            match(environment_variable='TEST_ENV', env1=env1)

    def test_match_fails_with_unknown_environment(self):
        os.environ['TEST_ENV'] = 'unknown'
        with self.assertRaises(UnknownEnvironment):
            match(environment_variable='TEST_ENV')
