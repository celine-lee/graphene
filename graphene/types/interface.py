
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .field import Field
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type


def _extract_fields(cls):
    """Extract fields from the class bases using Field.mounted for unmounted types."""
    fields = {}
    for base in reversed(cls.__mro__):
        collected = []
        for attname, value in base.__dict__.items():
            if isinstance(value, MountedType):
                field_val = value
            elif isinstance(value, UnmountedType):
                field_val = Field.mounted(value)
            else:
                continue
            if not field_val:
                continue
            collected.append((attname, field_val))
        # sort to preserve the field ordering
        collected = sorted(collected, key=lambda f: f[1])
        fields.update(dict(collected))
    return fields


class InterfaceOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]
    interfaces = ()  # type: Iterable[Type[Interface]]


class Interface(BaseType):
    """
    Interface Type Definition

    When a field can return one of a heterogeneous set of types, an Interface type
    is used to describe what types are possible, what fields are in common across
    all types, as well as a function to determine which type is actually used
    when the field is resolved.

    Example:

        from graphene import Interface, String

        class HasAddress(Interface):
            class Meta:
                description = "Address fields"

            address1 = String()
            address2 = String()

    If a field returns an Interface Type, the ambiguous type of the object can be determined using
    ``resolve_type`` on Interface and an ObjectType with ``Meta.possible_types`` or ``is_type_of``.

    Meta:
        name (str): The GraphQL type name.
        description (str): A useful description for the type.
        fields (Dict[str, Field]): A mapping of field names to Field instances.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, interfaces=(), **options):
        if not _meta:
            _meta = InterfaceOptions(cls)

        extracted_fields = _extract_fields(cls)
        if _meta.fields:
            _meta.fields.update(extracted_fields)
        else:
            _meta.fields = extracted_fields

        if not _meta.interfaces:
            _meta.interfaces = interfaces

        super(Interface, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def resolve_type(cls, instance, info):
        from .objecttype import ObjectType
        if isinstance(instance, ObjectType):
            return type(instance)

    def __init__(self, *args, **kwargs):
        raise Exception("An Interface cannot be initialized")
