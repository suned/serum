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
from serum import inject, Component, Environment, abstractmethod, mock


# Components are injectable types. They can be abstract... 
class AbstractLog(Component):
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


class NeedsLog:
    # Components can be injected
    log = inject(AbstractLog)

    
class NeedsSimpleLog:
    log = inject(SimpleLog)


# Environments provide dependencies
with Environment(SimpleLog):
    assert isinstance(NeedsLog().log, SimpleLog)

# Components can't be injected outside an environment
NeedsLog().log.info('Hello serum!')  # raises: NoEnvironment

with Environment():
    # Abstract components can only be injected in environments
    # that provide concrete implementations
    NeedsLog().log.info('Hello serum!')  # raises: UnregisteredDependency
    # Concrete components can be injected even in an
    # empty environment
    NeedsSimpleLog().log.info('Hello serum!') # outputs: Hello serum!

# Environments will always provide the most specific 
# subtype of the requested type
with Environment(SimpleLog, StubLog):
    NeedsLog().log.info('Hello serum!')  # doesn't output anything
    NeedsSimpleLog().log.info('Hello serum!')  # doesn't output anything

with Environment(SimpleLog):
    # mock is a helper method for mocking components
    mock_log = mock(AbstractLog)
    mock_log.info.return_value = 'Mocked!'
    assert NeedsLog().log is mock_log
    assert NeedsLog().log.info('') == 'Mocked!'
```
# Documentation
- [`Component`](#component)
- [`Environment`](#environment)
- [`inject`](#inject)
- [`Singleton`](#singleton)
- [`immutable`](#immutable)
- [`mock`](#mock)
- [`match`](#match)
- [PEP 484](#pep-484)
- [IPython Integration](#ipython-integration)

## `Component`
`Component`s are dependencies that can be injected.
```python
from serum import Component, Environment, inject


class Log(Component):
    def info(self, message):
        print(message)


class NeedsLog:
    log = inject(Log)


instance = NeedsLog()
with Environment():
    assert isinstance(instance.log, Log)
```
`Component`s can only define an `__init__` method that takes 1 parameter.
```python
class ValidComponent(Component):  # OK!
    some_dependency = inject(SomeDependency)

    def __init__(self):
        self.value = self.some_dependency.method()


class InvalidComponent(Component):  # raises: InvalidComponent: __init__ method in Components can only take 1 parameter
    def __init__(self, a):
        self.a = a
```
To construct `Component`s with dependencies, you should instead use `inject`.
```python
class ComponentWithDependencies(Component):
    log = inject(Log)
```
Note that if you access injected members in the constructor of any type,
that type can only be instantiated inside an environment (see [`Environment`](#environment)).

Also note that circular dependencies preventing component instantiation leads to
an error.
```python
class AbstractA(Component):
    pass


class AbstractB(Component):
    pass


class A(AbstractA):
    b = inject(AbstractB)


    def __init__(self):
        self.b


class B(AbstractB):
    a = inject(AbstractA)

    def __init__(self):
        self.a


class Dependent:
    a = inject(AbstractA)


with Environment(A, B):
    Dependent().a  # raises: CircularDependency: Circular dependency encountered while injecting <class 'AbstractA'> in <B object at 0x1061e3898>
```
`Component`s can be abstract. Abstract `Component`s can only be injected in an
`Environment` that provides a concrete implementation. For convenience you can import
`abstractmethod`, `abstractclassmethod` or `abstractclassmethod` from `serum`,
but they simply refer to the decorators from the `abc` module 
in the standard library.
```python
from serum import abstractmethod


class AbstractLog(Component):
    @abstractmethod
    def info(self, message):
        pass
        
        
class NeedsLog:
    log = inject(AbstractLog)


instance = NeedsLog()
with Environment():
    instance.log  # raises UnregisteredDependency: No concrete implementation of <class 'AbstractLog'> found


class ConcreteLog(AbstractLog):
    def info(self, message):
        print(message)


with Environment(ConcreteLog):
    instance.log  # Ok!
```
## `Environment`
`Environment`s provide implementations of `Component`s. An `Environment` will always provide the most
specific subtype of the requested type (in Method Resolution Order).
```python
class Super(component):
    pass


class Sub(Super):
    pass


class NeedsSuper:
    instance = inject(Super)


with Environment(Sub):
    assert isinstance(NeedsSuper().instance, Sub)
