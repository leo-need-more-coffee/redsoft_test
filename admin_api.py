""" TODO LIST
___ASYNCIO SOCKET SERVER___
[+] Client-Server architecture.
[+] Auth.
[+] CRUD с фильтрами.
[+] Log out.
[+] Unit-tests.
[+] Statistic.
"""
import asyncio
from service.server import Server
from service.handlers import main_loop, handler
from service.client import VCM, Admin
from hashlib import sha256, md5


def auth(func):
    async def func_wrapper(request):
        if 'token' not in request:
            return {'status': 'not ok', 'error': 'unauthorized'}
        if not Admin.objects.get(token=request['token']):
            return {'status': 'not ok', 'error': 'bad token'}
        res = await func(request)
        return res
    return func_wrapper


@handler(method='add', __required_data__=['id', 'ram', 'cpu', 'disk_memory', 'disk_uuid'])
@auth
async def add(request):
    new_vcm = VCM(
        request['id'],
        request['ram'],
        request['cpu'],
        request['disk_memory'],
        request['disk_uuid'],
    )
    vcm = VCM.objects.add(new_vcm)
    return vcm.json()


@handler(method='get', __required_data__=['id'])
@auth
async def get(request):
    vcm = VCM.objects.get(id=request['id'])
    if not vcm:
        return {"error": "doesnt exist"}
    return vcm.json()


@handler(method='list')
@auth
async def list(request):
    vcm = VCM.objects.all()
    return vcm.json()


@handler(method='filter', __required_data__=['filters'])
@auth
async def filter(request):
    vcm = VCM.objects.filter(**request['filters'])
    return vcm.json()


@handler(method='put', __required_data__=['id'])
@auth
async def put(request):
    vcm = VCM.objects.get(id=request['id'])
    if not vcm:
        return {"error": "doesnt exist"}
    for k, v in request.items():
        if k in VCM.__dict__:
            vcm.__setattr__(k, v)

    vcm.save()
    return vcm.json()


@handler(method='delete', __required_data__=['id'])
@auth
async def delete(request):
    vcm = VCM.objects.get(id=request['id'])
    if not vcm:
        return {"error": "doesnt exist"}
    vcm.delete()
    return vcm.json()


@handler(method='get_disks')
@auth
async def get_disks(request):
    """
    Можно оптимизировать запрос sql, но в данном случае выигрыш в скорости незначительный т.к. количество дисков =
    количеству vcm.
    """
    vcms = VCM.objects.all()
    disks = []
    for el in vcms:
        disks.append({"uuid": el.disk_uuid, "memory": el.disk_memory, "vcm": el.id})
    return disks


@handler(method='statistic')
@auth
async def statistic(request):
    vcms = VCM.objects.all()
    statistic = {
        "vcm_count": 0,
        "ram_count": 0,
        "cpu_count": 0,
    }
    for el in vcms:
        statistic['vcm_count'] += 1
        statistic['ram_count'] += el.ram
        statistic['cpu_count'] += el.cpu
    return statistic


if __name__ == '__main__':
    server = Server('0.0.0.0', 6688, main_loop)
    if len(Admin.objects.all()) == 0:
        admin = Admin(0, 'admin', md5('admin'.encode()).hexdigest(), 123, 1924022530, None, None)
        Admin.objects.add(admin)
    asyncio.run(server.run())
