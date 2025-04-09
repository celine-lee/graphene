
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .inputfield import InputField
from .unmountedtype import UnmountedType
from .mountedtype import MountedType

if TYPE_CHECKING:
    from typing import Dict, Callable  # NOQA


def extract_input_fields(cls):
    collected = {}
    for base in reversed(cls.__mro__):
        items = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field_inst = value
            elif isinstance(value, UnmountedType):
                field_inst = InputField.mounted(value)
            else:
                continue
            if not field_inst:
                continue
            items.append((attname, field_inst))
        items = sorted(items, key=lambda f: f[1])
        collected.update(dict(items))
    return collected


class InputObjectTypeOptions(BaseOptions):
    fields = None  # type: Dict[str, InputField]
    container = None  # type: InputObjectTypeContainer


_INPUT_OBJECT_TYPE_DEFAULT_VALUE = None


def set_input_object_type_default_value(default_value):
    """
    Change the sentinel value returned for non-specified fields in an InputObjectType.
    """
    global _INPUT_OBJECT_TYPE_DEFAULT_VALUE
    _INPUT_OBJECT_TYPE_DEFAULT_VALUE = default_value


class InputObjectTypeContainer(dict, BaseType):  # type: ignore
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for key in self._meta.fields:
            setattr(self, key, self.get(key, _INPUT_OBJECT_TYPE_DEFAULT_VALUE))

    def __init_subclass__(cls, *args, **kwargs):
        pass


class InputObjectType(UnmountedType, BaseType):
    """
    Input Object Type Definition.

    Example:

        from graphene import InputObjectType, String, InputField

        class Person(InputObjectType):
            first_name = String(required=True)
            last_name = InputField(String, description="Surname")
    """

    @classmethod
    def __init_subclass_with_meta__(cls, container=None, _meta=None, **options):
        if not _meta:
            _meta = InputObjectTypeOptions(cls)

        fields = extract_input_fields(cls)

        if _meta.fields:
            _meta.fields.update(fields)
        else:
            _meta.fields = fields
        if container is None:
            container = type(cls.__name__, (InputObjectTypeContainer, cls), {})
        _meta.container = container
        super(InputObjectType, cls).__init_subclass_with_meta__(_meta=_meta, **options)

    @classmethod
    def get_type(cls):
        return cls
