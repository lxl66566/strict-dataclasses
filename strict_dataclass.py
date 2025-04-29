import collections.abc
from dataclasses import dataclass
from functools import cache
from types import GenericAlias
from typing import Any, Union, dataclass_transform, get_args, get_origin

# def validate_type(value, expected_type):
#     if value is None:
#         if type(None) in get_args(expected_type) or expected_type is type(None):
#             return True
#         return False

#     origin = get_origin(expected_type)
#     args = get_args(expected_type)

#     if origin is Union:
#         return any(validate_type(value, arg) for arg in args)

#     if origin is dict or origin is collections.abc.Mapping:
#         if not isinstance(value, dict):
#             return False
#         if not args:
#             return True
#         key_type, val_type = args
#         return all(
#             validate_type(k, key_type) and validate_type(v, val_type)
#             for k, v in value.items()
#         )

#     elif origin is list or origin is collections.abc.Sequence:
#         if not isinstance(value, list):
#             return False
#         if not args:
#             return True
#         item_type = args[0]
#         return all(validate_type(item, item_type) for item in value)

#     elif origin is set or origin is collections.abc.Set:
#         if not isinstance(value, set):
#             return False
#         if not args:
#             return True
#         item_type = args[0]
#         return all(validate_type(item, item_type) for item in value)

#     elif origin is tuple:
#         if not isinstance(value, tuple):
#             return False
#         if not args:
#             return True
#         if len(args) == 2 and args[1] is ...:
#             return all(validate_type(item, args[0]) for item in value)
#         elif len(args) == len(value):
#             return all(validate_type(v, t) for v, t in zip(value, args))
#         return False

#     return isinstance(value, origin or expected_type)


# region opt


# Define NoneType for explicit checks
NoneType = type(None)

# Cache for compiled validation functions
_validator_cache = {}


