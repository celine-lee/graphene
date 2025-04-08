
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType, BaseTypeMeta
from .field import Field
from .interface import Interface
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

from dataclasses import make_dataclass, field

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type


def _extract_fields(cls, mount_func):
    """Extract field definitions using the provided mount_func for unmounted types."""
    fields = {}
    for base in reversed(cls.__mro__):
        collected = []
        for attname, value in base.__dict__.items():
            if isinstance(value, MountedType):
                fval = value
            elif isinstance(value, UnmountedType):
                fval = mount_func(value)
            else:
                continue
            if not fval:
                continue
            collected.append((attname, fval))
        collected = sorted(collected, key=lambda f: f[1])
        fields.update(dict(collected))
    return fields


class ObjectTypeOptions(BaseOptions):
    fields = None  # type: Dict[str, Field]
    interfaces = ()  # type: Iterable[Type[Interface]]


class ObjectTypeMeta(BaseTypeMeta):
    def __new__(cls, name_, bases, namespace, **options):
        # Create an inner class to later augment it with dataclass features
        class InterObjectType:
            pass

        base_cls = super().__new__(cls, name_, (InterObjectType,) + bases, namespace, **options)
        if base_cls._meta:
            dataclass_fields = [
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
            datacls = make_dataclass(name_, dataclass_fields, bases=())
            InterObjectType.__init__ = datacls.__init__
            InterObjectType.__eq__ = datacls.__eq__
            InterObjectType.__repr__ = datacls.__repr__
        return base_cls


class ObjectType(BaseType, metaclass=ObjectTypeMeta):
    """
    Defines a GraphQL Object Type. All class attributes become fields on the type.
    
    Example:

        from graphene import ObjectType, String, Field

        class Person(ObjectType):
            class Meta:
                description = 'A human'

            first_name = String()
            last_name = Field(String)

            def resolve_last_name(parent, info):
                return parent.last_name

        class Query(ObjectType):
            person = Field(Person)
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

        # Merge fields from interfaces.
        for interface in interfaces:
            assert issubclass(interface, Interface), (
                f'All interfaces of {cls.__name__} must be a subclass of Interface. '
                f'Received "{interface}".'
            )
            fields.update(interface._meta.fields)

        # Extract fields from the class hierarchy.
        fields.update(_extract_fields(cls, Field.mounted))

        assert not (possible_types and cls.is_type_of), (
            f"{cls.__name__}.Meta.possible_types collides with {cls.__name__}.is_type_of. "
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
