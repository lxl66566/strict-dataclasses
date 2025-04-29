import unittest
from typing import Dict, List, Optional, Tuple, Union

from strict_dataclasses import strict_dataclass


@strict_dataclass
class SimpleClass:
    name: str
    age: int
    is_active: bool


@strict_dataclass
class NestedClass:
    simple: SimpleClass
    score: float


@strict_dataclass
class ComplexClass:
    names: List[str]
    scores: Dict[str, int]
    optional_field: Optional[int]
    union_field: Union[str, int]
    nested_list: List[List[int]]
    nested_dict: Dict[str, Dict[str, int]]
    tuple_field: Tuple[int, str, bool]


class TestStrictDataclass(unittest.TestCase):
    def test_simple_class_init(self):
        # 测试正常初始化
        obj = SimpleClass(name="test", age=25, is_active=True)
        self.assertEqual(obj.name, "test")
        self.assertEqual(obj.age, 25)
        self.assertTrue(obj.is_active)

    def test_simple_class_type_error(self):
        # 测试类型错误
        with self.assertRaises(TypeError):
            SimpleClass(name=123, age=25, is_active=True)  # name 应该是 str
        with self.assertRaises(TypeError):
            SimpleClass(name="test", age="25", is_active=True)  # age 应该是 int
        with self.assertRaises(TypeError):
            SimpleClass(name="test", age=25, is_active=1)  # is_active 应该是 bool

    def test_simple_class_setattr(self):
        # 测试属性设置
        obj = SimpleClass(name="test", age=25, is_active=True)
        obj.name = "new_name"
        self.assertEqual(obj.name, "new_name")

        with self.assertRaises(TypeError):
            obj.name = 123  # 类型错误

    def test_nested_class(self):
        # 测试嵌套类
        simple = SimpleClass(name="test", age=25, is_active=True)
        nested = NestedClass(simple=simple, score=95.5)
        self.assertEqual(nested.simple.name, "test")
        self.assertEqual(nested.score, 95.5)

        with self.assertRaises(TypeError):
            NestedClass(
                simple="not_a_simple_class", score=95.5
            )  # simple 应该是 SimpleClass

    def test_complex_class(self):
        # 测试复杂类型
        obj = ComplexClass(
            names=["a", "b", "c"],
            scores={"math": 90, "english": 85},
            optional_field=None,
            union_field="test",
            nested_list=[[1, 2], [3, 4]],
            nested_dict={"a": {"b": 1}},
            tuple_field=(1, "test", True),
        )

        # 测试各种类型错误
        with self.assertRaises(TypeError):
            ComplexClass(
                names="not_a_list",  # 应该是 List[str]
                scores={"math": 90},
                optional_field=None,
                union_field="test",
                nested_list=[[1, 2]],
                nested_dict={"a": {"b": 1}},
                tuple_field=(1, "test", True),
            )

        with self.assertRaises(TypeError):
            ComplexClass(
                names=["a", "b"],
                scores={"math": "90"},  # 值应该是 int
                optional_field=None,
                union_field="test",
                nested_list=[[1, 2]],
                nested_dict={"a": {"b": 1}},
                tuple_field=(1, "test", True),
            )

    def test_multiple_setattr(self):
        # 测试多次设置属性
        obj = SimpleClass(name="test", age=25, is_active=True)

        # 多次设置正确的值
        for i in range(5):
            obj.name = f"name_{i}"
            obj.age = i
            obj.is_active = bool(i % 2)
            self.assertEqual(obj.name, f"name_{i}")
            self.assertEqual(obj.age, i)
            self.assertEqual(obj.is_active, bool(i % 2))

        # 多次设置错误的值
        for i in range(5):
            with self.assertRaises(TypeError):
                obj.name = i  # 类型错误

    def test_optional_fields(self):
        # 测试可选字段
        obj = ComplexClass(
            names=["a"],
            scores={"a": 1},
            optional_field=None,
            union_field="test",
            nested_list=[[1]],
            nested_dict={"a": {"b": 1}},
            tuple_field=(1, "test", True),
        )

        # 设置可选字段为 None
        obj.optional_field = None
        self.assertIsNone(obj.optional_field)

        # 设置可选字段为有效值
        obj.optional_field = 123
        self.assertEqual(obj.optional_field, 123)

        # 设置可选字段为无效值
        with self.assertRaises(TypeError):
            obj.optional_field = "not_an_int"

    def test_union_fields(self):
        # 测试联合类型字段
        obj = ComplexClass(
            names=["a"],
            scores={"a": 1},
            optional_field=None,
            union_field="test",
            nested_list=[[1]],
            nested_dict={"a": {"b": 1}},
            tuple_field=(1, "test", True),
        )

        # 设置联合类型字段为字符串
        obj.union_field = "string_value"
        self.assertEqual(obj.union_field, "string_value")

        # 设置联合类型字段为整数
        obj.union_field = 123
        self.assertEqual(obj.union_field, 123)

        # 设置联合类型字段为无效值
        with self.assertRaises(TypeError):
            obj.union_field = 1.23  # 不是 str 或 int


if __name__ == "__main__":
    unittest.main()
