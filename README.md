# Build Status

[![CircleCI](https://circleci.com/gh/suned/serum.svg?style=svg)](https://circleci.com/gh/suned/serum) [![codecov](https://codecov.io/gh/suned/serum/branch/master/graph/badge.svg)](https://codecov.io/gh/suned/serum)



# Description
`serum` is a fresh take on Dependency Injection in Python 3.

`serum` is pure python, has no dependencies, and is less than 300 lines of code.
# Installation
```
> pip install serum
```
# Quickstart
```python
from serum import inject, Component, Environment, abstractmethod

class Log(Component):
    @abstractmethod
    def info(self, message: str):
        pass

class SimpleLog(Log):
    def info(self, message: str):
        print(message)

class StubLog(Log):
    def info(self, message: str):
        pass

class NeedsLog:
    log = inject(Log)

NeedsLog().log.info('Hello serum!')  # raises: NoEnvironment

with Environment():
    NeedsLog().log.info('Hello serum!')  # raises: UnregisteredDependency

with Environment(SimpleLog):
    NeedsLog().log.info('Hello serum!')  # outputs: Hello serum!

with Environment(StubLog):
    NeedsLog().log.info('Hello serum!')  # doesn't output anything

class NeedsSimpleLog:
    log = inject(SimpleLog)

with Environment():
    NeedsSimpleLog().log.info('Hello serum!')  # outputs: Hello serum!
```
# Documentation
- [`Component`](#component)
- [`Singleton`](#singleton)
- [`Environment`](#environment)
- [`inject`](#inject)
- [`immutable`](#immutable)
- [`mock`](#mock)
- [PEP 484](#pep-484)

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
To construct `Component`s with dependencies, you should instead use `inject`
```python
class ComponentWithDependencies(Component):
    log = inject(Log)
```
Note that if you access injected members in the constructor of any type,
that type can only be instantiated inside an environment.

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
`Component`s can be abstract. Abstract `Component`s can't be injected in an
`Environment` that doesn't provide a concrete implementation. For convenience you can import
`abstractmethod`, `abstractclassmethod` or `abstractclassmethod` from `serum`,
but they are refer to the decorators from the `abc` module 
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
## `Singleton`
If you want to always inject the same instance of an object, inherit from `Singleton`.
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
## `Environment`
`Environment`s provide implementations of `Components`. An `Environment` will always provide the most
specific subtype of the requested type (in Method Resolution Order).
```python
class MockLog(Log):
    def info(self, message):
        pass

with Environment(MockLog):
    assert isinstance(instance.log, MockLog)
```
It is an error to inject a type in an `Environment` that provides two or more equally specific subtypes of that type:
```python
class FileLog(Log):
    _file = 'log.txt'
    def info(self, message):
        with open(self._file, 'w') as f:
            f.write(message)

with Environment(MockLog, FileLog):
    instance.log  # raises: AmbiguousDependencies: Attempt to inject type <class 'Log'> with equally specific provided subtypes: <class 'MockLog'>, <class 'FileLog'>
```
`Environment`s can also be used as decorators:
```python
test_environment = Environment(MockLog)

@test_environment
def f():
    assert isinstance(instance.log, MockLog)

```
You can only provide subtypes of `Component` with `Environment`.
```python
class C:
    pass

Environment(C)  # raises: InvalidDependency: Attempt to register type that is not a Component: <class 'C'> 
```
`Environment`s are local to each thread. This means that when using multi-threading
each thread must define its own environment.
```python
import threading

def worker_without_environment():
    NeedsLog().log  # raises NoEnvironment: Can't inject components outside an environment

def worker_with_environment():
    with Environment(ConcreteLog):
        NeedsLog().log  # OK!

with Environment(ConcreteLog):
    threading.Thread(target=worker_without_environment()).start()
    threading.Thread(target=worker_with_environment()).start()
```
## `inject`
Just as you can only provide subtypes of `Component` with `Environment`, 
you can only inject subtypes of `Component`.
```python
class InvalidDependent:
    dependency = inject(C)  # raises: InvalidDependency: Attempt to inject type that is not a Component: <class 'C'>
```
Injected `Component`s can't be accessed outside an `Environment` context:
```python
instance.log  # raises NoEnvironment: Can't inject components outside an environment 
```
Injected `Component`s are immutable
```python
with Environment():
    instance.log = 'mutate this'  # raises AttributeError: Can't set property
```
An injected member of an instance will always refer to the same component 
instance. Injected members of different instances will refer to different
component instances
```python
with Environment():
    instance1 = NeedsLog()
    assert instance1.log is instance1.log
    instance2 = NeedsLog()
    assert instance2.log is not instance1.log
``` 
## `immutable`
You can define mutable static fields in a `Component`. If you want to define 
immutable static fields (constants) in components (or any other classes), 
`serum` provides the `immutable` utility
that also supports type inference with PEP 484 tools. 
```python
from serum import immutable

class Immutable(Component):
    value = immutable(1)

i = Immutable()
i.value = 2  # raises AttributeError: Can't set property
```
This is just convenience for:
```python
class Immutable(Component):
    value = property(fget=lambda _: 1)
```
## `mock`
`serum` has support for injecting `MagicMock`s from the builtin
`unittest.mock` library in unittests using the `mock` utility
function. `mock` is only usable inside an an environment context. Mocks are reset
when the environment context is closed.
```python
from serum import mock

environment = Environment(ConcreteLog)
with environment:
    log_mock = mock(AbstractLog)
    log_mock.method.return_value = 'some value'
    instance = NeedsLog()
    assert instance.log is log_mock
    assert instance.log.method() == 'some value'

with environment:
    instance = NeedsLog()
    assert instance.log is not log_mock
    assert isinstance(instance.log, ConcreteLog)

mock(AbstractLog)  # raises: NoEnvironment: Can't register mock outside environment
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
## PEP 484
`serum` is designed for type inference with PEP 484 tools (work in progress). 
This feature is currently only supported for the PyCharm type checker.

![type inference in PyCharm](https://i.imgur.com/8fvvAQ2.png)
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
