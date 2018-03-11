from serum._environment import provide


class LazyDependency:
    def __init__(self, dependency):
        self.__dependency = dependency

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return provide(self.__dependency, instance)

    def __set__(self, instance, value):
        raise AttributeError('Can\'t set injected attribute')
