
import inspect
from functools import partial

from .unmountedtype import UnmountedType
from ..utils.module_loading import import_string


def resolve_inner_type(inner):
    """Helper to resolve inner type if it is a string or a callable."""
    if isinstance(inner, str):
        return import_string(inner)
    if inspect.isfunction(inner) or isinstance(inner, partial):
        return inner()
    return inner


class Structure(UnmountedType):
    """
    A structure is a GraphQL type instance that
    wraps a main type with certain structure.
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
        return resolve_inner_type(self._of_type)

    def get_type(self):
        return self


class List(Structure):
    """
    List Modifier

    A list is a kind of type marker, a wrapping type which points to another
    type. Lists are often created within the context of defining the fields of
    an object type.

    List indicates that many values will be returned (or input) for this field.

    .. code:: python

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
    Non-Null Modifier

    A non-null is a kind of type marker, a wrapping type which points to another
    type. Non-null types enforce that their values are never null and can ensure
    an error is raised if this ever occurs during a request. It is useful for
    fields which you can make a strong guarantee on non-nullability, for example
    usually the id field of a database row will never be null.

    Note: the enforcement of non-nullability occurs within the executor.

    NonNull can also be indicated on all Mounted types with the keyword argument ``required``.
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
