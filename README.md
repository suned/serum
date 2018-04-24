# Build Status

Build status: 

[![CircleCI](https://circleci.com/gh/suned/serum.svg?style=svg)](https://circleci.com/gh/suned/serum)

Code quality:

[![Test Coverage](https://api.codeclimate.com/v1/badges/523bc990f4ef696aa22d/test_coverage)](https://codeclimate.com/github/suned/serum/test_coverage) 

[![Maintainability](https://api.codeclimate.com/v1/badges/523bc990f4ef696aa22d/maintainability)](https://codeclimate.com/github/suned/serum/maintainability)




# Description
`serum` is a fresh take on Dependency Injection in Python 3.

`serum` is pure python and has no dependencies.
# Installation
```
> pip install serum
```
# Quickstart
```python
from serum import inject, dependency, Context


# Classes decorated with 'dependency' are injectable types.
@dependency 
class Log:
    def info(self, message: str):
        raise NotImplementedError()


class SimpleLog(Log):
    def info(self, message: str):
        print(message)


class StubLog(SimpleLog):
    def info(self, message: str):
        pass


@inject  # Dependencies are injected using a class decorator...
class NeedsLog:
    log: Log  # ...and class level annotations...


class NeedsSimpleLog:
    @inject  # ...or using a function decorator
    def __init__(self, log: SimpleLog):
        self.log = log 


@inject
class NeedsNamedDependency:
    named_dependency: str  # class level annotations annotated with a type that is not
                           # decorated with 'dependency' will be treated as a named
                           # dependency
                           

# Contexts provide dependencies
with Context(SimpleLog, named_dependency='this name is injected!'):
    assert isinstance(NeedsLog().log, SimpleLog)
    assert NeedsNamedDependency().named_dependency == 'this name is injected!'
    

# Contexts will always provide the most specific 
# subtype of the requested type. This allows you to change which
# dependencies are injected.
with Context(StubLog):
    NeedsLog().log.info('Hello serum!')  # doesn't output anything
    NeedsSimpleLog().log.info('Hello serum!')  # doesn't output anything
```
# Documentation
- [`inject`](#inject)
- [`dependency`](#dependency)
- [`Context`](#context)
- [`singleton`](#singleton)
- [`mock`](#mock)
- [`match`](#match)
- [IPython Integration](#ipython-integration)

## `inject`
`inject` is used to decorate functions and classes in which you want to inject
dependencies.
```python
from serum import inject, dependency

@dependency
class MyDependency:
    pass

@inject
def f(dependency: MyDependency):
    assert isinstance(dependency, MyDependency)

f()
```
Functions decorated with `inject` can be called as normal functions. `serum` will
not attempt to inject arguments given at call time.
```python
@inject
def f(dependency: MyDependency):
    print(dependency)

f('Overridden dependency')  #  outputs: Overridden dependency 
```
`inject` will instantiate classes decorated with [`dependency`](#dependency). In
this way, your entire dependency graph can be specified using just `inject` and 
`dependency`.

Instances of simple types and objects you want to instantiate yourself can be
injected using keyword arguments to [`Context`](#context).
```python
@inject
def f(dependency: str):
    assert dependency == 'a named dependency'

with Environment(dependency='a named dependency'):
    f()
```
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
Dependencies that are specified as class level annotations can be overridden
using key-word arguments to `__init__`
```python
assert SomeClass(dependency='Overridden!').dependency == 'Overridden!'
```
## `dependency`
Classes decorated with `dependency` can be instantiated and injected
by `serum`.
```python
from serum import dependency, inject

@dependency
class Log:
    def info(self, message):
        print(message)


@inject
class NeedsLog:
    log: Log


assert isinstance(NeedsLog().log, Log)
```
`serum` relies on being able to inject all dependencies for `dependency` decorated classes 
recursively. To achieve this, `serum` assumes that the `__init__` method 
of `dependency` decorated classes can be called without any arguments.
This means that all arguments to `__init__` of `dependency` decorated classes must be injected using `inject`.
```python
@dependency
class SomeDependency:
    def method(self):
        pass


@inject
@dependency
class ValidDependency:  # OK!
    some_dependency: SomeDependency

    def __init__(self):
        ...


@dependency
class AlsoValidDependency:  # Also OK!
    @inject
    def __init__(self, some_dependency: SomeDependency):
        ...


@dependency
class InvalidDependency:
    def __init__(self, a):
        ...

@inject
def f(dependency: InvalidDependency):
    ...

f()  
# raises:
# TypeError: __init__() missing 1 required positional argument: 'a'

# The above exception was the direct cause of the following exception:

# InjectionError                            Traceback (most recent call last)
# ...
# InjectionError: Could not instantiate dependency <class 'InvalidDependency'> 
# when injecting argument "dependency" in <function f at 0x10a074ea0>.
```

Note that circular dependencies preventing instantiation of `dependency` decorated
classes leads to an error.
```python
@dependency
class AbstractA:
    pass

@dependency
class AbstractB:
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


with Context(A, B):
    Dependent().a  # raises: CircularDependency: Circular dependency encountered while injecting <class 'AbstractA'> in <B object at 0x1061e3898>
```
## `Context`
`Context`s provide implementations of dependencies. A `Context` will always provide the most
specific subtype of the requested type (in Method Resolution Order).
```python
@dependency
class Super:
    pass


class Sub(Super):
    pass

@inject
class NeedsSuper:
    instance: Super


with Context(Sub):
    assert isinstance(NeedsSuper().instance, Sub)
```
It is an error to inject a type in an `Context` that provides two or more equally specific subtypes of that type:
```python
class AlsoSub(Super):
    pass


with Context(Sub, AlsoSub):
    NeedsSuper() # raises: AmbiguousDependencies: Attempt to inject type <class 'Log'> with equally specific provided subtypes: <class 'MockLog'>, <class 'FileLog'>
```
`Context`s can also be used as decorators:
```python
context = Context(Sub)

@context
def f():
    assert isinstance(NeedsSuper().instance, Sub)

``` 
You can provide named dependencies of any type using keyword arguments.
```python
@inject
class Database:
    connection_string: str
    

connection_string = 'mysql+pymysql://root:my_pass@127.0.0.1:3333/my_db'
context = Context(
    connection_string=connection_string
)
with context:
    assert Database().connection_string == connection_string
```
`Context`s are local to each thread. This means that when using multi-threading
each thread must define its own environment.
```python
import threading

def worker_without_environment():
    NeedsSuper().instance  # raises NoEnvironment: Can't inject components outside an environment

def worker_with_environment():
    with Environment(Sub):
        NeedsSuper().instance  # OK!

with Context():
    threading.Thread(target=worker_without_environment()).start()
    threading.Thread(target=worker_with_environment()).start()
```

## `singleton`
To always inject the same instance of a dependency in the same `Context`, inherit from `Singleton`.
```python
from serum import singleton


@singleton
class ExpensiveObject:
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

with Context():
    instance1 = NeedsExpensiveObject()

with Context():
    assert instance1.expensive_instance is not NeedsExpensiveObject().expensive_instance
```
## `mock`
`serum` has support for injecting `MagicMock`s from the builtin
`unittest.mock` library in unittests using the `mock` utility
function. Mocks are reset
when the environment context is closed.
```python
from serum import mock

@dependency
class SomeDependency:
    def method(self):
        return 'some value' 

@inject
class Dependent:
    dependency: SomeDependency


context = Context()
with context:
    mock_dependency = mock(SomeDependency)
    mock_dependency.method.return_value = 'some mocked value'
    instance = Dependent()
    assert instance.dependency is mock_dependency
    assert instance.dependency.method() == 'some mocked value'

with context:
    instance = Dependent()
    assert instance.dependency is not mock_dependency
    assert isinstance(instance.dependency, SomeDependency)
```
`mock` uses its argument to spec the injected instance of `MagicMock`. This means
that attempting to call methods that are not defined by the mocked `Component`
leads to an error
```python
with context:
    mock_dependency = mock(SomeDependency)
    mock_dependency.no_method()  # raises: AttributeError: Mock object has no attribute 'no method'
```
Note that `mock` will only mock requests of the
exact type supplied as its argument, but not requests of
more or less specific types
```python
from unittest.mock import MagicMock

@dependency
class Super:
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


with Context():
    mock(Sub)
    needs_super = NeedsSuper()
    needs_sub = NeedsSub()
    needs_subsub = NeedsSubSub()
    assert isinstance(needs_super.injected, Super)
    assert isinstance(needs_sub.injected, MagicMock)
    assert isinstance(needs_subsub.injected, SubSub)
```
## `match`
`match` is small utility function for matching `Context` instances
with values of an environment variable.
```python
# my_script.py
from serum import match, dependency, Environment, inject

@dependency
class BaseDependency:
    def method(self):
        raise NotImplementedError()


class ProductionDependency(BaseDependency):
    def method(self):
        print('Production!')


class TestDependency(BaseDependency):
    def method(self):
        print('Test!')


@inject
def f(dependency: BaseDependency):
    dependency.method()


context = match(
    environment_variable='MY_SCRIPT_ENV', 
    default=Context(ProductionDependency),
    PROD=Context(ProductionDependency),
    TEST=Context(TestDependency)
)

with context:
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
## IPython Integration
It can be slightly annoying to import some `Context` and start it as a
context manager in the beginning of every IPython session. 
Moreover, you quite often want to run an IPython REPL in a special context,
e.g to provide configuration that is normally supplied through command line
arguments in some other way.

To this end `serum` can act as an IPython extension. To activate it,
add the following lines to your `ipython_config.py`:
```python
c.InteractiveShellApp.extensions = ['serum']
```
Finally, create a file named `ipython_context.py` in the root of your project. In it,
assign the `Context` instance you would like automatically started to a global
variable named `context`:
```python
# ipython_context.py
from serum import Context


context = Context()
```
IPython will now enter this context automatically in the beginning of
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
dependencies and allowing dependencies to be abstract.