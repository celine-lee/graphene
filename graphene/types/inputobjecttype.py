
from typing import TYPE_CHECKING

from .base import BaseOptions, BaseType
from .inputfield import InputField
from .unmountedtype import UnmountedType
from .mountedtype import MountedType

if TYPE_CHECKING:
    from typing import Dict, Callable


def _extract_input_fields(cls, mount_func):
    """Extract InputField definitions from class bases using the provided mount_func."""
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


# Default sentinel value.
_INPUT_OBJECT_TYPE_DEFAULT_VALUE = None


def set_input_object_type_default_value(default_value):
    """
    Change the default value returned by non-specified fields in an InputObjectType.
    """
    global _INPUT_OBJECT_TYPE_DEFAULT_VALUE
    _INPUT_OBJECT_TYPE_DEFAULT_VALUE = default_value


class InputObjectTypeOptions(BaseOptions):
    fields = None  # type: Dict[str, InputField]
    container = None  # type: InputObjectTypeContainer


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
    Defines an Input Object Type for structured input fields.

    All class attributes are implicitly mounted as InputField.
    """

    @classmethod
    def __init_subclass_with_meta__(cls, container=None, _meta=None, **options):
        if not _meta:
            _meta = InputObjectTypeOptions(cls)

        fields = _extract_input_fields(cls, InputField.mounted)
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
        """Called when the unmounted type is mounted."""
        return cls