```
It is an error to inject a type in an `Environment` that provides two or more equally specific subtypes of that type:
```python
class AlsoSub(Super):
    pass


with Environment(Sub, AlsoSub):
    NeedsSuper().instance  # raises: AmbiguousDependencies: Attempt to inject type <class 'Log'> with equally specific provided subtypes: <class 'MockLog'>, <class 'FileLog'>
```
`Environment`s can also be used as decorators:
```python
environment = Environment(Sub)

@environment
def f():
    assert isinstance(NeedsSuper().instance, Sub)

```
You can only provide subtypes of `Component` with `Environment`.
```python
class NotAComponent:
    pass


Environment(NotAComponent)  # raises: InvalidDependency: Attempt to register type that is not a Component: <class 'C'> 
```

You can however provide named values of any type using keyword arguments.
```python
class Database(Component):
    connection_string = inject('connection_string')
    

connection_string = 'mysql+pymysql://root:my_pass@127.0.0.1:3333/my_db'
environment = Environment(
    connection_string=connection_string
)
with environment:
    assert Database().connection_string == connection_string
```
`Environment`s define the scope of the injected components. This means that injected
`Component` and `Singleton` instances are destroyed when the environment context closes.
```python
needs_super = NeedsSuper()

with Environment():
    instance = needs_super.instance

