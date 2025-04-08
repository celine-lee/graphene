
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .field import Field
from .mountedtype import MountedType
from .unmountedtype import UnmountedType
from .utils import collect_fields_from_bases

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type  # NOQA


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

    ...[rest of original docstring]...
    """

    @classmethod
    def __init_subclass_with_meta__(cls, _meta=None, interfaces=(), **options):
        if not _meta:
            _meta = InterfaceOptions(cls)

        fields = collect_fields_from_bases(cls, Field.mounted)

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
