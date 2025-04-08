
import inspect
from functools import partial
from graphql import Undefined

from .mountedtype import MountedType
from .structures import NonNull
from ..utils.module_loading import import_string


def _resolve_type_ref(type_ref):
    """Resolve a type reference that may be a string or callable."""
    if isinstance(type_ref, str):
        return import_string(type_ref)
    if inspect.isfunction(type_ref) or isinstance(type_ref, partial):
        return type_ref()
    return type_ref


class InputField(MountedType):
    """
    Makes a field available on an InputObjectType in the GraphQL schema.

    All class attributes of an InputObjectType are implicitly mounted as InputField.
    """

    def __init__(
        self,
        type_,
        name=None,
        default_value=Undefined,
        deprecation_reason=None,
        description=None,
        required=False,
        _creation_counter=None,
        **extra_args,
    ):
        super(InputField, self).__init__(_creation_counter=_creation_counter)
        self.name = name
        if required:
            assert deprecation_reason is None, f"InputField {name} is required and cannot be deprecated."
            type_ = NonNull(type_)
        self._type = type_
        self.deprecation_reason = deprecation_reason
        self.default_value = default_value
        self.description = description

    @property
    def type(self):
        return _resolve_type_ref(self._type)
