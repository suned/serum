class AmbiguousDependencies(Exception):
    """
    Exception type to signal registering conflicting types in an environment
    """
    pass


class CircularDependency(Exception):
    """
    Exception type to signal attempt to inject dependency with circular
    dependencies
    """
    pass


class UnknownEnvironment(Exception):
    pass


class NoNamedDependency(Exception):
    pass


class InjectionError(Exception):
    pass
