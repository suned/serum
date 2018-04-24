import os

from serum import Context, match
from serum.exceptions import UnknownEnvironment
import pytest


@pytest.fixture()
def environ():
    yield os.environ
    os.environ.pop('TEST_ENV', None)


def test_match_returns_correct_env(environ):
    env1 = Context()
    env2 = Context()
    environ['TEST_ENV'] = 'ENV1'
    env = match(environment_variable='TEST_ENV', ENV1=env1, ENV2=env2)
    assert env is env1
    environ['TEST_ENV'] = 'ENV2'
    env = match(environment_variable='TEST_ENV', ENV1=env1, ENV2=env2)
    assert env is env2


def test_match_gets_default():
    default = Context()
    env1 = Context()
    env = match(environment_variable='TEST_ENV', default=default, ENV1=env1)
    assert env is default


def test_match_fails_when_no_default_and_no_env():
    env1 = Context()
    with pytest.raises(UnknownEnvironment):
        match(environment_variable='TEST_ENV', env1=env1)


def test_match_fails_with_unknown_environment(environ):
    environ['TEST_ENV'] = 'unknown'
    with pytest.raises(UnknownEnvironment):
        match(environment_variable='TEST_ENV')
