
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .field import Field
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

# For static type checking with type checker
if TYPE_CHECKING:
    from typing import Dict, Iterable, Type  # NOQA


def _collect_fields(cls, mount_fn):
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

    .. code:: python

        from graphene import Interface, String

        class HasAddress(Interface):
            class Meta:
                description = "Address fields"

            address1 = String()
            address2 = String()

    If a field returns an Interface Type, the ambiguous type of the object can be determined using
    ``resolve_type`` on Interface and an ObjectType with ``Meta.possible_types`` or ``is_type_of``.

    Meta:
        name (str): Name of the GraphQL type (must be unique in schema). Defaults to class
            name.
        description (str): Description of the GraphQL type in the schema. Defaults to class
            docstring.
        fields (Dict[str, graphene.Field]): Dictionary of field name to Field. Not recommended to
            use (prefer class attributes).
    """

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, interfaces=(), **options):
        if not _meta:
            _meta = InterfaceOptions(cls)

        # Abstract the field collection from the class bases.
        fields = _collect_fields(
            cls,
            lambda value: value if isinstance(value, MountedType)
            else Field.mounted(value) if isinstance(value, UnmountedType)
            else None,
        )

        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields

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
