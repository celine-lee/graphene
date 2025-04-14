
from .mountedtype import MountedType
from .unmountedtype import UnmountedType

def collect_fields_from_bases(cls, mount_func):
    """
    Collect fields from the MRO of the given class using the specified mounting function.
    The mount_func is used to convert an UnmountedType into a MountedType (or an InputField)
    instance. Returns a dictionary mapping attribute names to the mounted fields.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field = value
            elif isinstance(value, UnmountedType):
                field = mount_func(value)
            else:
                continue
            if not field:
                continue
            fields_with_names.append((attname, field))
        fields_with_names = sorted(fields_with_names, key=lambda f: f[1])
        fields.update(dict(fields_with_names))
    return fields



from .mountedtype import MountedType
from .unmountedtype import UnmountedType

def collect_fields_from_bases(cls, mount_func):
    """
    Collect fields from the MRO of the given class using the specified mounting function.
    The mount_func is used to convert an UnmountedType into a MountedType (or an InputField)
    instance. Returns a dictionary mapping attribute names to the mounted fields.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field = value
            elif isinstance(value, UnmountedType):
                field = mount_func(value)
            else:
                continue
            if not field:
                continue
            fields_with_names.append((attname, field))
        fields_with_names = sorted(fields_with_names, key=lambda f: f[1])
        fields.update(dict(fields_with_names))
    return fields



from .mountedtype import MountedType
from .unmountedtype import UnmountedType

def collect_fields_from_bases(cls, mount_func):
    """
    Collect fields from the MRO of the given class using the specified mounting function.
    The mount_func is used to convert an UnmountedType into a MountedType (or an InputField)
    instance. Returns a dictionary mapping attribute names to the mounted fields.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field = value
            elif isinstance(value, UnmountedType):
                field = mount_func(value)
            else:
                continue
            if not field:
                continue
            fields_with_names.append((attname, field))
        fields_with_names = sorted(fields_with_names, key=lambda f: f[1])
        fields.update(dict(fields_with_names))
    return fields



from .mountedtype import MountedType
from .unmountedtype import UnmountedType

def collect_fields_from_bases(cls, mount_func):
    """
    Collect fields from the MRO of the given class using the specified mounting function.
    The mount_func is used to convert an UnmountedType into a MountedType (or an InputField)
    instance. Returns a dictionary mapping attribute names to the mounted fields.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field = value
            elif isinstance(value, UnmountedType):
                field = mount_func(value)
            else:
                continue
            if not field:
                continue
            fields_with_names.append((attname, field))
        fields_with_names = sorted(fields_with_names, key=lambda f: f[1])
        fields.update(dict(fields_with_names))
    return fields



from .mountedtype import MountedType
from .unmountedtype import UnmountedType

def collect_fields_from_bases(cls, mount_func):
    """
    Collect fields from the MRO of the given class using the specified mounting function.
    The mount_func is used to convert an UnmountedType into a MountedType (or an InputField)
    instance. Returns a dictionary mapping attribute names to the mounted fields.
    """
    fields = {}
    for base in reversed(cls.__mro__):
        fields_with_names = []
        for attname, value in list(base.__dict__.items()):
            if isinstance(value, MountedType):
                field = value
            elif isinstance(value, UnmountedType):
                field = mount_func(value)
            else:
                continue
            if not field:
                continue
            fields_with_names.append((attname, field))
        fields_with_names = sorted(fields_with_names, key=lambda f: f[1])
        fields.update(dict(fields_with_names))
    return fields