with Environment():
    assert instance is not needs_super.instance
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
Moreover, injected `Component` and `Singleton` instances are local to each thread.
This means you can't share state between threads through injected components.
```python
from queue import Queue

q = Queue()
needs_super = NeedsSuper()
environment = Environment()

def first_worker():
    instance = q.get()
    with environment:
        assert instance is not needs_super.instance

def second_worker():
    with environment:
        q.put(needs_super.instance)

threading.Thread(target=first_worker()).start()
threading.Thread(target=second_worker()).start()
```
To share state between injected `Component`s in different threads, use mutable 
class/module variables and locking (yuck) 
or [`queue`](https://docs.python.org/3.6/library/queue.html).
## `inject`
When used inside an `Environment`, `inject` eagerly returns the requested dependency.
`inject` only accepts subtypes of `Component` and `str` as its argument.
Calling `inject` with a `Component` subtype as its argument will provide an instance of that
type (or a subtype depending on the environment).
```python
class Dependency(Component):
    pass


with Environment():
    assert isinstance(inject(Dependency), Dependency)
```
Calling `inject` with a `str` argument will return the named value associated with
that keyword argument in the current `Environment`. Note that type inference is
impossible for this pattern, and you have to annotate the type of the injected
dependency if you want PEP484 features to work.
```python
with Environment(key='value'):
    value: str = inject('key')
    assert value == 'value'
```
When used outside an `Environment`, `inject` returns a 
[descriptor](https://docs.python.org/3/reference/datamodel.html#implementing-descriptors) 
that can be used to lazily inject a dependency at a later time.
```python
class Dependency(Component):
    pass
    
print(type(inject(Dependency)))  # outputs: LazyDependency

class Dependent:
    dependency = inject(Dependency)


with Environment():
    assert isinstance(Dependent().dependency, Dependency) 
```
Lazily injected `Component`s can't be accessed outside an `Environment` context:
```python
class Dependency(Component):
    pass


class Dependent:
    dependency = inject(Dependency)


Dependent().dependency  # raises NoEnvironment: Can't inject dependencies outside an environment 
```
Calling `inject` with anything else than a `Component` subtype or `str` is
an error.
```python
class NotAComponent:
    pass
    

class InvalidDependent:
    dependency = inject(NotAComponent)  # raises: InvalidDependency: Attempt to inject type that is not a Component or str: <class 'C'>
```
Injected `Component` properties are immutable
```python
with Environment():
    Dependent().dependency = 'mutate this'  # raises AttributeError: Can't set injected attribute
```
A lazily injected member of an instance will always refer to the same component 
instance. Lazily injected members of different instances will refer to different
component instances.
```python
with Environment():
    instance1 = NeedsLog()
    assert instance1.log is instance1.log
    instance2 = NeedsLog()
    assert instance2.log is not instance1.log
```
When lazily injected components are used in nested environments, the following
rules apply:

- Attributes injected in the outer environment refer to the same instances
in the inner environment
- Attributes injected in the inner environment are destroyed when the environment context
closes
```python
with Environment():
    outer = Dependent()
    inner = Dependent()
    outer_dependency = outer.dependency  # Accessing the lazy attribute instantiates the component
    with Environment():
        inner_dependency = inner.dependency
        # Instances created in the outer environment are still available in the inner environment
        assert outer.dependency is outer_dependency
    # Since the inner environment context is closed, a new instance will be created
    # in the outer environment
    assert inner.dependency is not inner_dependency
    assert outer.dependency is outer_dependency
```
Note that the eager version of `inject` makes it possible to write something like:
```python
class Dependent:
    with Environment():
        dependency = inject(Dependency)
```
Which is essentially equivalent to:
```python
class Dependent:
    dependency = Dependency()
```
Or similarly
```python
with Environment():
    def f(dependency=inject(Dependency)):
        print(dependency)
```
In the above examples, `dependency` is assigned to eagerly, and will not change
based on changing environments. This very much defeats the purpose of `inject`.
The intended use case of eager `inject` is for use inside functions and methods that can
be run in different environments.
```python
def f():
    dependency = inject(Dependency)
    print(type(dependency))

class TestDependency(Dependency):
    pass

environment = Environment()
test_environment = Environment(TestDependency)

with environment:
    f()  # outputs: Dependency

with test_environment:
    f()  # outputs: TestDependency
```
If you want to use `inject` to eagerly inject instance members in a class,
do it inside `__init__`
```python
class Dependent:
    def __init__(self):
        self.dependency = inject(Dependency)
```
Note that this will restrict instances of `Dependent` to be instantiated
inside environments.

Similarly, if you want to use `inject` to assign to keyword arguments, wrap it in
a `lambda`
```python
def f(dependency=lambda: inject(Dependency)):
    print(dependency())
```
## `Singleton`
To always inject the same instance of a component in the same `Environment`, inherit from `Singleton`.
```python
from serum import Singleton


class ExpensiveObject(Singleton):
    pass


class NeedsExpensiveObject:
    expensive_instance = inject(ExpensiveObject)


with Environment():
    instance1 = NeedsExpensiveObject()
    instance2 = NeedsExpensiveObject()
    assert instance1.expensive_instance is instance2.expensive_instance
```
Note that even `Singleton` objects are destroyed when an `Environment`
context is closed
```python
needs_expensive_object = NeedsExpensiveObject()
with Environment():
    expensive_instance = needs_expensive_object.expensive_instance

with Environment():
    assert expensive_instance is not needs_expensive_object.expensive_instance
```
## `immutable`
If you want to define immutable members (constants) in components (or any other classes), 
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


class Dependency(Component):
    def method(self):
        return 'some value' 


class Dependent:
    dependency = inject(Dependency)


environment = Environment()
with environment:
    mock_dependency = mock(Dependency)
    mock_dependency.method.return_value = 'some mocked value'
    instance = Dependent()
    assert instance.dependency is mock_dependency
    assert instance.dependency.method() == 'some mocked value'

with environment:
    instance = Dependent()
    assert instance.dependency is not mock_dependency
    assert isinstance(instance.dependency, Dependency)

mock(Dependency)  # raises: NoEnvironment: Can't register mock outside environment
```
`mock` uses its argument to spec the injected instance of `MagicMock`. This means
that attempting to call methods that are not defined by the mocked `Component`
leads to an error
```python
with environment:
    mock_dependency = mock(Dependency)
    mock_dependency.no_method()  # raises: AttributeError: Mock object has no attribute 'no method'
```
Note that `mock` will only mock requests of the
exact type supplied as its argument, but not requests of
more or less specific types
```python
from unittest.mock import MagicMock


class Super(Component):
    pass


class Sub(Super):
    pass


class SubSub(Sub):
    pass


class NeedsSuper:
    injected = inject(Super)


class NeedsSub:
    injected = inject(Sub)


class NeedsSubSub:
    injected = inject(SubSub)


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
from serum import match, Component, abstractmethod, Environment, inject

class Dependency(Component):
    @abstractmethod
    def method(self):
        pass


class ProductionDependency(Dependency):
    def method(self):
        print('Production!')


class TestDependency(Dependency):
    def method(self):
        print('Test!')


environment = match(
    environment_variable='MY_SCRIPT_ENV', 
    default=Environment(ProductionDependency),
    PROD=Environment(ProductionDependency),
    TEST=Environment(TestDependency)
)
with environment:
    inject(Dependency).method()
      
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