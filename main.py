# pyright: reportAttributeAccessIssue=false

import inspect
import typing
from datetime import datetime  # 示例中用到


class Intersection:
    """Represents a type intersection (value must match ALL types)."""

    def __class_getitem__(cls, types):
        if not isinstance(types, tuple):
            types = (types,)
        # Store the types in __args__ similar to typing.Union
        instance = object.__new__(cls)
        instance.__args__ = types
        return instance

    def __repr__(self):
        return f"Intersection[{', '.join(repr(arg) for arg in self.__args__)}]"


class Not:
    """Represents a type negation (value must NOT match the type)."""

    def __class_getitem__(cls, type_to_negate):
        # Store the negated type in __args__ as a single-element tuple
        instance = object.__new__(cls)
        instance.__args__ = (type_to_negate,)
        return instance

    def __repr__(self):
        return f"Not[{repr(self.__args__[0])}]"


# --- SNP Metaclass ---


class SNPMeta(type):
    """
    Metaclass for SNP models, providing type checking on init and setattr.
    """

    def __new__(metacls, name, bases, cls_dict):
        annotations = cls_dict.get("__annotations__", {})

        # We will call the static validation method directly via SNPMeta,
        # so no need to add it to the class dictionary here.
        # cls_dict['_validate_field'] = SNPMeta._validate_field_impl # REMOVED

        original_init = cls_dict.get("__init__")  # Not used in this simple model

        def __init__(self, **kwargs):
            # Validate and set fields provided in kwargs
            for field_name, field_type in annotations.items():
                if field_name in kwargs:
                    value = kwargs[field_name]
                    try:
                        # Call the static method directly using the metaclass name
                        SNPMeta._validate_field_impl(field_name, value, field_type)
                        # Set the attribute directly using object.__setattr__
                        # to avoid triggering our custom __setattr__ during initialization
                        object.__setattr__(self, field_name, value)
                    except Exception as e:
                        # Catch any validation error and re-raise with context
                        raise TypeError(
                            f"Validation failed for field '{field_name}': {e}"
                        ) from e

            # Check for missing required fields (those in annotations but not in kwargs)
            for field_name, field_type in annotations.items():
                if field_name not in kwargs:
                    # Check if the field is Optional (Union with NoneType)
                    is_optional = typing.get_origin(
                        field_type
                    ) is typing.Union and type(None) in typing.get_args(field_type)
                    # Check if the field has a default value defined in the class body
                    # Note: This simple check doesn't handle complex defaults like default_factory
                    # Access cls_dict from the closure
                    has_default = field_name in cls_dict

                    if not is_optional and not has_default:
                        raise TypeError(f"Missing required field '{field_name}'")
                    elif has_default:
                        # If it has a default and wasn't in kwargs, set the default
                        # We need to get the default value from the class dictionary
                        default_value = cls_dict[field_name]
                        # Validate the default value itself
                        try:
                            # Call the static method directly
                            SNPMeta._validate_field_impl(
                                field_name, default_value, field_type
                            )
                            object.__setattr__(self, field_name, default_value)
                        except Exception as e:
                            raise TypeError(
                                f"Validation failed for default value of field '{field_name}': {e}"
                            ) from e

            # If there was an original __init__ and we wanted to call it *after* our setup,
            # we would do it here. But for a simple model, our __init__ replaces it.
            if original_init:
                original_init(self, **kwargs)

        cls_dict["__init__"] = __init__

        # --- Create the new __setattr__ method ---
        # original_setattr = cls_dict.get('__setattr__') # Not used in this simple model

        def __setattr__(self, name, value):
            # If the attribute being set is one of the annotated fields, validate it
            if name in annotations:
                field_type = annotations[name]
                try:
                    # Call the static method directly using the metaclass name
                    SNPMeta._validate_field_impl(name, value, field_type)
                except Exception as e:
                    # Catch any validation error and re-raise with context
                    raise TypeError(f"Validation failed for field '{name}': {e}") from e

            # Set the attribute using the base object's setattr to avoid infinite recursion
            object.__setattr__(self, name, value)

        cls_dict["__setattr__"] = __setattr__

        # Create the class using the modified dictionary
        cls = super().__new__(metacls, name, bases, cls_dict)
        return cls

    @staticmethod
    def _validate_field_impl(name, value, type_spec) -> None:
        """
        Recursive validation logic for a single field value against its type specification.
        Raises TypeError or ValueError on failure.
        """
        # 1. Handle custom validation function (callable but not a typing type)
        # Check if it's a function/callable and doesn't have typing attributes like __origin__
        if inspect.isfunction(type_spec) or (
            inspect.isclass(type_spec) and issubclass(type_spec, typing.Callable)
        ):
            # Exclude typing types that are also callable (like typing.Callable itself)
            if not hasattr(type_spec, "__origin__") and not hasattr(
                type_spec, "__args__"
            ):
                try:
                    # Call the custom validator. It's expected to raise on failure.
                    type_spec(value)
                except Exception as e:
                    # Wrap the custom validator's error
                    raise ValueError(
                        f"Custom validator {getattr(type_spec, '__name__', type_spec)!r} failed: {e}"
                    ) from e
                return

        # 2. Handle custom Intersection type (e.g., Intersection[T1, T2])
        if isinstance(type_spec, Intersection):
            if not hasattr(type_spec, "__args__"):
                raise TypeError(
                    f"Invalid Intersection type specification: {type_spec!r}"
                )
            for i, sub_type in enumerate(type_spec.__args__):
                try:
                    # Value must pass ALL intersection types
                    SNPMeta._validate_field_impl(name, value, sub_type)
                    print(f"Value matched intersection type {sub_type!r}")
                except Exception as e:
                    # If any intersection type fails, the whole intersection fails
                    print(
                        f"Intersection validation failed for sub-type {i} ({sub_type!r}): {e}"
                    )
                    raise TypeError(
                        f"Intersection validation failed for sub-type {i} ({sub_type!r}): {e}"
                    ) from e
            return  # All intersection types passed

        # 3. Handle custom Negation type (e.g., Not[T])
        if isinstance(type_spec, Not):
            if not hasattr(type_spec, "__args__") or len(type_spec.__args__) != 1:
                raise TypeError(f"Invalid Not type specification: {type_spec!r}")
            negated_type = type_spec.__args__[0]
            try:
                # Try validating against the negated type
                SNPMeta._validate_field_impl(name, value, negated_type)
                print(f"negated type {negated_type!r}, raised")
                raise TypeError(
                    f"Value unexpectedly matched negated type {negated_type!r}"
                )
            except Exception:
                # If validation of the negated type FAILS (raises), the Negation SUCCEEDS
                pass  # Validation passed
            return

        # 4. Handle standard typing types and built-ins
        origin = typing.get_origin(type_spec)
        args = typing.get_args(type_spec)

        # Handle Union (includes Optional, which is Union[T, NoneType])
        if origin is typing.Union:
            # Check if value matches ANY of the union types
            for arg in args:
                try:
                    SNPMeta._validate_field_impl(name, value, arg)
                    return  # Found a match, validation passed for Union
                except Exception:
                    pass  # This branch failed, try the next one
            # If we get here, none of the union types matched
            # Construct a helpful error message listing the expected types
            expected_types_str = ", ".join(repr(arg) for arg in args)
            raise TypeError(
                f"Value does not match any expected types in Union ({expected_types_str})"
            )

        # Handle collections with type parameters (list[T], dict[K, V], etc.)
        # Note: This handles typing.List, typing.Dict, and also built-in list, dict
        # when used with __class_getitem__ like list[str] (origin will be list)
        if origin is list or origin is typing.List:
            if not isinstance(value, list):
                raise TypeError(f"Expected list, got {type(value).__name__}")
            if args:  # Has type parameters (e.g., list[str])
                elem_type = args[0]
                for i, elem in enumerate(value):
                    try:
                        # Recursively validate each element
                        SNPMeta._validate_field_impl(
                            f"{name}[{i}]", elem, elem_type
                        )  # Pass index for better error message
                    except Exception as e:
                        raise TypeError(
                            f"Validation failed for element {i} in list '{name}': {e}"
                        ) from e
            # else: list without type parameter (e.g., list) - any list is fine

        elif origin is dict or origin is typing.Dict:
            if not isinstance(value, dict):
                raise TypeError(f"Expected dict, got {type(value).__name__}")
            if args:  # Has type parameters (e.g., dict[str, int])
                if len(args) != 2:
                    raise TypeError(
                        f"Dict type hint requires 2 type parameters (key, value), got {len(args)}"
                    )
                key_type, value_type = args
                for k, v in value.items():
                    try:
                        # Recursively validate key and value
                        SNPMeta._validate_field_impl(f"{name}.keys()", k, key_type)
                        SNPMeta._validate_field_impl(f"{name}[{k!r}]", v, value_type)
                    except Exception as e:
                        raise TypeError(
                            f"Validation failed for item with key {k!r} in dict '{name}': {e}"
                        ) from e
            # else: dict without type parameter (e.g., dict) - any dict is fine

        # Add other collections (tuple, set, frozenset) similarly if needed
        # elif origin is tuple or origin is typing.Tuple: ...
        # elif origin is set or origin is typing.Set: ...

        # Handle basic types and classes (when origin is None)
        elif origin is None:
            # Check if type_spec is a type (e.g., str, int, custom class)
            if isinstance(type_spec, type):
                if not isinstance(value, type_spec):
                    raise TypeError(
                        f"Expected {type_spec.__name__}, got {type(value).__name__}"
                    )
            # Handle typing.Any - any value is valid
            elif type_spec is typing.Any:
                pass
            # Add other special typing types if needed (Callable, etc.)
            # elif type_spec is typing.Callable: ...
            else:
                # Fallback for unhandled types - maybe raise or pass? Let's pass for now.
                # print(f"Warning: Unhandled type specification {type_spec!r} for field {name}")
                pass  # Assume valid if type spec is unknown/unhandled

        # Fallback for unhandled origins (e.g., typing.Literal, typing.Protocol)
        else:
            print(
                f"Warning: Unhandled type origin {origin!r} for type specification {type_spec!r} for field {name}"
            )
            pass


