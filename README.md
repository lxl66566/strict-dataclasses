# strict-dataclass

English | [简体中文](./README-zh_CN.md)

A Python standard library `dataclasses` enhancement implementation that provides strict type checking.

This is an experimental library. Please do not use it in production environments. You might want to use [pydantic](https://github.com/pydantic/pydantic) or [attrs](https://github.com/python-attrs/attrs) instead.

## Features

- Advantages:
  - Compatible with standard library `dataclasses` usage
  - Strict type checking during initialization and attribute modification
  - Supports validation of nested complex data types
  - Unlike pydantic, it doesn't deep copy input values
  - Performs deep checking of nested complex data types (pydantic's BaseModel / dataclass doesn't perform deep checking)
- Disadvantages:
  - Poor performance, object creation and attribute modification takes about 3 times longer than pydantic. However, it seems acceptable considering the cost of deep checking.

## Installation

```bash
pip install strict-dataclass
# Python >= 3.11
```

## Usage

### Basic Usage

```python
from strict_dataclass import strict_dataclass

@strict_dataclass
class User:
    name: str
    age: int
    is_active: bool

# Correct usage - passes type checking
user = User(name="Alice", age=25, is_active=True)

# Incorrect usage - raises TypeError
user = User(name=123, age="25", is_active=1)  # TypeError: Field 'name' must be of type str
```

### Complex Types

```python
from typing import Optional
from strict_dataclass import strict_dataclass

@strict_dataclass
class Student:
    name: str
    scores: dict[str, list[int]]
    tags: list[str]
    note: Optional[str] = None

# Correct usage
student = Student(
    name="Bob",
    scores={"math": [90], "english": [85]},
    tags=["good", "active"],
    note="Excellent student"
)

# Type errors
student = Student(
    name="Bob",
    scores={"math": ["90"]},  # TypeError: Value must be a list[int]
    tags="good",  # TypeError: Must be a list
    note=123  # TypeError: Must be a string or None
)
```
