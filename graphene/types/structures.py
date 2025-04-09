
import inspect
from functools import partial

from .unmountedtype import UnmountedType
from ..utils.module_loading import import_string


class Structure(UnmountedType):
    """
    A structure is a GraphQL type instance that wraps a main type with a modifier.
    """

    def __init__(self, of_type, *args, **kwargs):
        super(Structure, self).__init__(*args, **kwargs)
        if not isinstance(of_type, Structure) and isinstance(of_type, UnmountedType):
            cls_name = type(self).__name__
            of_type_name = type(of_type).__name__
            raise Exception(
                f"{cls_name} cannot have a mounted {of_type_name}() as inner type. Try with {cls_name}({of_type_name})."
            )
        self._of_type = of_type

    @property
    def of_type(self):
        if isinstance(self._of_type, str):
            return import_string(self._of_type)
        if inspect.isfunction(self._of_type) or isinstance(self._of_type, partial):
            return self._of_type()
        return self._of_type

    def get_type(self):
        return self


class List(Structure):
    """
    List Modifier.
    
    Indicates many values will be returned (or input) for this field.
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
    Non-Null Modifier.
    
    Indicates that the wrapped type cannot be null.
    """

    def __init__(self, *args, **kwargs):
        super(NonNull, self).__init__(*args, **kwargs)
        assert not isinstance(
            self._of_type, NonNull
        ), f"Cannot create NonNull of a NonNull type: {self._of_type}."

    def __str__(self):
        return f"{self.of_type}!"

    def __eq__(self, other):
        return (
            isinstance(other, NonNull)
            and self.of_type == other.of_type
            and self.args == other.args
            and self.kwargs == other.kwargs
        )
