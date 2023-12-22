import json
import sqlite3
import asyncio
import copy
import sys
from .basic_types import BaseType, IntegerField, TextField, BlobField, RealField, NumericField, JsonField, ForeignKey

db_name = 'db.sqlite3'


BASIC_TYPES = [IntegerField, TextField, BlobField, RealField, NumericField]
EXTERN_TYPES = {}


def simple_orm(class_: type):
    EXTERN_TYPES[class_.__name__] = class_
    class_.objects.__createTable__()

    return class_


class ListOfObjects:
    def __init__(self, objects):
        self.objects = objects

    def __len__(self):
        return len(self.objects)

    def __iter__(self):
        for item in self.objects:
            yield item

    def filter(self, **kwargs):
        filtered_objects = []
        for obj in self.objects:
            if all(getattr(obj, attr, None) == value for attr, value in kwargs.items()):
                filtered_objects.append(obj)
        return ListOfObjects(filtered_objects)

    def delete(self):
        for obj in self.objects:
            obj.delete()

    def json(self):
        object_dicts = [obj.json() for obj in self.objects]
        return object_dicts


class Object:
    def __init__(self, object_type, primary_key):
        self.object_type = object_type
        self.primary_key = primary_key

    def add(self, obj):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        d = copy.copy(obj.__dict__)

        object_type_name = self.object_type.__name__
        for key, value in vars(self.object_type).items():
            if not key.startswith("__") and not callable(value):
                if key not in d:
                    d[key] = getattr(obj, key).default
                if type(value) in BASIC_TYPES:
                    continue
                if type(value) == JsonField:
                    d[key] = json.dumps(d[key])
                if type(value) == ForeignKey:
                    if d[key] is not None:
                        d[key] = json.dumps({'type': value.object_class[0].__name__, 'key': value.foreign_field[0], 'value': getattr(d[key], value.foreign_field[0])})

        insert_sql = f'INSERT INTO {object_type_name} ({", ".join(d.keys())}) VALUES ({", ".join(["?"] * len(d))});'

        values = tuple(d.values())
        cursor.execute(insert_sql, values)
        conn.commit()
        conn.close()
        return obj

    def save(self, obj):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        d = copy.copy(obj.__dict__)

        object_type_name = self.object_type.__name__
        for key, value in vars(self.object_type).items():
            if not key.startswith("__") and not callable(value):
                if type(value) in BASIC_TYPES:
                    continue
                if type(value) == JsonField:
                    d[key] = json.dumps(d[key])
                if type(value) == ForeignKey:
                    if not d[key] is None and d[key] != 'None':
                        d[key] = json.dumps({'type': value.object_class[0].__name__, 'key': value.foreign_field[0], 'value': getattr(d[key], value.foreign_field[0])})
        values = tuple(d.values())
        changing_values = [f"{p}='{q}'" for p, q in zip(obj.__dict__.keys(), values)]
        upsert_sql = f'UPDATE {object_type_name} SET {", ".join(changing_values)} WHERE {self.primary_key}={obj.__getattribute__(self.primary_key)};'

        cursor.execute(upsert_sql)
        conn.commit()
        conn.close()
        return obj

    def get(self, **kwargs):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        object_type_name = self.object_type.__name__

        attr_value_pairs = [(attr, value) for attr, value in kwargs.items()]

        where_clauses = [f'{attr} = ?' for attr, _ in attr_value_pairs]
        where_clause = ' AND '.join(where_clauses)
        select_by_attrs_sql = f'SELECT * FROM {object_type_name} WHERE {where_clause};'

        values = tuple(value for _, value in attr_value_pairs)

        cursor.execute(select_by_attrs_sql, values)
        row = cursor.fetchone()
        conn.close()

        if row:
            obj = self.object_type()
            for i, value in enumerate(row):
                if type(getattr(obj, cursor.description[i][0])) == JsonField:
                    if value is not None:
                        value = json.loads(value)
                    setattr(obj, cursor.description[i][0], value)
                elif type(getattr(obj, cursor.description[i][0])) == ForeignKey:
                    if value is not None and value != 'None':
                        value = json.loads(value)
                        setattr(obj, cursor.description[i][0], EXTERN_TYPES[value['type']].objects.get(**{value['key']: value['value']}))
                    else:
                        setattr(obj, cursor.description[i][0], value)

                else:
                    setattr(obj, cursor.description[i][0], value)

            return obj
        else:
            return None

    def delete_object(self, obj):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        object_type_name = self.object_type.__name__

        delete_by_attrs_sql = f'DELETE FROM {object_type_name} WHERE {self.primary_key}={obj.__getattribute__(self.primary_key)};'
        cursor.execute(delete_by_attrs_sql)
        conn.commit()
        conn.close()

    def delete(self, **kwargs):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        object_type_name = self.object_type.__name__

        attr_value_pairs = [(attr, value) for attr, value in kwargs.items()]

        where_clauses = [f'{attr} = ?' for attr, _ in attr_value_pairs]
        where_clause = ' AND '.join(where_clauses)
        delete_by_attrs_sql = f'DELETE FROM {object_type_name} WHERE {where_clause};'
        values = tuple(value for _, value in attr_value_pairs)

        cursor.execute(delete_by_attrs_sql, values)
        conn.commit()
        conn.close()

    def filter(self, **kwargs):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        d = kwargs

        if 'sort_by' in d:
            sort_order = d['sort_by'][0] == '+'
            sort_by = d['sort_by'][1:]
            print(sort_order, sort_by)
            del d['sort_by']
        else:
            sort_order = None
            sort_by = None

        if 'limit' in d:
            limit = d['limit']
            del d['limit']
        else:
            limit = None

        if 'page' in d:
            page = d['page']
            del d['page']
        else:
            page = None

        if 'from' in d:
            from_ = d['from']
            del d['from']
        else:
            from_ = None

        if 'to' in d:
            to = d['to']
            del d['to']
        else:
            to = None

        if 'fromtocolumn' in d:
            fromtocolumn = d['fromtocolumn']
            del d['fromtocolumn']
        else:
            fromtocolumn = None

        attributes = {}
        for key, value in d.items():
            if not key.startswith("__") and not callable(value):
                if value == 'null':
                    attributes[key] = None
                    continue

                if type(getattr(self.object_type, key)) == ForeignKey:
                    attributes[key] = json.dumps({'type': type(value).__name__, 'key': getattr(self.object_type, key).foreign_field[0],
                                       'value': getattr(value, getattr(self.object_type, key).foreign_field[0])})
                    continue

                attributes[key] = value

        object_type_name = self.object_type.__name__

        attr_value_pairs = [(attr, value) for attr, value in attributes.items() if value is not None]
        attr_value_IS_NULL = [attr for attr, value in attributes.items() if value is None]

        nulls_sql = ' AND '.join([f"{att} IS NULL" for att in attr_value_IS_NULL])
        where_clauses = [f'{attr} = ?' for attr, _ in attr_value_pairs]

        additional_conditions = []
        if fromtocolumn and from_:
            additional_conditions.append(f'{fromtocolumn} >= {from_}')
        if fromtocolumn and to:
            additional_conditions.append(f'{fromtocolumn} <= {to}')

        where_clause = ' AND '.join(where_clauses + additional_conditions)

        select_by_attrs_sql = f'SELECT * FROM {object_type_name} ' \
                              "WHERE " \
                              f'{nulls_sql + " AND " if nulls_sql else ""}' \
                              f'{where_clause}' \
                              f'{"ORDER BY {sort_by} DESC " if sort_by and not sort_order else ""}' \
                              f'{"LIMIT {limit} " if limit else ""}' \
                              f'{"OFFSET {int(page) * int(limit)} " if page else ""};'

        values = tuple(value for _, value in attr_value_pairs)

        cursor.execute(select_by_attrs_sql, values)

        rows = cursor.fetchall()
        conn.close()

        objects = []
        for row in rows:
            obj = self.object_type()
            for i, value in enumerate(row):
                if type(getattr(obj, cursor.description[i][0])) == JsonField:
                    if value is not None:
                        value = json.loads(value)
                    setattr(obj, cursor.description[i][0], value)
                elif type(getattr(obj, cursor.description[i][0])) == ForeignKey:
                    if value is not None:
                        value = json.loads(value)
                        setattr(obj, cursor.description[i][0], EXTERN_TYPES[value['type']].objects.get(**{value['key']: value['value']}))
                    else:
                        setattr(obj, cursor.description[i][0], value)

                else:
                    setattr(obj, cursor.description[i][0], value)
            objects.append(obj)

        return ListOfObjects(objects)

    def all(self):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        object_type_name = self.object_type.__name__
        select_all_sql = f'SELECT * FROM {object_type_name};'

        cursor.execute(select_all_sql)
        rows = cursor.fetchall()
        conn.close()

        objects = []
        for row in rows:
            obj = self.object_type()
            for i, value in enumerate(row):
                if type(getattr(obj, cursor.description[i][0])) == JsonField:
                    if value is not None:
                        value = json.loads(value)
                    setattr(obj, cursor.description[i][0], value)
                elif type(getattr(obj, cursor.description[i][0])) == ForeignKey:
                    if value is not None and value != 'None':
                        value = json.loads(value)
                        setattr(obj, cursor.description[i][0], EXTERN_TYPES[value['type']].objects.get(**{value['key']: value['value']}))
                    else:
                        setattr(obj, cursor.description[i][0], value)

                else:
                    setattr(obj, cursor.description[i][0], value)
            objects.append(obj)

        return ListOfObjects(objects)

    def count(self):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        object_type_name = self.object_type.__name__
        cursor.execute(f"SELECT COUNT(*) FROM {object_type_name}")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    def __createTable__(self):
        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()
        custom_fields = []
        primary_key = None
        for key, value in vars(self.object_type).items():
            if not key.startswith("__") and not callable(value):
                field_name = key
                field_type = value.field_type
                is_primary = value.primary_key
                is_unique = value.unique
                is_null = value.null
                default_value = value.default

                if value.field_type == 'FOREIGN_KEY':
                    field_type = "TEXT"
                if value.field_type == 'JSON':
                    field_type = 'TEXT'

                field_declaration = [f'"{field_name}" {field_type}']

                if is_primary:
                    primary_key = key
                if is_unique:
                    field_declaration.append('UNIQUE')
                if not is_null:
                    field_declaration.append('NOT NULL')
                if default_value is not None:
                    field_declaration.append(f'DEFAULT {default_value}')

                custom_fields.append(' '.join(field_declaration))

        if not primary_key is None:
            custom_fields.append(f'PRIMARY KEY({primary_key})')
        create_table_sql = f'''
        CREATE TABLE IF NOT EXISTS {self.object_type.__name__} (
            {", ".join(custom_fields)}
        );
        '''
        cursor.execute(create_table_sql)

        conn.commit()
        conn.close()


class ProxyObjects:
    def __get__(self, instance, owner):
        fields = [el for el in vars(owner) if not el.startswith("__")]
        primary_key = None
        for el in fields:
            if getattr(owner, el).primary_key:
                primary_key = el
                break
        return Object(owner, primary_key)


class Model:
    objects = ProxyObjects()

    def __init__(self, *args, **kwargs):
        fields = [el for el in vars(self.__class__) if not el.startswith("__")]
        for i, value in enumerate(args):
            setattr(self, fields[i], value)

        for field, value in kwargs.items():
            setattr(self, field, value)

    def save(self):
        self.objects.save(self)

    def delete(self):
        self.objects.delete_object(self)

    def json(self):
        attributes = {}
        for key, value in vars(self).items():
            if not key.startswith("__") and not callable(value):
                if type(getattr(self.objects.object_type, key)) == ForeignKey and value is not None and value != 'None':
                    attributes[key] = {'type': type(value).__name__, 'key': getattr(type(self), key).foreign_field[0],
                     'value': getattr(value, getattr(type(self), key).foreign_field[0])}
                    continue
                attributes[key] = value

        return attributes

