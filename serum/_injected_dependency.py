class Dependency:
    def __init__(self, name):
        self.__name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        return getattr(instance, self.__name)

    def __set__(self, instance, value):
        raise AttributeError('Can\'t set injected dependency')
