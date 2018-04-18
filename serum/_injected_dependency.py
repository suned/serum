class Dependency:
    """
    Dependency descriptor for dependencies specified as class
    level annotations
    """
    def __init__(self, name):
        self.__name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        dependency_instance = getattr(instance, self.__name)
        if isinstance(dependency_instance, Exception):
            raise dependency_instance
        return dependency_instance

    def __set__(self, instance, value):
        raise AttributeError('Can\'t set injected dependency')
