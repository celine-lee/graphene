
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .inputfield import InputField
from .unmountedtype import UnmountedType
from .mountedtype import MountedType

# For static type checking with type checker
if TYPE_CHECKING:
    from typing import Dict, Callable  # NOQA


def _collect_input_fields(cls, mount_fn):
    collected = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in base.__dict__.items():
            field_val = mount_fn(value)
            if field_val:
                fields_with_names.append((attname, field_val))
        fields_with_names.sort(key=lambda tup: tup[1])
        collected.update(dict(fields_with_names))
    return collected


# Currently in Graphene, we get a `None` whenever we access an (optional) field that was not set in an InputObjectType
# using the InputObjectType.<attribute> dot access syntax. This is ambiguous, because in this current (Graphene
# historical) arrangement, we cannot distinguish between a field not being set and a field being set to None.
# At the same time, we shouldn't break existing code that expects a `None` when accessing a field that was not set.
_INPUT_OBJECT_TYPE_DEFAULT_VALUE = None

def set_input_object_type_default_value(default_value):
    """
    Change the sentinel value returned by non-specified fields in an InputObjectType
    Useful to differentiate between a field not being set and a field being set to None by using a sentinel value
    (e.g. Undefined is a good sentinel value for this purpose)

    This function should be called at the beginning of the app or in some other place where it is guaranteed to
    be called before any InputObjectType is defined.
    """
    global _INPUT_OBJECT_TYPE_DEFAULT_VALUE
    _INPUT_OBJECT_TYPE_DEFAULT_VALUE = default_value


class InputObjectTypeContainer(dict, BaseType):  # type: ignore
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for key in self._meta.fields:
            setattr(self, key, self.get(key, _INPUT_OBJECT_TYPE_DEFAULT_VALUE))

    def __init_subclass__(cls, *args, **kwargs):
        pass


class InputObjectType(UnmountedType, BaseType):
    """
    Input Object Type Definition

    An input object defines a structured collection of fields which may be
    supplied to a field argument.

    Using ``graphene.NonNull`` will ensure that an input value must be provided by the query.

    All class attributes of ``graphene.InputObjectType`` are implicitly mounted as InputField
    using the below Meta class options.

    .. code:: python

        from graphene import InputObjectType, String, InputField

        class Person(InputObjectType):
            # implicitly mounted as Input Field
            first_name = String(required=True)
            # explicitly mounted as Input Field
            last_name = InputField(String, description="Surname")

    The fields on an input object type can themselves refer to input object types, but you can't
    mix input and output types in your schema.

    Meta class options (optional):
        name (str): the name of the GraphQL type (must be unique in schema). Defaults to class
            name.
        description (str): the description of the GraphQL type in the schema. Defaults to class
            docstring.
        container (class): A class reference for a value object that allows for
            attribute initialization and access. Default InputObjectTypeContainer.
        fields (Dict[str, graphene.InputField]): Dictionary of field name to InputField. Not
            recommended to use (prefer class attributes).
    """

    @classmethod
    def __init_subclass_with_meta__(cls, container=None, _meta=None, **options):
        if not _meta:
            _meta = InputObjectTypeOptions(cls)

        fields = _collect_input_fields(
            cls,
            lambda value: value if isinstance(value, MountedType)
            else InputField.mounted(value) if isinstance(value, UnmountedType)
            else None,
        )
        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields
        if container is None:
            container = type(cls.__name__, (InputObjectTypeContainer, cls), {})
        _meta.container = container
        super(InputObjectType, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def get_type(cls):
        """
        This function is called when the unmounted type (InputObjectType instance)
        is mounted (as a Field, InputField or Argument)
        """
        return cls
