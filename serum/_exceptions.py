class NoEnvironment(Exception):
    pass


class InvalidDependency(Exception):
    pass


class UnregisteredDependency(Exception):
    pass


class InvalidComponent(Exception):
    pass


class AmbiguousDependencies(Exception):
    pass