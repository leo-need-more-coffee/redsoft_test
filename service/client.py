"""
Я тут реализовал очень простую ORM, в ней нет удаления зависимостей и можно было бы оптимизировать фильтры.
Если бы это был бы реальный проект, я либо сделал бы это, либо не изобретал бы велосипед и использовал существующую.
"""
import simple_orm.models as models
from simple_orm.models import IntegerField, TextField, ForeignKey, JsonField
from simple_orm.models import simple_orm
from pathlib import Path
import sys


@simple_orm
class VCM(models.Model):
    """ Виртуальная клиентская машина

    Attributes:
        id  ID.
        ram  Ram в Mb.
        cpu  Количество CPU.
        disk_memory  HDD память в Mb.
        disk_id  HDD uuid.
    """
    id = IntegerField(primary_key=True, unique=True)
    ram = IntegerField()
    cpu = IntegerField()
    disk_memory = IntegerField()
    disk_uuid = TextField()
    is_active = IntegerField(default=0)

@simple_orm
class Admin(models.Model):
    """
    Класс Админа с простейшей авторизацией, можно было бы реализовать полноценный OAuth(или даже OAuth2), но мне кажется
    суть задания не в этом, так что пока что так.


    Attributes:
        token Токен авторизации/аутентификации админа(нужен, чтобы получить доступ к серверу).
        token_expire Unix-time даты, когда кончается токен.
        session_id ID текущей сессии админа.

    """
    id = IntegerField(primary_key=True, unique=True)
    login = TextField(unique=True)
    password_hash = TextField()
    token = TextField()
    token_expire = IntegerField()
    vcm = ForeignKey(VCM, 'id')
    is_active = IntegerField(default=0)


