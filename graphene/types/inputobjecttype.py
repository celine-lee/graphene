
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
    Change the default value for non-specified fields in InputObjectType.
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


def _extract_fields_from_mro(cls, mount_method):
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field_obj = value
            elif isinstance(value, UnmountedType):
                field_obj = InputField.mounted(value)
            else:
                continue
            if not field_obj:
                continue
            fields_with_names.append((attname, field_obj))
        for name, f in sorted(fields_with_names, key=lambda item: item[1]):
            fields[name] = f
    return fields


class InputObjectType(UnmountedType, BaseType):
    """
    Input Object Type Definition.

    Defines a collection of InputFields.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, container=None, _meta=None, **options):
        if not _meta:
            _meta = InputObjectTypeOptions(cls)

        fields = _extract_fields_from_mro(cls, InputField.mounted)
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
