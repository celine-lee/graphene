
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .field import Field
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type  # NOQA


def _extract_fields_from_mro(cls, mount_method):
    """
    Helper to extract and merge mounted fields from a class and its bases.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field_obj = value
            elif isinstance(value, UnmountedType):
                field_obj = Field.mounted(value)
            else:
                continue
            if not field_obj:
                continue
            fields_with_names.append((attname, field_obj))
        for name, f in sorted(fields_with_names, key=lambda item: item[1]):
            fields[name] = f
    return fields


class InterfaceOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]
    interfaces = ()  # type: Iterable[Type[Interface]]


class Interface(BaseType):
    """
    Interface Type Definition

    Describes common fields for heterogeneous types.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, interfaces=(), **options):
        if not _meta:
            _meta = InterfaceOptions(cls)

        fields = _extract_fields_from_mro(cls, Field.mounted)
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
