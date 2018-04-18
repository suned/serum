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
    """
    Exception type to signal attempt to run app in unknown environment
    using match function
    """
    pass


class NoNamedDependency(Exception):
    """
    Exception type to signal attempt to inject named dependency not provided
    in the current environment
    """
    pass


class InjectionError(Exception):
    """
    Exception type to signal failure to instantiate a dependency decorated
     type
    """
    pass
