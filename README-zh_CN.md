# strict-dataclass

[English](./README.md) | 简体中文

一个提供严格的类型检查的 Python 标准库 `dataclasses` 增强实现。

这是一个实验性质的库，请不要在生产环境中使用。您可能更希望使用 [pydantic](https://github.com/pydantic/pydantic) 或 [attrs](https://github.com/python-attrs/attrs)。

## 特性

- 优点：
  - 兼容标准库 `dataclasses` 的使用方式
  - 在初始化和属性修改时进行严格的类型检查
  - 支持嵌套复杂数据类型的验证
  - 不像 pydantic 那样会深拷贝传入的值
  - 对嵌套的复杂数据类型进行深度检查（pydantic 的 BaseModel / dataclass 没有进行深度检查）
- 缺点：
  - 性能差，对象创建耗时与属性修改耗时约为 pydantic 的 3 倍。不过考虑到深度检查的开销，这似乎是可接受的。

## 安装

```bash
pip install strict-dataclass
# Python >= 3.11
```

## 使用方法

### 基本使用

```python
from strict_dataclass import strict_dataclass

@strict_dataclass
class User:
    name: str
    age: int
    is_active: bool

# 正确使用 - 通过类型检查
user = User(name="Alice", age=25, is_active=True)

# 错误使用 - 抛出 TypeError
user = User(name=123, age="25", is_active=1)  # TypeError: Field 'name' must be of type str
```

### 复杂类型

```python
from typing import Optional
from strict_dataclass import strict_dataclass

@strict_dataclass
class Student:
    name: str
    scores: dict[str, list[int]]
    tags: list[str]
    note: Optional[str] = None

# 正确使用
student = Student(
    name="Bob",
    scores={"math": [90], "english": [85]},
    tags=["good", "active"],
    note="Excellent student"
)

# 类型错误
student = Student(
    name="Bob",
    scores={"math": ["90"]},  # TypeError: 值必须是 list[int]
    tags="good",  # TypeError: 必须是列表
    note=123  # TypeError: 必须是字符串或 None
)
```
