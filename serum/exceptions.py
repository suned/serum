class NoEnvironment(Exception):
    """
    Exception type to signal attempts to call functions that require
    an environment outside an environment
    """
    pass


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


class InvalidComponent(Exception):
    """
    Exception type to signal bad declaration of a Component subtype
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
