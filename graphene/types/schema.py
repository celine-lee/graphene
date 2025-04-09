
from enum import Enum as PyEnum
import inspect
from functools import partial

from graphql import (
    default_type_resolver,
    get_introspection_query,
    graphql,
    graphql_sync,
    introspection_types,
    parse,
    print_schema,
    subscribe,
    validate,
    ExecutionResult,
    GraphQLArgument,
    GraphQLBoolean,
    GraphQLError,
    GraphQLEnumValue,
    GraphQLField,
    GraphQLFloat,
    GraphQLID,
    GraphQLInputField,
    GraphQLInt,
    GraphQLList,
    GraphQLNonNull,
    GraphQLObjectType,
    GraphQLSchema,
    GraphQLString,
)

from ..utils.str_converters import to_camel_case
from ..utils.get_unbound_function import get_unbound_function
from .definitions import (
    GrapheneEnumType,
    GrapheneGraphQLType,
    GrapheneInputObjectType,
    GrapheneInterfaceType,
    GrapheneObjectType,
    GrapheneScalarType,
    GrapheneUnionType,
)
from .dynamic import Dynamic
from .enum import Enum
from .field import Field
from .inputobjecttype import InputObjectType
from .interface import Interface
from .objecttype import ObjectType
from .resolver import get_default_resolver
from .scalars import ID, Boolean, Float, Int, Scalar, String
from .structures import List, NonNull
from .union import Union
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

# A helper to resolve deferred types (string, callable, or partial)
def _resolve_type(type_):
    from functools import partial
    from ..utils.module_loading import import_string
    import inspect
    if isinstance(type_, str):
        return import_string(type_)
    if inspect.isfunction(type_) or isinstance(type_, partial):
        return type_()
    return type_

introspection_query = get_introspection_query()
IntrospectionSchema = introspection_types["__Schema"]


def assert_valid_root_type(type_):
    if type_ is None:
        return
    is_graphene_objecttype = inspect.isclass(type_) and issubclass(type_, ObjectType)
    is_graphql_objecttype = isinstance(type_, GraphQLObjectType)
    assert (
        is_graphene_objecttype or is_graphql_objecttype
    ), f"Type {type_} is not a valid ObjectType."


def is_graphene_type(type_):
    from .structures import List, NonNull
    from .objecttype import ObjectType
    from .inputobjecttype import InputObjectType
    from .scalars import Scalar
    from .interface import Interface
    from .union import Union
    from .enum import Enum
    if isinstance(type_, (List, NonNull)):
        return True
    if inspect.isclass(type_) and issubclass(
        type_, (ObjectType, InputObjectType, Scalar, Interface, Union, Enum)
    ):
        return True


def is_type_of_from_possible_types(possible_types, root, _info):
    return isinstance(root, possible_types)


def identity_resolve(root, info, **arguments):
    return root


