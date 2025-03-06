from unittest.mock import AsyncMock, MagicMock, call
import pytest

from database.models import Product
from handlers.admin_private import ADMIN_KB, add_product, starring_at_product
from handlers.user_private import start_cmd
from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard




@pytest.mark.asyncio
async def test_start_handler():
    message = AsyncMock()
    await start_cmd(message)

    message.answer.assert_called_with("Здрастуйте! Натисніть кнопку 'Меню🍎' для перегляду списку ваших рецептів: " ,
        reply_markup=get_keyboard(
            "Меню🍎",
        ))


@pytest.mark.asyncio
async def test_add_product():
    message = AsyncMock()
    await add_product(message)
    message.answer.assert_called_with(
        "Що ви хочете зробити?",
        reply_markup=ADMIN_KB
    )



@pytest.mark.asyncio
async def test_starring_at_product():
    message = AsyncMock()
    session = MagicMock()

    session.orm_get_products.return_value = [
        Product(id=1, name="Product 1", image="image1.jpg", recipe="Recipe 1"),
        Product(id=2, name="Product 2", image="image2.jpg", recipe="Recipe 2"),
    ]

    await starring_at_product(message, session)
    session.orm_get_products.assert_called_once()
    expected_calls = [
        call(product.image, caption=f"<strong>{product.name}</strong>\n{product.recipe}", reply_markup=get_callback_btns(btns={
            'Видалити': f'delete_{product.id}',
            'Змінити': f'change_{product.id}'
        })) for product in session.orm_get_products.return_value
    ]
    message.answer_photo.assert_has_calls(expected_calls, any_order=True)
    message.answer.assert_called_once_with("Ось список рецептів:")
