class InvalidDependency(Exception):
    """
    Exception type to signal attempts to inject/register types that do
    not inherit from Component
    """
    pass


class UnregisteredDependency(Exception):
    """
    Exception type to signal failure to find an appropriate concrete type
    in an environment
    """
    pass


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
