# Description
`serum` is a fresh take on a Dependency Injection framework for Python 3.

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
`Environment`s provide implementations of `Components`.
```python
class MockLog(Log):
    def info(self, message):
        pass

with Environment(MockLog):
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
`serum` is designed for type inference with `mypy`.
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
> mypy my_script.py
```