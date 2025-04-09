
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .field import Field
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type  # NOQA


class InterfaceOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]
    interfaces = ()  # type: Iterable[Type[Interface]]


def _extract_fields(cls):
    """
    Extract Field instances from the class definition. Converts an UnmountedType
    into a mounted Field using Field.mounted.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field_inst = value
            elif isinstance(value, UnmountedType):
                field_inst = Field.mounted(value)
            else:
                continue
            if not field_inst:
                continue
            fields_with_names.append((attname, field_inst))
        fields_with_names = sorted(fields_with_names, key=lambda f: f[1])
        extracted = dict(fields_with_names)
        fields.update(extracted)
    return fields


class Interface(BaseType):
    """
    Interface Type Definition
    
    When a field can return one of a heterogeneous set of types, an Interface type
    is used to describe the common fields and a function to determine the actual type used
    when resolving.
    
    Example:
    
        from graphene import Interface, String
    
        class HasAddress(Interface):
            class Meta:
                description = "Address fields"
    
            address1 = String()
            address2 = String()
    
    Note: An Interface cannot be initialized.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, interfaces=(), **options):
        if not _meta:
            _meta = InterfaceOptions(cls)
        fields = _extract_fields(cls)
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
