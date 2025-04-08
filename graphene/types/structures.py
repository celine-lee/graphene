
import inspect
from functools import partial

from .unmountedtype import UnmountedType
from ..utils.module_loading import import_string


def _resolve_type_ref(type_ref):
    """Resolve a type reference that may be a string or a callable."""
    if isinstance(type_ref, str):
        return import_string(type_ref)
    if inspect.isfunction(type_ref) or isinstance(type_ref, partial):
        return type_ref()
    return type_ref


class Structure(UnmountedType):
    """
    A structure is a GraphQL type instance that wraps a main type with a particular structure.
    """

    def __init__(self, of_type, *args, **kwargs):
        super(Structure, self).__init__(*args, **kwargs)
        if not isinstance(of_type, Structure) and isinstance(of_type, UnmountedType):
            cls_name = type(self).__name__
            of_type_name = type(of_type).__name__
            raise Exception(
                f"{cls_name} could not have a mounted {of_type_name}() as inner type. "
                f"Try with {cls_name}({of_type_name})."
            )
        self._of_type = of_type

    @property
    def of_type(self):
        typ = self._of_type
        if isinstance(typ, str):
            return import_string(typ)
        if inspect.isfunction(typ) or isinstance(typ, partial):
            return typ()
        return typ

    def get_type(self):
        """Called when the unmounted type is mounted (as a Field, InputField or Argument)."""
        return self


class List(Structure):
    """
    List Modifier

    Indicates that many values will be returned (or input) for a field.
    """

    def __str__(self):
        return f"[{self.of_type}]"

    def __eq__(self, other):
        return isinstance(other, List) and (
            self.of_type == other.of_type and self.args == other.args and self.kwargs == other.kwargs
        )


class NonNull(Structure):
    """
    Non-Null Modifier

    Indicates that a field will never be null. Using NonNull ensures that a validation error
    is raised if a null value is encountered.
    """

    def __init__(self, *args, **kwargs):
        super(NonNull, self).__init__(*args, **kwargs)
        assert not isinstance(
            self._of_type, NonNull
        ), f"NonNull can only wrap a nullable type but got: {self._of_type}."

    def __str__(self):
        return f"{self.of_type}!"

    def __eq__(self, other):
        return isinstance(other, NonNull) and (
            self.of_type == other.of_type and self.args == other.args and self.kwargs == other.kwargs
        )
