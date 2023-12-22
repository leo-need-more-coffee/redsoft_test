"""Естественно тесты в реальном продукте должны быть не такие простые. Это просто пример, как бы я это реализовал без
библиотек."""
from api import server, VCM
import asyncio
import traceback


def test(func):
    async def func_wrapper(*args, **kwargs):
        try:
            res = await func(*args, **kwargs)
            print(f'== {func.__name__} PASSED ==')
            return res
        except Exception:
            print(traceback.format_exc())
            print(f'== {func.__name__} FAILED ==')
    return func_wrapper


@test
async def add_test():
    await VCM.add(0, 0, 0, 0, "")


@test
async def get_test():
    await VCM.get(0)


@test
async def save_test():
    vcm = await VCM.get(0)
    vcm.ram += 1
    await vcm.save()


@test
async def delete_test():
    vcm = await VCM.get(0)
    await vcm.delete()


tests = [add_test, get_test, save_test, delete_test]


async def main():
    await server.connect()
    await server.auth("admin", "admin")
    for test in tests:
        await test()
    await server.disconnect()


if __name__ == "__main__":
    asyncio.run(main())