
import inspect
from functools import partial

from .unmountedtype import UnmountedType
from ..utils.module_loading import import_string


def _resolve_type(type_):
    """
    Resolve a deferred type reference.
    """
    from functools import partial
    if isinstance(type_, str):
        return import_string(type_)
    if inspect.isfunction(type_) or isinstance(type_, partial):
        return type_()
    return type_


class Structure(UnmountedType):
    """
    A structure wraps a main type with additional structure.
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
        return _resolve_type(self._of_type)

    def get_type(self):
        return self


class List(Structure):
    """
    List Modifier - indicates many values.
    """

    def __str__(self):
        return f"[{self.of_type}]"

    def __eq__(self, other):
        return (
            isinstance(other, List)
            and self.of_type == other.of_type
            and self.args == other.args
            and self.kwargs == other.kwargs
        )


class NonNull(Structure):
    """
    Non-Null Modifier - indicates the field cannot be null.
    """

    def __init__(self, *args, **kwargs):
        super(NonNull, self).__init__(*args, **kwargs)
        assert not isinstance(
            self._of_type, NonNull
        ), f"Can only create NonNull of a Nullable GraphQLType but got: {self._of_type}."

    def __str__(self):
        return f"{self.of_type}!"

    def __eq__(self, other):
        return (
            isinstance(other, NonNull)
            and self.of_type == other.of_type
            and self.args == other.args
            and self.kwargs == other.kwargs
        )
