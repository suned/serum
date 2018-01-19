# Description
`serum` is a fresh take on Dependency Injection in Python 3.

It's pure python, has no dependencies, and is less than 150 lines of code.
# Installation
```
> pip install serum
```
# Documentation
`serum` uses 3 main abstractions: `Component`, `Environment` and `inject`.

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
`Environment`s provide implementations of `Components`. An `Environment` will always provide the most
specific subtype of the requested type.
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
Similarly, you can't inject types that are not `Component` subtypes.
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
You can define mutable static fields in a `Component`. If you want to define 
immutable static fields (constants), `serum` provides the `immutable` utility
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
`Component`s can't define an `__init__` method.
```python
class InvalidComponent(Component):  # raises InvalidComponent: Components should not have an __init__ method
    def __init__(self):
        pass
```
To construct `Component`s with dependencies, you should instead use `inject`
```python
class ComponentWithDependencies(Component):
    log = inject(Log)
```
`Component`s can be abstract. Abstract `Component`s can't be instantiated in an
`Environment` without a concrete implementation. For convenience you can import
`abstractmethod`, `abstractclassmethod` or `abstractclassmethod` from `serum`,
but they are simply references to the equivalent decorators from the `abc` module 
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
`Component`s are injected lazily. This means that you can instantiate classes
with injected dependencies outside an environment and use it in different
environments with different effects.
```python
class MockLog(AbstractLog):
    def info(self, message):
        pass

instance = NeedsLog()
with Environment(ConcreteLog):
    instance.log.info('Hello serum!')  # outputs: Hello serum!

with Environment(MockLog):
    instance.log.info('Hello serum!')  # doesn't output anything
```
`Environment`s are local to each thread. This means that when using multi threading
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
`serum` is designed for type inference with `mypy` (or some other PEP 484 tool)
(Work in progress). I find it works best with PyCharm's type checker.
```python
# my_script.py
from serum import inject, Component, abstractmethod


class AbstractLog(Component):
    @abstractmethod
    def info(self, message):
        pass


class NeedsLog:
    log = inject(AbstractLog)
    def test(self):
        self.log.warning('DANGER!')
```
```
> mypy my_script.py  # should fail, but currently doesn't :(
```
# Why?
If you've been researching Dependency Injection frameworks for python,
you've no doubt come across this opinion:

>_"You dont need Dependency Injection in python. 
>You can just use duck typing and monkey patching!"_
 
The position behind this statement is often that you only need Dependency 
Injection in statically typed language.

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
detailed tutorial.
