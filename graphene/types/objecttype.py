
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType, BaseTypeMeta
from .field import Field
from .interface import Interface
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

from dataclasses import make_dataclass, field

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type  # NOQA


def extract_object_fields(cls):
    collected = {}
    for base in reversed(cls.__mro__):
        items = []
        for attname, value in list(base.__dict__.items()):
            field_inst = None
            if isinstance(value, MountedType):
                field_inst = value
            elif isinstance(value, UnmountedType):
                field_inst = Field.mounted(value)
            if not field_inst:
                continue
            items.append((attname, field_inst))
        items = sorted(items, key=lambda f: f[1])
        collected.update(dict(items))
    return collected


class ObjectTypeOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]
    interfaces = ()  # type: Iterable[Type[Interface]]


class ObjectTypeMeta(BaseTypeMeta):
    def __new__(cls, name_, bases, namespace, **options):
        class InterObjectType:
            pass

        base_cls = super().__new__(
            cls, name_, (InterObjectType,) + bases, namespace, **options
        )
        if base_cls._meta:
            field_definitions = [
                (
                    key,
                    "typing.Any",
                    field(
                        default=field_value.default_value
                        if isinstance(field_value, Field)
                        else None
                    ),
                )
                for key, field_value in base_cls._meta.fields.items()
            ]
            dataclass_type = make_dataclass(name_, field_definitions, bases=())
            InterObjectType.__init__ = dataclass_type.__init__
            InterObjectType.__eq__ = dataclass_type.__eq__
            InterObjectType.__repr__ = dataclass_type.__repr__
        return base_cls


class ObjectType(BaseType, metaclass=ObjectTypeMeta):
    """
    Object Type Definition.

    Example:

        from graphene import ObjectType, String, Field

        class Person(ObjectType):
            first_name = String()
            last_name = Field(String)

            def resolve_last_name(parent, info):
                return "Smith"
    """

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=(),
        possible_types=(),
        default_resolver=None,
        _meta=None,
        **options,
    ):
        if not _meta:
            _meta = ObjectTypeOptions(cls)
        fields = {}

        for interface in interfaces:
            assert issubclass(
                interface, Interface
            ), f'All interfaces of {cls.__name__} must be a subclass of Interface. Received "{interface}".'
            fields.update(interface._meta.fields)
        fields.update(extract_object_fields(cls))
        assert not (possible_types and cls.is_type_of), (
            f"{cls.__name__}.Meta.possible_types will cause collision with {cls.__name__}.is_type_of. "
            "Please use one or the other."
        )

        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields
        if not _meta.interfaces:
            _meta.interfaces = interfaces
        _meta.possible_types = possible_types
        _meta.default_resolver = default_resolver

        super(ObjectType, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    is_type_of = None
