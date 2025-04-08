
from typing import TYPE_CHECKING

from ..utils.deprecated import warn_deprecation
from ..utils.get_unbound_function import get_unbound_function
from ..utils.props import props
from .field import Field
from .objecttype import ObjectType, ObjectTypeOptions
from .interface import Interface
from .mountedtype import MountedType
from .unmountedtype import UnmountedType
from .utils import collect_fields_from_bases

if TYPE_CHECKING:
    from .argument import Argument  # NOQA
    from typing import Dict, Type, Callable, Iterable  # NOQA


class MutationOptions(ObjectTypeOptions):
    arguments = None  # type: Dict[str, Argument]
    output = None  # type: Type[ObjectType]
    resolver = None  # type: Callable
    interfaces = ()  # type: Iterable[Type[Interface]]


class Mutation(ObjectType):
    """
    Object Type Definition (mutation field)

    Mutation is a convenience type that helps us build a Field which takes Arguments and returns a
    mutation Output ObjectType.

    ...[rest of original docstring]...
    """

    @classmethod
    def __init_subclass_with_meta__(
        cls,
        interfaces=(),
        resolver=None,
        output=None,
        arguments=None,
        _meta=None,
        **options,
    ):
        if not _meta:
            _meta = MutationOptions(cls)
        output = output or getattr(cls, "Output", None)
        fields = {}

        for interface in interfaces:
            assert issubclass(
                interface, Interface
            ), f'All interfaces of {cls.__name__} must be a subclass of Interface. Received "{interface}".'
            fields.update(interface._meta.fields)
        if not output:
            fields.update(collect_fields_from_bases(cls, Field.mounted))
            output = cls
        if not arguments:
            input_class = getattr(cls, "Arguments", None)
            if not input_class:
                input_class = getattr(cls, "Input", None)
                if input_class:
                    warn_deprecation(
                        f"Please use {cls.__name__}.Arguments instead of {cls.__name__}.Input."
                        " Input is now only used in ClientMutationID.\n"
                        "Read more:"
                        " https://github.com/graphql-python/graphene/blob/v2.0.0/UPGRADE-v2.0.md#mutation-input"
                    )
            arguments = props(input_class) if input_class else {}
        if not resolver:
            mutate = getattr(cls, "mutate", None)
            assert mutate, "All mutations must define a mutate method in it"
            resolver = get_unbound_function(mutate)
        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields
        _meta.interfaces = interfaces
        _meta.output = output
        _meta.resolver = resolver
        _meta.arguments = arguments

        super(Mutation, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def Field(
        cls, name=None, description=None, deprecation_reason=None, required=False
    ):
        """Mount instance of mutation Field."""
        return Field(
            cls._meta.output,
            args=cls._meta.arguments,
            resolver=cls._meta.resolver,
            name=name,
            description=description or cls._meta.description,
            deprecation_reason=deprecation_reason,
            required=required,
        )