class SNP(metaclass=SNPMeta):
    """
    Base class for models with automatic type checking.
    Inherit from this class to enable validation.
    """

    pass


# 自定义验证函数
def my_val(input):
    """Custom validator: input must be a string starting with 'a'."""
    assert isinstance(input, str), "input must be string"
    assert input.startswith("a"), (
        "input must start with 'a'"
    )  # Use startswith for clarity


# 另一个 SNP 模型作为嵌套类型
class ChatOptions(SNP):
    timeout: int = 30  # 示例带默认值 (SNP现在会处理这个默认值)
    enabled: bool


# 你的 ChatSession 示例
class ChatSession(SNP):
    id: str
    created_at: datetime

    def other_functions(self):
        """An example of a non-validation method."""
        print(f"Session ID: {self.id}")


class SendMessageRequest(SNP):
    content: str
    messages: Intersection[list[dict], Not[typing.List[typing.Dict[str, str]]]]
    options: typing.Optional[ChatOptions] = None  # 使用 Union[ChatOptions, NoneType]
    other_info: my_val  # 使用自定义验证函数


# --- 测试 ---

# print("--- Testing ChatSession ---")
# try:
#     session = ChatSession(id="session-123", created_at=datetime.now())
#     print(f"Created session: {session.id}, {session.created_at}")

