
import inspect
from functools import partial
from graphql import Undefined

from .mountedtype import MountedType
from .structures import NonNull
from ..utils.module_loading import import_string


def _resolve_type(type_):
    """
    Resolves deferred types.  If type_ is a string, a callable or a partial, returns the actual type.
    """
    if isinstance(type_, str):
        return import_string(type_)
    if inspect.isfunction(type_) or isinstance(type_, partial):
        return type_()
    return type_


class InputField(MountedType):
    """
    Makes a field available on an InputObjectType.
    
    Example:
        from graphene import InputObjectType, String, InputField

        class Person(InputObjectType):
            first_name = String(required=True)
            last_name = InputField(String, description="Surname")
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
            assert deprecation_reason is None, f"InputField {name} is required, cannot deprecate it."
            type_ = NonNull(type_)
        self._type = type_
        self.deprecation_reason = deprecation_reason
        self.default_value = default_value
        self.description = description

    @property
    def type(self):
        return _resolve_type(self._type)
