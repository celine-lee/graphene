
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType, BaseTypeMeta
from .field import Field
from .interface import Interface
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

from dataclasses import make_dataclass, field

if TYPE_CHECKING:
    from typing import Dict, Iterable, Type  # NOQA


def _extract_fields_from_mro(cls, mount_method):
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
            fields = [
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
            dataclass_def = make_dataclass(name_, fields, bases=())
            InterObjectType.__init__ = dataclass_def.__init__
            InterObjectType.__eq__ = dataclass_def.__eq__
            InterObjectType.__repr__ = dataclass_def.__repr__
        return base_cls


class ObjectType(BaseType, metaclass=ObjectTypeMeta):
    """
    Object Type Definition

    Almost all GraphQL types are object types. Fields are auto-mounted from class attributes.
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
        fields.update(_extract_fields_from_mro(cls, Field.mounted))
        assert not (possible_types and cls.is_type_of), (
            f"{cls.__name__}.Meta.possible_types will cause type collision with {cls.__name__}.is_type_of. "
            "Please use one or other."
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