#     session.id = "session-456"  # Valid update
#     print(f"Updated session ID: {session.id}")

#     # session.created_at = "not a datetime"  # Invalid update - uncomment to test failure
#     # print("This line should not be reached if validation fails")

#     # session = ChatSession(
#     #     id=123, created_at=datetime.now()
#     # )  # Invalid init - uncomment to test failure
#     # print("This line should not be reached if validation fails")

#     # session = ChatSession(
#     #     id="session-789"
#     # )  # Missing required field - uncomment to test failure
#     # print("This line should not be reached if validation fails")

#     session.other_functions()

# except Exception as e:
#     print(f"Caught expected error: {e}")

print("\n--- Testing SendMessageRequest ---")
try:
    # Valid case 1: Empty list for messages
    # req1 = SendMessageRequest(
    #     content="Hello", messages=[], options=None, other_info="apple"
    # )
    # print(f"Created req1: {req1.__dict__}")

    # # Valid case 2: List with mixed types (not strictly list[dict[str, str]])
    # req2 = SendMessageRequest(
    #     content="World",
    #     messages=[{"a": "b"}, 123, "test"],
    #     options=ChatOptions(enabled=False),
    #     other_info="apply",
    # )
    # print(f"Created req2: {req2.__dict__}")

    # # Valid case 3: Options is ChatOptions instance
    # req3 = SendMessageRequest(
    #     content="Test",
    #     messages=[],
    #     options=ChatOptions(timeout=60, enabled=True),
    #     other_info="agree",
    # )
    # print(f"Created req3: {req3.__dict__}")
    # print(f"Req3 options timeout (default handled): {req3.options.timeout}")

    # Invalid case 1: messages is strictly list[dict[str, str]]
    req_invalid_msg = SendMessageRequest(
        content="Fail",
        messages=[{"k1": "v1"}, {"k2": "v2"}],
        options=None,
        other_info="apple",
    )
    print("This line should not be reached if validation fails")

    # Invalid case 2: content is wrong type
    # req_invalid_content = SendMessageRequest(
    #     content=123, messages=[], options=None, other_info="apple"
    # )
    # print("This line should not be reached if validation fails")

    # Invalid case 3: options is wrong type
    # req_invalid_options = SendMessageRequest(
    #     content="Fail", messages=[], options="not options", other_info="apple"
    # )
    # print("This line should not be reached if validation fails")

    # Invalid case 4: other_info fails custom validator
    # req_invalid_other = SendMessageRequest(
    #     content="Fail", messages=[], options=None, other_info="banana"
    # )
    # print("This line should not be reached if validation fails")

    # Invalid case 5: Missing required field (content)
    # req_missing = SendMessageRequest(messages=[], options=None, other_info="apple")
    # print("This line should not be reached if validation fails")

    # Invalid case 6: Setting invalid value
    # req1.content = 456  # Uncomment to test failure
    # print("This line should not be reached if validation fails")


except Exception as e:
    print(f"Caught expected error: {e}")
