import unittest
from unittest.mock import patch, MagicMock, AsyncMock
import sys
import asyncio


# Спершу створюємо Mock об'єкти для всіх залежностей
class AsyncMockWithAsyncMethods(MagicMock):
    """Спеціальний клас для моків, які можуть використовуватись з await"""

    async def __call__(self, *args, **kwargs):
        return super(AsyncMockWithAsyncMethods, self).__call__(*args, **kwargs)

    def __await__(self):
        future = asyncio.Future()
        future.set_result(None)
        return future.__await__()


# Мокуємо усі необхідні модулі
bot_mock = AsyncMockWithAsyncMethods()
dp_mock = MagicMock()
create_db_mock = AsyncMockWithAsyncMethods()
drop_db_mock = AsyncMockWithAsyncMethods()
session_maker_mock = MagicMock()
database_session_mock = MagicMock()
bot_cmd_list_mock = MagicMock()
bot_cmd_list_mock.private = []

# Створюємо моки для модулів
sys.modules['aiogram'] = MagicMock()
sys.modules['aiogram.enums'] = MagicMock()
sys.modules['middlewares.db'] = MagicMock()
sys.modules['middlewares.db'].DataBaseSession = database_session_mock
sys.modules['database.engine'] = MagicMock()
sys.modules['database.engine'].create_db = create_db_mock
sys.modules['database.engine'].drop_db = drop_db_mock
sys.modules['database.engine'].session_maker = session_maker_mock
sys.modules['handlers.user_private'] = MagicMock()
sys.modules['handlers.user_group'] = MagicMock()
sys.modules['handlers.admin_private'] = MagicMock()
sys.modules['common.bot_cmd_list'] = bot_cmd_list_mock

# Мокуємо asyncio.run
original_run = asyncio.run


def mock_run(coro):
    # Не запускаємо корутину під час імпорту модуля
    return None


asyncio.run = mock_run

# Мокуємо os.getenv
import os

original_getenv = os.getenv


def mock_getenv(key, default=None):
    if key == 'TOKEN':
        return 'fake_token'
    return original_getenv(key, default)


os.getenv = mock_getenv

# Тепер імпортуємо модуль app
import app

# Відновлюємо оригінальну функцію asyncio.run
asyncio.run = original_run
# Відновлюємо оригінальну функцію os.getenv
os.getenv = original_getenv

# Замінюємо об'єкти в app на наші моки
app.bot = bot_mock
app.dp = dp_mock


class TestApp(unittest.TestCase):
    """
    Тести для функцій з файлу app.py
    """

    async def test_on_startup_with_drop_db(self):
        """
        Тест функції on_startup коли run_param=True
        """
        # Встановлюємо значення run_param на True
        app.on_startup.__globals__['run_param'] = True

        # Скидаємо лічильники викликів
        drop_db_mock.reset_mock()
        create_db_mock.reset_mock()

        # Виконуємо функцію
        await app.on_startup(bot_mock)

        # Перевіряємо виклики
        drop_db_mock.assert_called_once()
        create_db_mock.assert_called_once()

        # Повертаємо оригінальне значення
        app.on_startup.__globals__['run_param'] = False

    async def test_on_startup_without_drop_db(self):
        """
        Тест функції on_startup коли run_param=False
        """
        # Встановлюємо значення run_param на False
        app.on_startup.__globals__['run_param'] = False

        # Скидаємо лічильники викликів
        drop_db_mock.reset_mock()
        create_db_mock.reset_mock()

        # Виконуємо функцію
        await app.on_startup(bot_mock)

        # Перевіряємо, що drop_db не викликалася, а create_db викликалася
        drop_db_mock.assert_not_called()
        create_db_mock.assert_called_once()

    async def test_on_shutdown(self):
        """
        Тест функції on_shutdown
        """
        # Тестуємо з підміною print
        with patch('builtins.print') as mock_print:
            await app.on_shutdown(bot_mock)
            mock_print.assert_called_once_with('бот ліг')

    async def test_main_function(self):
        """
        Тест функції main
        """
        # Мокуємо всі використовувані методи
        dp_mock.startup = MagicMock()
        dp_mock.startup.register = MagicMock()
        dp_mock.shutdown = MagicMock()
        dp_mock.shutdown.register = MagicMock()
        dp_mock.update = MagicMock()
        dp_mock.update.middleware = MagicMock()
        dp_mock.start_polling = AsyncMockWithAsyncMethods()
        dp_mock.resolve_used_update_types = MagicMock(return_value=['message', 'callback_query'])

        bot_mock.delete_webhook = AsyncMockWithAsyncMethods()
        bot_mock.set_my_commands = AsyncMockWithAsyncMethods()

        # Виконуємо функцію main
        await app.main()

        # Перевіряємо реєстрацію handlers
        dp_mock.startup.register.assert_called_once_with(app.on_startup)
        dp_mock.shutdown.register.assert_called_once_with(app.on_shutdown)

        # Перевіряємо налаштування middleware
        dp_mock.update.middleware.assert_called_once()

        # Перевіряємо виклик методів бота
        bot_mock.delete_webhook.assert_called_once_with(drop_pending_updates=True)
        bot_mock.set_my_commands.assert_called_once()

        # Перевіряємо запуск polling
        dp_mock.start_polling.assert_called_once()


# Функція для запуску асинхронних тестів
def run_async_test(test_case):
    async def wrapped_test(self, *args, **kwargs):
        await test_case(self, *args, **kwargs)

    return wrapped_test


# Прив'язуємо асинхронні методи до класу TestApp
TestApp.test_on_startup_with_drop_db = run_async_test(TestApp.test_on_startup_with_drop_db)
TestApp.test_on_startup_without_drop_db = run_async_test(TestApp.test_on_startup_without_drop_db)
TestApp.test_on_shutdown = run_async_test(TestApp.test_on_shutdown)
TestApp.test_main_function = run_async_test(TestApp.test_main_function)

if __name__ == '__main__':
    unittest.main()