class TypeMap(dict):
    def __init__(
        self,
        query=None,
        mutation=None,
        subscription=None,
        types=None,
        auto_camelcase=True,
    ):
        assert_valid_root_type(query)
        assert_valid_root_type(mutation)
        assert_valid_root_type(subscription)
        if types is None:
            types = []
        for type_ in types:
            assert is_graphene_type(type_)

        self.auto_camelcase = auto_camelcase

        create_graphql_type = self.add_type

        self.query = create_graphql_type(query) if query else None
        self.mutation = create_graphql_type(mutation) if mutation else None
        self.subscription = create_graphql_type(subscription) if subscription else None

        self.types = [create_graphql_type(graphene_type) for graphene_type in types]

    def add_type(self, graphene_type):
        if inspect.isfunction(graphene_type):
            graphene_type = graphene_type()
        if isinstance(graphene_type, List):
            return GraphQLList(self.add_type(graphene_type.of_type))
        if isinstance(graphene_type, NonNull):
            return GraphQLNonNull(self.add_type(graphene_type.of_type))
        try:
            name = graphene_type._meta.name
        except AttributeError:
            raise TypeError(f"Expected Graphene type, but received: {graphene_type}.")
        graphql_type = self.get(name)
        if graphql_type:
            return graphql_type
        if issubclass(graphene_type, ObjectType):
            graphql_type = self.create_objecttype(graphene_type)
        elif issubclass(graphene_type, InputObjectType):
            graphql_type = self.create_inputobjecttype(graphene_type)
        elif issubclass(graphene_type, Interface):
            graphql_type = self.create_interface(graphene_type)
        elif issubclass(graphene_type, Scalar):
            graphql_type = self.create_scalar(graphene_type)
        elif issubclass(graphene_type, Enum):
            graphql_type = self.create_enum(graphene_type)
        elif issubclass(graphene_type, Union):
            graphql_type = self.construct_union(graphene_type)
        else:
            raise TypeError(f"Expected Graphene type, but received: {graphene_type}.")
        self[name] = graphql_type
        return graphql_type

    @staticmethod
    def create_scalar(graphene_type):
        _scalars = {
            String: GraphQLString,
            Int: GraphQLInt,
            Float: GraphQLFloat,
            Boolean: GraphQLBoolean,
            ID: GraphQLID,
        }
        if graphene_type in _scalars:
            return _scalars[graphene_type]

        return GrapheneScalarType(
            graphene_type=graphene_type,
            name=graphene_type._meta.name,
            description=graphene_type._meta.description,
            serialize=getattr(graphene_type, "serialize", None),
            parse_value=getattr(graphene_type, "parse_value", None),
            parse_literal=getattr(graphene_type, "parse_literal", None),
        )

    @staticmethod
    def create_enum(graphene_type):
        values = {}
        for name, value in graphene_type._meta.enum.__members__.items():
            description = getattr(value, "description", None)
            if isinstance(description, PyEnum):
                description = None
            if not description and callable(graphene_type._meta.description):
                description = graphene_type._meta.description(value)

            deprecation_reason = getattr(value, "deprecation_reason", None)
            if isinstance(deprecation_reason, PyEnum):
                deprecation_reason = None
            if not deprecation_reason and callable(
                graphene_type._meta.deprecation_reason
            ):
                deprecation_reason = graphene_type._meta.deprecation_reason(value)

            values[name] = GraphQLEnumValue(
                value=value,
                description=description,
                deprecation_reason=deprecation_reason,
            )

        type_description = (
            graphene_type._meta.description(None)
            if callable(graphene_type._meta.description)
            else graphene_type._meta.description
        )

        return GrapheneEnumType(
            graphene_type=graphene_type,
            values=values,
            name=graphene_type._meta.name,
            description=type_description,
        )

    def create_objecttype(self, graphene_type):
        create_graphql_type = self.add_type

        def interfaces():
            lst = []
            for graphene_interface in graphene_type._meta.interfaces:
                interface = create_graphql_type(graphene_interface)
                assert interface.graphene_type == graphene_interface
                lst.append(interface)
            return lst

        if graphene_type._meta.possible_types:
            is_type_of = partial(
                is_type_of_from_possible_types, graphene_type._meta.possible_types
            )
        else:
            is_type_of = graphene_type.is_type_of

        return GrapheneObjectType(
            graphene_type=graphene_type,
            name=graphene_type._meta.name,
            description=graphene_type._meta.description,
            fields=partial(self.create_fields_for_type, graphene_type),
            is_type_of=is_type_of,
            interfaces=interfaces,
        )

    def create_interface(self, graphene_type):
        resolve_type = (
            partial(
                self.resolve_type, graphene_type.resolve_type, graphene_type._meta.name
            )
            if graphene_type.resolve_type
            else None
        )

        def interfaces():
            lst = []
            for graphene_interface in graphene_type._meta.interfaces:
                interface = self.add_type(graphene_interface)
                assert interface.graphene_type == graphene_interface
                lst.append(interface)
            return lst

        return GrapheneInterfaceType(
            graphene_type=graphene_type,
            name=graphene_type._meta.name,
            description=graphene_type._meta.description,
            fields=partial(self.create_fields_for_type, graphene_type),
            interfaces=interfaces,
            resolve_type=resolve_type,
        )

    def create_inputobjecttype(self, graphene_type):
        return GrapheneInputObjectType(
            graphene_type=graphene_type,
            name=graphene_type._meta.name,
            description=graphene_type._meta.description,
            out_type=graphene_type._meta.container,
            fields=partial(
                self.create_fields_for_type, graphene_type, is_input_type=True
            ),
        )

    def construct_union(self, graphene_type):
        create_graphql_type = self.add_type

        def types():
            lst = []
            for graphene_objecttype in graphene_type._meta.types:
                object_type = create_graphql_type(graphene_objecttype)
                assert object_type.graphene_type == graphene_objecttype
                lst.append(object_type)
            return lst

        resolve_type = (
            partial(
                self.resolve_type, graphene_type.resolve_type, graphene_type._meta.name
            )
            if graphene_type.resolve_type
            else None
        )

        return GrapheneUnionType(
            graphene_type=graphene_type,
            name=graphene_type._meta.name,
            description=graphene_type._meta.description,
            types=types,
            resolve_type=resolve_type,
        )

    def get_name(self, name):
        if self.auto_camelcase:
            return to_camel_case(name)
        return name

    def create_fields_for_type(self, graphene_type, is_input_type=False):
        create_graphql_type = self.add_type
        fields = {}
        for name, field in graphene_type._meta.fields.items():
            if isinstance(field, Dynamic):
                resolved_field = field.get_type(self)
                if isinstance(resolved_field, MountedType):
                    field = resolved_field
                elif isinstance(resolved_field, UnmountedType):
                    field = Field.mounted(resolved_field)
                else:
                    continue
                if not field:
                    continue
            field_type = create_graphql_type(field.type)
            if is_input_type:
                _field = GraphQLInputField(
                    field_type,
                    default_value=field.default_value,
                    out_name=name,
                    description=field.description,
                    deprecation_reason=field.deprecation_reason,
                )
            else:
                args = {}
                for arg_name, arg in field.args.items():
                    arg_type = create_graphql_type(arg.type)
                    processed_arg_name = arg.name or self.get_name(arg_name)
                    args[processed_arg_name] = GraphQLArgument(
                        arg_type,
                        out_name=arg_name,
                        description=arg.description,
                        default_value=arg.default_value,
                        deprecation_reason=arg.deprecation_reason,
                    )
                subscribe = field.wrap_subscribe(
                    self.get_function_for_type(
                        graphene_type, f"subscribe_{name}", name, field.default_value
                    )
                )
                if subscribe:
                    field_default_resolver = identity_resolve
                elif issubclass(graphene_type, ObjectType):
                    default_resolver = (
                        graphene_type._meta.default_resolver or get_default_resolver()
                    )
                    field_default_resolver = partial(
                        default_resolver, name, field.default_value
                    )
                else:
                    field_default_resolver = None

                resolve = field.wrap_resolve(
                    self.get_function_for_type(
                        graphene_type, f"resolve_{name}", name, field.default_value
                    )
                    or field_default_resolver
                )

                _field = GraphQLField(
                    field_type,
                    args=args,
                    resolve=resolve,
                    subscribe=subscribe,
                    deprecation_reason=field.deprecation_reason,
                    description=field.description,
                )
            field_name = field.name or self.get_name(name)
            fields[field_name] = _field
        return fields

    def get_function_for_type(self, graphene_type, func_name, name, default_value):
        """Gets a resolve or subscribe function for a given ObjectType"""
        from .objecttype import ObjectType
        if not issubclass(graphene_type, ObjectType):
            return
        resolver = getattr(graphene_type, func_name, None)
        if not resolver:
            interface_resolver = None
            for interface in graphene_type._meta.interfaces:
                if name not in interface._meta.fields:
                    continue
                interface_resolver = getattr(interface, func_name, None)
                if interface_resolver:
                    break
            resolver = interface_resolver

        if resolver:
            return get_unbound_function(resolver)

    def resolve_type(self, resolve_type_func, type_name, root, info, _type):
        type_ = resolve_type_func(root, info)
        from .objecttype import ObjectType
        if inspect.isclass(type_) and issubclass(type_, ObjectType):
            return type_._meta.name
        return_type = self[type_name]
        return default_type_resolver(root, info, return_type)


