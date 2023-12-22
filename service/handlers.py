import json
from service.client import Admin
from hashlib import sha256, md5
from uuid import uuid4
import time


def request_filter(request, filters):
    """ Проверяет запрос на соответствие фильтрам хэндлера.
    """
    for k, v in filters.items():
        if '__in' == k[-4:]:
            if k[:-4] not in request or v not in request[k[:-4]]:
                return False
        elif '__not_in' == k[-9:]:
            if k[:-9] not in request or v in request[k[:-9]]:
                return False
        elif '__gre' == k[-5:]:
            if k[:-5] not in request or v >= int(request[k[:-5]]):
                return False
        elif '__gr' == k[-4:]:
            if k[:-4] not in request or v > int(request[k[:-4]]):
                return False
        elif '__lte' == k[-5:]:
            if k[:-5] not in request or v <= int(request[k[:-5]]):
                return False
        elif '__lt' == k[-4:]:
            if k[:-4] not in request or v < int(request[k[:-4]]):
                return False
        elif k == '__required_data__':
            for _ in v:
                if _ not in request:
                    return False
        else:
            if k not in request:
                return False
            if not (v == request[k] or (request[k].isdigit() and v == int(request[k]))):
                return False
    return True


handlers = {}


def handler(*_, **filters):
    """ Декоратор, который добавляет хэндлеры и фильтры к ним в список хэндлеров.
    """
    def decorator(func):
        handlers[func] = filters

    return decorator


def auth(auth_request):
    """ Функция аутентификации. Возвращает False, None или Admin.
    """
    try:
        auth_request = json.loads(auth_request)
    except:
        return False

    if 'login' not in auth_request or 'password' not in auth_request:
        return False

    admin = Admin.objects.get(
        login=auth_request['login'],
        password_hash=md5(str(auth_request['password']).encode()).hexdigest()
    )

    return admin


async def main_loop(reader, writer):
    """ Цикл сессии. Принимает запросы, раскидывает их по хэндлерам.
    """
    global handlers

    # Авторизация
    auth_request = (await reader.read(2**15)).decode('utf8')
    admin: Admin = auth(auth_request)
    if admin:
        admin.token = str(uuid4())
        admin.token_expire = time.time() + 7 * 24 * 60 * 60
        admin.is_active = 1
        admin.save()
        response = json.dumps({"status": "successfully authorized", "admin": admin.json()})
        writer.write(response.encode('utf8'))
        await writer.drain()
    else:
        response = json.dumps({"status": "quit", "error": "unauthorized"})
        writer.write(response.encode('utf8'))
        await writer.drain()
        writer.close()
        return

    # Цикл сессии
    while True:
        try:
            request = json.loads((await reader.read(2**15)).decode('utf8'))

            # Выход из сессии
            if request['method'] == 'quit':
                response = json.dumps({"status": "successfully quited"})
                writer.write(response.encode('utf8'))
                await writer.drain()
                writer.close()
                admin.is_active = 0
                admin.save()
                return

            # Определение хэндлера
            for func, filters in handlers.items():
                if request_filter(request, filters):
                    response = json.dumps(await func(request))
                    break

        except Exception as e:
            print(request)
            print(e)
            response = json.dumps({"status": "bad request"})

        writer.write(response.encode('utf8'))

        try:
            await writer.drain()
        except:
            admin.is_active = 0
            admin.save()
            print('bad session end')
            return

    writer.close()
