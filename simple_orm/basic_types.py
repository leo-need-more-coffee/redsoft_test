"""
Базовые типы данных.
"""


class BaseType:
    field_type: str

    def __init__(self, primary_key=False, unique: bool = False, null: bool = True, default: int = None):
        self.primary_key = primary_key
        self.unique = unique
        self.null = null
        self.default = default


class IntegerField(BaseType):
    field_type = 'INTEGER'


class TextField(BaseType):
    field_type = 'TEXT'


class BlobField(BaseType):
    field_type = 'BLOB'


class RealField(BaseType):
    field_type = 'REAL'


class NumericField(BaseType):
    field_type = 'NUMERIC'


class JsonField(BaseType):
    field_type = 'JSON'


class ForeignKey(BaseType):
    field_type = 'FOREIGN_KEY'

    def __init__(self, object_class: type, foreign_field: str, unique: bool = False,
                 null: bool = True, default=None):
        self.primary_key = None
        self.object_class = object_class,
        self.foreign_field = foreign_field,
        self.unique = unique
        self.null = null
        self.default = default
