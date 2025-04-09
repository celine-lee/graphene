
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .field import Field
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type  # NOQA


def extract_fields(cls):
    collected = {}
    for base in reversed(cls.__mro__):
        items = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field_inst = value
            elif isinstance(value, UnmountedType):
                field_inst = Field.mounted(value)
            else:
                continue
            if not field_inst:
                continue
            items.append((attname, field_inst))
        items = sorted(items, key=lambda f: f[1])
        collected.update(dict(items))
    return collected


class InterfaceOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]
    interfaces = ()  # type: Iterable[Type[Interface]]


class Interface(BaseType):
    """
    Interface Type Definition

    When a field can return one of a heterogeneous set of types, an Interface type
    is used to describe what types are possible, what fields are in common, as well as a
    resolve_type function.
    
    Example:

        from graphene import Interface, String

        class HasAddress(Interface):
            class Meta:
                description = "Address fields"

            address1 = String()
            address2 = String()

    An Interface cannot be instantiated.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, interfaces=(), **options):
        if not _meta:
            _meta = InterfaceOptions(cls)

        fields = extract_fields(cls)

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
