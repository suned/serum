from serum import *


__dependency__ = True


def dependency(cls):
    cls.__is_dependency__ = True
    return cls


@dependency
class ArchiiConfig:
    pass


class ProductionConfig(ArchiiConfig):
    pass



class NeedsConfig:
    config: ArchiiConfig


from envs import production_env
with production_env:
    NeedsConfig()


@inject
def f(connection_string: D, a: int):
    a = connection_string


class Needs:
    a: int

    def __init__(self, a):
        self.a = a

