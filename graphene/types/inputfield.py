
import inspect
from functools import partial
from graphql import Undefined

from .mountedtype import MountedType
from .structures import NonNull
from ..utils.module_loading import import_string


class InputField(MountedType):
    """
    Makes a field available on an ObjectType in the GraphQL schema as an Input Field.
    It can be implicitly mounted (via class attributes on an InputObjectType) or explicitly.
    
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
            assert (
                deprecation_reason is None
            ), f"InputField {name} is required, cannot deprecate it."
            type_ = NonNull(type_)
        self._type = type_
        self.deprecation_reason = deprecation_reason
        self.default_value = default_value
        self.description = description

    @property
    def type(self):
        if isinstance(self._type, str):
            return import_string(self._type)
        if inspect.isfunction(self._type) or isinstance(self._type, partial):
            return self._type()
        return self._type
