
from aiogram import F, types, Router
from aiogram.filters import CommandStart, Command, or_f
from database.orm_query import orm_get_products
from filters.chat_types import ChatTypeFilter
from kbds.reply import get_keyboard
from sqlalchemy.ext.asyncio import AsyncSession

user_private_router=Router()
user_private_router.message.filter(ChatTypeFilter(["private"]))


@user_private_router.message(CommandStart())
async def start_cmd(message: types.Message):
    await message.answer(
        "Здрастуйте! Натисніть кнопку 'Меню🍎' для перегляду списку ваших рецептів: " ,
        reply_markup=get_keyboard(
            "Меню🍎",
        ),
    )



@user_private_router.message(F.text.lower()== "меню🍎")
@user_private_router.message(Command("menu"))
async def breakfast_cmd(message: types.Message,session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}\
                    </strong>\n{product.recipie}",
        )
    await message.answer("Ось меню)) Приємного апетиту!")

'''
@user_private_router.message(F.text.lower()== "обід🥗")
@user_private_router.message(Command("lunch"))
async def lunch_cmd(message: types.Message):
    await message.answer("Ось рецепти обідів)) Приємного апетиту!")

@user_private_router.message(F.text.lower() == "вечеря🥙")
@user_private_router.message(Command("dinner"))
async def dinner_cmd(message: types.Message):
    await message.answer("Ось рецепти вечерь)) Приємного апетиту!")


@user_private_router.message((F.text) | (F.photo) | (F.stiker))
async def menu_cmd(message: types.Message):
    await message.answer("Натисніть клавішу 'меню' на панелі та оберіть потрібний блок рецептів")
'''


    