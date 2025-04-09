
import inspect
from functools import partial

from .unmountedtype import UnmountedType
from ..utils.module_loading import import_string


def resolve_structure(raw):
    """Helper to resolve the inner type of a structure."""
    if isinstance(raw, str):
        return import_string(raw)
    if inspect.isfunction(raw) or isinstance(raw, partial):
        return raw()
    return raw


class Structure(UnmountedType):
    """
    A structure wraps a main type with a modifier (e.g. List or NonNull).
    """

    def __init__(self, of_type, *args, **kwargs):
        super(Structure, self).__init__(*args, **kwargs)
        if not isinstance(of_type, Structure) and isinstance(of_type, UnmountedType):
            cls_name = type(self).__name__
            of_type_name = type(of_type).__name__
            raise Exception(
                f"{cls_name} could not have a mounted {of_type_name}()"
                f" as inner type. Try with {cls_name}({of_type_name})."
            )
        self._of_type = of_type

    @property
    def of_type(self):
        return resolve_structure(self._of_type)

    def get_type(self):
        return self


class List(Structure):
    """
    List Modifier: indicates that many values will be returned.
    
    Example:
        from graphene import List, String
        field_name = List(String, description="There will be many values")
    """

    def __str__(self):
        return f"[{self.of_type}]"

    def __eq__(self, other):
        return isinstance(other, List) and (
            self.of_type == other.of_type
            and self.args == other.args
            and self.kwargs == other.kwargs
        )


class NonNull(Structure):
    """
    Non-Null Modifier: enforces that values are never null.
    
    Example:
        from graphene import NonNull, String
        field_name = NonNull(String, description='This field will not be null')
    """

    def __init__(self, *args, **kwargs):
        super(NonNull, self).__init__(*args, **kwargs)
        assert not isinstance(
            self._of_type, NonNull
        ), f"Can only create NonNull of a Nullable GraphQLType but got: {self._of_type}."

    def __str__(self):
        return f"{self.of_type}!"

    def __eq__(self, other):
        return isinstance(other, NonNull) and (
            self.of_type == other.of_type
            and self.args == other.args
            and self.kwargs == other.kwargs
        )
