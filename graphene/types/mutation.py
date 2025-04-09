
from typing import TYPE_CHECKING

from ..utils.deprecated import warn_deprecation
from ..utils.get_unbound_function import get_unbound_function
from ..utils.props import props
from .field import Field
from .objecttype import ObjectType, ObjectTypeOptions
from .interface import Interface
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

if TYPE_CHECKING:
    from .argument import Argument  # NOQA
    from typing import Dict, Type, Callable, Iterable  # NOQA


def _resolve_type(type_):
    from ..utils.module_loading import import_string
    from functools import partial
    import inspect
    if isinstance(type_, str):
        return import_string(type_)
    if inspect.isfunction(type_) or isinstance(type_, partial):
        return type_()
    return type_


def _extract_fields_from_mro(cls, mount_method):
    """
    Iterates the MRO of cls and returns a dictionary of field names to mounted field instances.
    mount_method is used to mount values that are not already mounted.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            # Try to mount the value if it is one of our unmounted types.
            if isinstance(value, MountedType):
                field_obj = value
            elif isinstance(value, UnmountedType):
                field_obj = mount_method(value)
            else:
                continue
            if not field_obj:
                continue
            fields_with_names.append((attname, field_obj))
        # preserve order if needed (old code sorted by the field instance)
        for name, f in sorted(fields_with_names, key=lambda item: item[1]):
            fields[name] = f
    return fields


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
    
    Example:
        import graphene

        class CreatePerson(graphene.Mutation):
            class Arguments:
                name = graphene.String()

            ok = graphene.Boolean()
            person = graphene.Field(Person)

            def mutate(parent, info, name):
                person = Person(name=name)
                ok = True
                return CreatePerson(person=person, ok=ok)

        class Mutation(graphene.ObjectType):
            create_person = CreatePerson.Field()
            
    Meta options:
        output, resolver, arguments, interfaces (and others) are available
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
        from .interface import Interface  # for runtime checking
        if not _meta:
            _meta = MutationOptions(cls)

        # If an inner Output class exists, use it as output.
        output = output or getattr(cls, "Output", None)

        # First, add fields from all interfaces (only if an output is set on the mutation,
        # interfaces are merged with their fields)
        fields = {}
        for interface in interfaces:
            assert issubclass(
                interface, Interface
            ), f'All interfaces of {cls.__name__} must be a subclass of Interface. Received "{interface}".'
            fields.update(interface._meta.fields)

        # Get fields: if output not provided then use cls as output and extract fields from its MRO.
        if not output:
            fields = _extract_fields_from_mro(cls, Field.mounted)
            output = cls

        # Process arguments: try to grab from an inner "Arguments" or deprecated "Input"
        if not arguments:
            input_class = getattr(cls, "Arguments", None)
            if not input_class:
                input_class = getattr(cls, "Input", None)
                if input_class:
                    warn_deprecation(
                        f"Please use {cls.__name__}.Arguments instead of {cls.__name__}.Input."
                        " Input is now only used in ClientMutationID.\n"
                        "Read more: "
                        "https://github.com/graphql-python/graphene/blob/v2.0.0/UPGRADE-v2.0.md#mutation-input"
                    )
            arguments = props(input_class) if input_class else {}
        # Process resolver: if not provided, use the mutate method.
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