class Schema:
    """
    Schema Definition.

    A Graphene Schema can execute operations (query, mutation, subscription) against the defined types.
    """

    def __init__(
        self,
        query=None,
        mutation=None,
        subscription=None,
        types=None,
        directives=None,
        auto_camelcase=True,
    ):
        self.query = query
        self.mutation = mutation
        self.subscription = subscription
        type_map = TypeMap(
            query, mutation, subscription, types, auto_camelcase=auto_camelcase
        )
        self.graphql_schema = GraphQLSchema(
            type_map.query,
            type_map.mutation,
            type_map.subscription,
            type_map.types,
            directives,
        )

    def __str__(self):
        return print_schema(self.graphql_schema)

    def __getattr__(self, type_name):
        _type = self.graphql_schema.get_type(type_name)
        if _type is None:
            raise AttributeError(f'Type "{type_name}" not found in the Schema')
        from .definitions import GrapheneGraphQLType
        if isinstance(_type, GrapheneGraphQLType):
            return _type.graphene_type
        return _type

    def lazy(self, _type):
        return lambda: self.get_type(_type)

    def execute(self, *args, **kwargs):
        kwargs = normalize_execute_kwargs(kwargs)
        return graphql_sync(self.graphql_schema, *args, **kwargs)

    async def execute_async(self, *args, **kwargs):
        kwargs = normalize_execute_kwargs(kwargs)
        return await graphql(self.graphql_schema, *args, **kwargs)

    async def subscribe(self, query, *args, **kwargs):
        try:
            document = parse(query)
        except GraphQLError as error:
            return ExecutionResult(data=None, errors=[error])
        validation_errors = validate(self.graphql_schema, document)
        if validation_errors:
            return ExecutionResult(data=None, errors=validation_errors)
        kwargs = normalize_execute_kwargs(kwargs)
        return await subscribe(self.graphql_schema, document, *args, **kwargs)

    def introspect(self):
        introspection = self.execute(introspection_query)
        if introspection.errors:
            raise introspection.errors[0]
        return introspection.data


def normalize_execute_kwargs(kwargs):
    if "root" in kwargs and "root_value" not in kwargs:
        kwargs["root_value"] = kwargs.pop("root")
    if "context" in kwargs and "context_value" not in kwargs:
        kwargs["context_value"] = kwargs.pop("context")
    if "variables" in kwargs and "variable_values" not in kwargs:
        kwargs["variable_values"] = kwargs.pop("variables")
    if "operation" in kwargs and "operation_name" not in kwargs:
        kwargs["operation_name"] = kwargs.pop("operation")
    return kwargs
