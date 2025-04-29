import statistics
import timeit
from dataclasses import dataclass
from typing import Dict, List, Optional

from pydantic import BaseModel
from pydantic.dataclasses import dataclass as pydantic_dataclass

from strict_dataclass import strict_dataclass


# 定义三种不同的数据类
@dataclass
class StandardClass:
    name: str
    age: int
    scores: Dict[str, int]
    tags: List[str]
    note: Optional[str]


@strict_dataclass
class StrictClass:
    name: str
    age: int
    scores: Dict[str, int]
    tags: List[str]
    note: Optional[str]


@pydantic_dataclass
class PydanticClass:
    name: str
    age: int
    scores: Dict[str, int]
    tags: List[str]
    note: Optional[str]


class PydanticClassModel(BaseModel):
    name: str
    age: int
    scores: Dict[str, int]
    tags: List[str]
    note: Optional[str]


# 测试数据
valid_data = {
    "name": "test",
    "age": 25,
    "scores": {"math": 90, "english": 85},
    "tags": ["student", "class_1"],
    "note": "good student",
}

invalid_data = {
    "name": 123,  # 应该是 str
    "age": "25",  # 应该是 int
    "scores": {"math": "90"},  # value 应该是 int
    "tags": "not_a_list",  # 应该是 list
    "note": 123,  # 应该是 str 或 None
}


def benchmark_creation(cls, data, number=10000, rounds=5):
    """测试对象创建性能"""
    times = []
    for _ in range(rounds):
        time_taken = timeit.timeit(lambda: cls(**data), number=number)
        times.append(time_taken)
    return times


def benchmark_attribute_access(cls, data, number=10000, rounds=5):
    """测试属性访问性能"""
    obj = cls(**data)
    times = []
    for _ in range(rounds):
        time_taken = timeit.timeit(
            lambda: (obj.name, obj.age, obj.scores, obj.tags, obj.note), number=number
        )
        times.append(time_taken)
    return times


def benchmark_attribute_modification(cls, data, number=10000, rounds=5):
    """测试属性修改性能"""
    obj = cls(**data)
    times = []

    def modify():
        obj.name = "new_name"
        obj.age = 26
        obj.note = "updated"

    for _ in range(rounds):
        time_taken = timeit.timeit(modify, number=number)
        times.append(time_taken)
    return times


def benchmark_error_handling(cls, data, rounds=5):
    """测试错误数据处理性能"""
    times = []
    errors = []
    for _ in range(rounds):
        start = timeit.default_timer()
        try:
            cls(**data)
        except Exception as e:
            end = timeit.default_timer()
            times.append(end - start)
            errors.append(str(e))
    return times, errors


def print_stats(label, times):
    """打印统计信息"""
    if not times:
        print(f"{label}: 无数据")
        return

    print(
        f"{label}: 平均: {statistics.mean(times):.6f} 秒 中位数: {statistics.median(times):.6f} 秒 标准差: {statistics.stdev(times):.6f} 秒 最小: {min(times):.6f} 秒 最大: {max(times):.6f} 秒"
    )


def run_benchmarks():
    iterations = 10000
    rounds = 5
    print(f"运行每项测试 {iterations} 次，共 {rounds} 轮")
    print("\n=== 正常数据测试 ===")

    # 测试对象创建
    print("\n对象创建性能:")
    std_times = benchmark_creation(StandardClass, valid_data, iterations, rounds)
    strict_times = benchmark_creation(StrictClass, valid_data, iterations, rounds)
    pydantic_times = benchmark_creation(PydanticClass, valid_data, iterations, rounds)
    pydantic_model_times = benchmark_creation(
        PydanticClassModel, valid_data, iterations, rounds
    )

    print_stats("标准 dataclass", std_times)
    print_stats("strict_dataclass", strict_times)
    print_stats("pydantic dataclass", pydantic_times)
    print_stats("pydantic BaseModel", pydantic_model_times)

    # 测试属性访问
    print("\n属性访问性能:")
    std_times = benchmark_attribute_access(
        StandardClass, valid_data, iterations, rounds
    )
    strict_times = benchmark_attribute_access(
        StrictClass, valid_data, iterations, rounds
    )
    pydantic_times = benchmark_attribute_access(
        PydanticClass, valid_data, iterations, rounds
    )
    pydantic_model_times = benchmark_attribute_access(
        PydanticClassModel, valid_data, iterations, rounds
    )

    print_stats("标准 dataclass", std_times)
    print_stats("strict_dataclass", strict_times)
    print_stats("pydantic dataclass", pydantic_times)
    print_stats("pydantic BaseModel", pydantic_model_times)

    # 测试属性修改
    print("\n属性修改性能:")
    std_times = benchmark_attribute_modification(
        StandardClass, valid_data, iterations, rounds
    )
    strict_times = benchmark_attribute_modification(
        StrictClass, valid_data, iterations, rounds
    )
    pydantic_times = benchmark_attribute_modification(
        PydanticClass, valid_data, iterations, rounds
    )
    pydantic_model_times = benchmark_attribute_modification(
        PydanticClassModel, valid_data, iterations, rounds
    )

    print_stats("标准 dataclass", std_times)
    print_stats("strict_dataclass", strict_times)
    print_stats("pydantic dataclass", pydantic_times)
    print_stats("pydantic BaseModel", pydantic_model_times)

    print("\n=== 错误数据测试 ===")
    print("\n错误数据处理性能:")

    # 标准 dataclass 不进行类型检查，所以跳过
    print("标准 dataclass: 不执行类型检查")

    # strict_dataclass
    strict_times, strict_errors = benchmark_error_handling(
        StrictClass, invalid_data, rounds
    )
    print_stats("strict_dataclass 错误检测", strict_times)

    # pydantic dataclass
    pydantic_times, pydantic_errors = benchmark_error_handling(
        PydanticClass, invalid_data, rounds
    )
    print_stats("pydantic dataclass 错误检测", pydantic_times)

    # pydantic BaseModel
    pydantic_model_times, pydantic_model_errors = benchmark_error_handling(
        PydanticClassModel, invalid_data, rounds
    )
    print_stats("pydantic BaseModel 错误检测", pydantic_model_times)


if __name__ == "__main__":
    run_benchmarks()
