# Build Status

[![CircleCI](https://circleci.com/gh/suned/serum.svg?style=svg)](https://circleci.com/gh/suned/serum) [![codecov](https://codecov.io/gh/suned/serum/branch/master/graph/badge.svg)](https://codecov.io/gh/suned/serum)



# Description
`serum` is a fresh take on Dependency Injection in Python 3.

`serum` is pure python and has no dependencies.
# Installation
```
> pip install serum
```
# Quickstart
```python
from serum import inject, Dependency, Environment, abstractmethod


# Dependency subclasses are injectable types. They can be abstract... 
class AbstractLog(Dependency):
    @abstractmethod
    def info(self, message: str):
        pass


# ...And concrete
class SimpleLog(AbstractLog):
    def info(self, message: str):
        print(message)


class StubLog(SimpleLog):
    def info(self, message: str):
        pass


@inject  # Dependencies are injected using a class decorator...
class NeedsLog:
    log: AbstractLog  # ...and class level annotations...


class NeedsSimpleLog:
    @inject  # ...or using function argument annotations and a function decorator
    def __init__(self, log: SimpleLog):
        self.log = log 


# Environments provide dependencies
with Environment(SimpleLog):
    assert isinstance(NeedsLog().log, SimpleLog)

with Environment():
    # Abstract dependencies can only be injected in environments
    # that provide concrete implementations.
    NeedsLog().log.info('Hello serum!')  # raises: UnregisteredDependency
    # Concrete dependencies can be injected even in an
    # empty environment
    NeedsSimpleLog().log.info('Hello serum!') # outputs: Hello serum!


# The default Environment is empty
assert isinstance(NeedsSimpleLog().log, SimpleLog)


# Environments will always provide the most specific 
# subtype of the requested type. This allows you to change which concrete
# dependencies are injected.
with Environment(SimpleLog, StubLog):
    NeedsLog().log.info('Hello serum!')  # doesn't output anything
    NeedsSimpleLog().log.info('Hello serum!')  # doesn't output anything
```
# Documentation
- [`Dependency`](#dependency)
- [`Environment`](#environment)
- [`inject`](#inject)
- [`Singleton`](#singleton)
- [`immutable`](#immutable)
- [`mock`](#mock)
- [`match`](#match)
- [PEP 484](#pep-484)
- [IPython Integration](#ipython-integration)

## `Dependency`
All subclasses of `Dependency` can be injected.
```python
from serum import Dependency, Environment, inject


class Log(Dependency):
    def info(self, message):
        print(message)

@inject
class NeedsLog:
    log: Log



assert isinstance(NeedsLog().log, Log)
```
`serum` relies on being able to inject all dependencies for a `Dependency`
subclass recursively. To achieve this, the `__init__` method of `Dependency` subclasses
is limited such that: 
- If `__init__` takes more than the `self` parameter, it must be
decorated with `inject`.
- All parameters to `__init__` except `self` must be annotated
with other `Dependency` subclasses or `inject.name` (see [`inject`](#inject)).
```python
@inject
class ValidDependency(Dependency):  # OK!
    some_dependency: SomeDependency

    def __init__(self):
        self.value = self.some_dependency.method()

class AlsoValidDependency(Dependency):  # Also OK!
    @inject
    def __init__(self, some_dependency: SomeDependency):
        pass


class InvalidDependency(Dependency):  # raises: InvalidDependency: __init__ method of Dependency subclasses that takes parameters must be decorated with inject
    def __init__(self, a):
        pass

class AlsoInvalidDependency(Dependency):  # raises: InvalidDependency: __init__ method of Dependency subclasses that takes parameters must have all parameters except "self" annotated with Dependency types or Key
    @inject
    def __init__(self, a):
        pass
```

Note that circular dependencies preventing `Dependency` instantiation leads to
an error.
```python
class AbstractA(Dependency):
    pass


class AbstractB(Dependency):
    pass


class A(AbstractA):

    @inject
    def __init__(self, b: AbstractB):
        self.b = b

class B(AbstractB):
    @inject
    def __init__(self, a: AbstractA):
        self.a = a

@inject
class Dependent:
    a: AbstractA


with Environment(A, B):
    Dependent()  # raises: CircularDependency: Circular dependency encountered while injecting <class 'AbstractA'> in <B object at 0x1061e3898>
```
`Dependency` subclasses can be abstract. Abstract dependencies can only be injected in an
`Environment` that provides a concrete implementation. For convenience you can import
`abstractmethod`, `abstractclassmethod` or `abstractclassmethod` from `serum`,
but they simply refer to the decorators from the `abc` module 
in the standard library.
```python
from serum import abstractmethod


class AbstractLog(Dependency):
    @abstractmethod
    def info(self, message):
        pass
        
@inject
class NeedsLog:
    log: AbstractLog


NeedsLog()  # raises UnregisteredDependency: No concrete implementation of <class 'AbstractLog'> found


class ConcreteLog(AbstractLog):
    def info(self, message):
        print(message)


with Environment(ConcreteLog):
    NeedsLog()  # Ok!
```
## `Environment`
`Environment`s provide implementations of dependencies. An `Environment` will always provide the most
specific subtype of the requested type (in Method Resolution Order).
```python
class Super(Dependency):
    pass


class Sub(Super):
    pass

@inject
class NeedsSuper:
    instance: Super


with Environment(Sub):
    assert isinstance(NeedsSuper().instance, Sub)
```
It is an error to inject a type in an `Environment` that provides two or more equally specific subtypes of that type:
```python
class AlsoSub(Super):
    pass


with Environment(Sub, AlsoSub):
    NeedsSuper() # raises: AmbiguousDependencies: Attempt to inject type <class 'Log'> with equally specific provided subtypes: <class 'MockLog'>, <class 'FileLog'>
```
`Environment`s can also be used as decorators:
```python
environment = Environment(Sub)

@environment
def f():
    assert isinstance(NeedsSuper().instance, Sub)

``` 
You can provide named dependencies of any type using keyword arguments using [`inject.name()`](#inject).
```python
@inject
class Database(Dependency):
    connection_string: inject.name()
    

connection_string = 'mysql+pymysql://root:my_pass@127.0.0.1:3333/my_db'
environment = Environment(
    connection_string=connection_string
)
with environment:
    assert Database().connection_string == connection_string
```
`Environment`s are local to each thread. This means that when using multi-threading
each thread must define its own environment.
```python
import threading

def worker_without_environment():
    NeedsSuper().instance  # raises NoEnvironment: Can't inject components outside an environment

def worker_with_environment():
    with Environment(Sub):
        NeedsSuper().instance  # OK!

with Environment():
    threading.Thread(target=worker_without_environment()).start()
    threading.Thread(target=worker_with_environment()).start()
```
## `inject`
`inject` is used to decorate functions and classes in which you want to inject
dependencies.
```python
class MyDependency(Dependency):
    pass

@inject
def f(dependency: MyDependency):
    assert isinstance(dependency, MyDependency)

with Environment():
    f()
```
If you want to inject a named dependency given as a keyword argument to `Environment`,
you can annotate an argument using `inject.name`.
```python
@inject
def f(dependency: inject.name(of_type=str)):
    assert dependency == 'a named dependency'

with Environment(dependency='a named dependency'):
    f()
```
The optional `of_type` argument is used to enable PEP484 type-hinting for tools
that support it. `serum` does not prevent you from injecting a named dependency
of another type, but will issue a warning if you do so.

`inject` can also be used to decorate classes. 
```python
@inject
class SomeClass:
    dependency: MyDependency 
```
This is roughly equivalent to:
```python
class SomeClass:
    @inject
    def __init__(self, dependency: MyDependency):
        self.__dependency = dependency
    
    @property
    def dependency(self) -> MyDependency:
        return self.__dependency
```
## `Singleton`
To always inject the same instance of a dependency in the same `Environment`, inherit from `Singleton`.
```python
from serum import Singleton


class ExpensiveObject(Singleton):
    pass


@inject
class NeedsExpensiveObject:
    expensive_instance: ExpensiveObject


instance1 = NeedsExpensiveObject()
instance2 = NeedsExpensiveObject()
assert instance1.expensive_instance is instance2.expensive_instance
```
Note that `Singleton` dependencies injected in different environments 
will not refer to the same instance.
```python

with Environment():
    instance1 = NeedsExpensiveObject()

with Environment():
    assert instance1.expensive_instance is not NeedsExpensiveObject().expensive_instance
```
## `immutable`
If you want to define immutable members (constants), 
`serum` provides the `immutable` utility
that also supports type inference with PEP 484 tools. 
```python
from serum import immutable


class Immutable:
    value = immutable(1)


i = Immutable()
i.value = 2  # raises AttributeError: Can't set property
```
## `mock`
`serum` has support for injecting `MagicMock`s from the builtin
`unittest.mock` library in unittests using the `mock` utility
function. `mock` is only usable inside an an environment context. Mocks are reset
when the environment context is closed.
```python
from serum import mock


class SomeDependency(Dependency):
    def method(self):
        return 'some value' 

@inject
class Dependent:
    dependency: SomeDependency


environment = Environment()
with environment:
    mock_dependency = mock(SomeDependency)
    mock_dependency.method.return_value = 'some mocked value'
    instance = Dependent()
    assert instance.dependency is mock_dependency
    assert instance.dependency.method() == 'some mocked value'

with environment:
    instance = Dependent()
    assert instance.dependency is not mock_dependency
    assert isinstance(instance.dependency, SomeDependency)

mock(SomeDependency)  # raises: NoEnvironment: Can't register mock outside environment
```
`mock` uses its argument to spec the injected instance of `MagicMock`. This means
that attempting to call methods that are not defined by the mocked `Component`
leads to an error
```python
with environment:
    mock_dependency = mock(SomeDependency)
    mock_dependency.no_method()  # raises: AttributeError: Mock object has no attribute 'no method'
```
Note that `mock` will only mock requests of the
exact type supplied as its argument, but not requests of
more or less specific types
```python
from unittest.mock import MagicMock


class Super(Dependency):
    pass


class Sub(Super):
    pass


class SubSub(Sub):
    pass


@inject
class NeedsSuper:
    injected: Super


@inject
class NeedsSub:
    injected: Sub


@inject
class NeedsSubSub:
    injected: SubSub


with Environment():
    mock(Sub)
    needs_super = NeedsSuper()
    needs_sub = NeedsSub()
    needs_subsub = NeedsSubSub()
    assert isinstance(needs_super.injected, Super)
    assert isinstance(needs_sub.injected, MagicMock)
    assert isinstance(needs_subsub.injected, SubSub)
```
## `match`
`match` is small utility function for matching `Environment` instances
with values of an environment variable.
```python
# my_script.py
from serum import match, Dependency, abstractmethod, Environment, inject


class BaseDependency(Dependency):
    @abstractmethod
    def method(self):
        pass


class ProductionDependency(BaseDependency):
    def method(self):
        print('Production!')


class TestDependency(BaseDependency):
    def method(self):
        print('Test!')


@inject
def f(dependency: BaseDependency):
    dependency.method()


environment = match(
    environment_variable='MY_SCRIPT_ENV', 
    default=Environment(ProductionDependency),
    PROD=Environment(ProductionDependency),
    TEST=Environment(TestDependency)
)

with environment:
    f()
```
```
> python my_script.py
Production!
```
```
> MY_SCRIPT_ENV=PROD python my_script.py
Production!
```
```
> MY_SCRIPT_ENV=TEST python my_script.py
Test!
```
## PEP 484
`serum` is designed for type inference with PEP 484 tools (work in progress). 
This feature is currently only supported for the PyCharm type checker.

![type inference in PyCharm](https://i.imgur.com/8fvvAQ2.png)
## IPython Integration
It can be slightly annoying to import some `Environment` and start it as a
context manager in the beginning of every IPython session. 
Moreover, you quite often want to run an IPython REPL in a special environment,
e.g to provide configuration that is normally supplied through command line
arguments in some other way.

To this end `serum` can act as an IPython extension. To activate it,
add the following lines to your `ipython_config.py`:
```python
c.InteractiveShellApp.extensions = ['serum']
```
Finally, create a file named `ipython_environment.py` in the root of your project. In it,
assign the `Environment` instance you would like automatically started to a global
variable named `environment`:
```python
# ipython_environment.py
from serum import Environment


environment = Environment()
```
IPython will now enter this environment automatically in the beginning of
every REPL session started in the root of your project.
# Why?
If you've been researching Dependency Injection frameworks for python,
you've no doubt come across this opinion:

>You dont need Dependency Injection in python. 
>You can just use duck typing and monkey patching!
 
The position behind this statement is often that you only need Dependency 
Injection in statically typed languages.

In truth, you don't really _need_ Dependency Injection in any language, 
statically typed or otherwise. 
When building large applications that need to run in multiple environments however,
Dependency Injection can make your life a lot easier. In my experience,
excessive use of monkey patching for managing environments leads to a jumbled
mess of implicit initialisation steps and `if value is None` type code.

In addition to being a framework, I've attempted to design `serum` to encourage
designing classes that follow the Dependency Inversion Principle:

> one should “depend upon abstractions, _not_ concretions."

This is achieved by letting inheritance being the principle way of providing
dependencies and allowing dependencies to be abstract. See the `example.py` for a
detailed tutorial (work in progress).