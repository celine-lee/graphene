
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .inputfield import InputField
from .unmountedtype import UnmountedType
from .mountedtype import MountedType

if TYPE_CHECKING:
    from typing import Dict, Callable  # NOQA


class InputObjectTypeOptions(BaseOptions):
    fields = None  # type: Dict[str, InputField]
    container = None  # type: InputObjectTypeContainer


_INPUT_OBJECT_TYPE_DEFAULT_VALUE = None


def set_input_object_type_default_value(default_value):
    """
    Change the sentinel value returned by non-specified fields in an InputObjectType.
    """
    global _INPUT_OBJECT_TYPE_DEFAULT_VALUE
    _INPUT_OBJECT_TYPE_DEFAULT_VALUE = default_value


class InputObjectTypeContainer(dict, BaseType):
    class Meta:
        abstract = True

    def __init__(self, *args, **kwargs):
        dict.__init__(self, *args, **kwargs)
        for key in self._meta.fields:
            setattr(self, key, self.get(key, _INPUT_OBJECT_TYPE_DEFAULT_VALUE))

    def __init_subclass__(cls, *args, **kwargs):
        pass


def _extract_input_fields(cls):
    """
    Extract InputField instances from a class. For MountedType use as is and for
    UnmountedType use InputField.mounted.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field_inst = value
            elif isinstance(value, UnmountedType):
                field_inst = InputField.mounted(value)
            else:
                continue
            if not field_inst:
                continue
            fields_with_names.append((attname, field_inst))
        fields_with_names = sorted(fields_with_names, key=lambda f: f[1])
        extracted = dict(fields_with_names)
        fields.update(extracted)
    return fields


class InputObjectType(UnmountedType, BaseType):
    """
    Input Object Type Definition.
    
    Collects its fields from class attributes.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, container=None, _meta=None, **options):
        if not _meta:
            _meta = InputObjectTypeOptions(cls)
        fields = _extract_input_fields(cls)
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