@cache
def _compile_validator(expected_type):
    """
    Compiles a type hint into a validation function.
    Caches the result.
    """
    if expected_type is Any:
        validator = lambda value: True
    elif expected_type is NoneType:
        validator = lambda value: value is None

    else:
        origin = get_origin(expected_type)
        args = get_args(expected_type)

        # Handle Union (includes Optional)
        if origin is Union:
            # Filter out NoneType if present, handle None separately
            non_none_args = tuple(arg for arg in args if arg is not NoneType)
            arg_validators = [_compile_validator(arg) for arg in non_none_args]

            if NoneType in args:
                # If None is allowed, check if value is None OR matches any other type
                validator = lambda value: value is None or any(
                    v(value) for v in arg_validators
                )
            else:
                # If None is not allowed, check if value is not None AND matches any type
                validator = lambda value: value is not None and any(
                    v(value) for v in arg_validators
                )

        # Handle Collections (Dict, List, Set, Tuple)
        elif origin in (dict, collections.abc.Mapping):
            if not args:  # Dict without args (like Dict, or Dict[Any, Any])
                validator = lambda value: isinstance(value, dict)
            else:  # Dict with args (like Dict[K, V])
                key_validator = _compile_validator(args[0])
                val_validator = _compile_validator(args[1])
                validator = lambda value: isinstance(value, dict) and all(
                    key_validator(k) and val_validator(v) for k, v in value.items()
                )

        elif (
            origin in (list, collections.abc.Sequence) and origin is not tuple
        ):  # Exclude tuple here
            if not args:  # List without args (like List, or List[Any])
                validator = lambda value: isinstance(value, list)
            else:  # List with args (like List[T])
                item_validator = _compile_validator(args[0])
                validator = lambda value: isinstance(value, list) and all(
                    item_validator(item) for item in value
                )

        elif origin in (set, collections.abc.Set):
            if not args:  # Set without args (like Set, or Set[Any])
                validator = lambda value: isinstance(value, set)
            else:  # Set with args (like Set[T])
                item_validator = _compile_validator(args[0])
                validator = lambda value: isinstance(value, set) and all(
                    item_validator(item) for item in value
                )

        elif origin is tuple:
            if not args:  # Tuple (equivalent to Tuple[Any, ...])
                validator = lambda value: isinstance(value, tuple)
            elif len(args) == 2 and args[1] is Ellipsis:  # Tuple[T, ...]
                item_validator = _compile_validator(args[0])
                validator = lambda value: isinstance(value, tuple) and all(
                    item_validator(item) for item in value
                )
            else:  # Fixed-length tuple Tuple[T1, T2, ...]
                element_validators = [_compile_validator(arg) for arg in args]
                validator = (
                    lambda value: isinstance(value, tuple)
                    and len(value) == len(args)
                    and all(v(val) for val, v in zip(value, element_validators))
                )

        # Handle basic types and non-generic type hints whose origin is the type itself
        # This covers int, str, bool, classes, and generic types like List, Dict themselves
        # when used without args (e.g., type(List) is not list, but get_origin(List) is list)
        # Also covers types like typing.Pattern, typing.IO etc.
        # The original code's final line `isinstance(value, origin or expected_type)`
        # effectively does: if origin is not None: check isinstance(value, origin)
        # else: check isinstance(value, expected_type)
        # This seems correct for the fallback.
        else:
            type_to_check = origin if origin is not None else expected_type
            try:
                # Check if type_to_check is a valid type for isinstance
                # Avoids TypeError for things like Union, which should be caught by origin check anyway
                if not isinstance(
                    type_to_check, (type, GenericAlias)
                ):  # _GenericAlias covers types like typing.Pattern
                    # If it's not a standard type or generic alias, maybe it's a complex typing object
                    # that isinstance can't handle directly. Fallback to False or a more specific check if needed.
                    # For now, let's assume types reachable here are intended for isinstance.
                    # If it fails, the except block will handle it.
                    pass  # Proceed to try isinstance

                validator = lambda value: isinstance(value, type_to_check)

            except TypeError:
                # This can happen for some complex typing objects that aren't directly usable with isinstance
                # If we can't check it with isinstance, it doesn't match this basic type case.
                # The original code would likely also fail or return False here.
                # Returning False is a safe default if the type structure is unexpected.
                # print(f"Warning: Cannot create isinstance validator for type {expected_type}. Falling back to False.") # Optional warning
                validator = lambda value: False  # Cannot validate this type structure

    return validator


def validate_type_optimized(value, expected_type):
    """
    Validates if a value conforms to a type hint using a cached validator.
    """
    # Handle None value first as a common case, avoids cache lookup/compilation
    # This mirrors the original code's first check and is slightly faster
    # than compiling a validator for Optional[X] every time value is None.
    if value is None:
        origin = get_origin(expected_type)
        args = get_args(expected_type)
        # Check if expected_type is NoneType or if NoneType is in the Union args
        if expected_type is NoneType or (origin is Union and NoneType in args):
            return True
        return False

    # For non-None values, get or compile the validator from the cache
    if expected_type not in _validator_cache:
        _validator_cache[expected_type] = _compile_validator(expected_type)

    validator = _validator_cache[expected_type]
    return validator(value)


validate_type = validate_type_optimized

# endregion opt


def validate_field_type(class_or_instance, name: str):
    value = getattr(class_or_instance, name)
    field_type = getattr(class_or_instance, "__dataclass_fields__").get(name).type

    if not validate_type(value, field_type):
        raise TypeError(
            f"Field '{name}' must be of type {field_type}, got {type(value)} instead",
        )


@dataclass_transform()
def strict_dataclass(cls=None, **kwargs):
    cls = dataclass(cls, **kwargs)
    original_setattr = cls.__setattr__

    def __setattr__(self, name, value):
        original_setattr(self, name, value)  # type: ignore
        if name in getattr(self, "__dataclass_fields__", {}):
            validate_field_type(self, name)

    cls.__setattr__ = __setattr__  # type: ignore
    return cls
