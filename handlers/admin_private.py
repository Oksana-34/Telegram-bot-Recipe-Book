from aiogram import F, Router, types
from aiogram.filters import Command, StateFilter, or_f
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy.ext.asyncio import AsyncSession

from database.orm_query import (
    orm_add_product,
    orm_delete_product,
    orm_get_product,
    orm_get_products,
    orm_update_product,
)


from filters.chat_types import ChatTypeFilter, IsAdmin
from kbds.inline import get_callback_btns
from kbds.reply import get_keyboard
from handlers.user_private import start_cmd


admin_router = Router()
admin_router.message.filter(ChatTypeFilter(["private"]), IsAdmin())


ADMIN_KB = get_keyboard(
    "Додати рецепт",
    "Асортимент",
    placeholder="Оберіть дію",
    sizes=(2,),
)

class AddRecepie(StatesGroup):
    block = State()
    name = State()
    recipie = State()
    image = State()
    product_for_change = None
    texts = {
        'AddRecepie:block': 'Оберіть блок заново:',
        'AddRecepie:name': 'Введіть назву страви заново:',
        'AddRecepie:recipie': 'Введіть рецепт страви заново:',
        'AddRecepie:image': 'Цей крок останній, тому',
    }

@admin_router.message(Command("admin"))
async def add_product(message: types.Message):
    await message.answer("Що ви хочете зробити?", reply_markup=ADMIN_KB)


@admin_router.message(F.text == "Асортимент")
async def starring_at_product(message: types.Message, session: AsyncSession):
    for product in await orm_get_products(session):
        await message.answer_photo(
            product.image,
            caption=f"<strong>{product.name}</strong>\n{product.recipie}",
            reply_markup=get_callback_btns(btns={
                'Видалити': f'delete_{product.id}',
                'Змінити': f'change_{product.id}'
            })
        )
    
    await message.answer("Ось список рецептів:")


@admin_router.callback_query(F.data.startswith('delete_'))
async def delete_product(callback: types.CallbackQuery, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    await orm_delete_product(session, int(product_id))

    await callback.answer("Товар видалено")
    await callback.message.answer("Товар видалено!")
  
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def delete_product_callback(callback: types.CallbackQuery, state: FSMContext, session: AsyncSession):
    product_id = callback.data.split("_")[-1]
    product_for_change = await orm_get_product(session, int(product_id))

    AddRecepie.product_for_change = product_for_change
    await callback.answer()
    await callback.message.answer(
        "Введіть назву страви", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddRecepie.name)



#Код для машини станів (FSM)

#У стані вводу name
@admin_router.callback_query(StateFilter(None), F.data.startswith("change_"))
async def change_product_callback(
    callback: types.CallbackQuery, state: FSMContext, session: AsyncSession
):
    product_id = callback.data.split("_")[-1]

    product_for_change = await orm_get_product(session, int(product_id))

    AddRecepie.product_for_change = product_for_change

    await callback.answer()
    await callback.message.answer(
        "Введіть назву страви", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddRecepie.name)


#Очікуємо ввід name
@admin_router.message(StateFilter(None) ,F.text == "Додати рецепт")
async def add_meal(message: types.Message, state: FSMContext):
    await message.answer(
        "Введіть назву страви:", reply_markup=types.ReplyKeyboardRemove()
    )
    await state.set_state(AddRecepie.name)


@admin_router.message(StateFilter('*') ,Command("відміна"))
@admin_router.message(StateFilter('*') ,F.text.casefold() == "відміна")
async def cancel_handler(message: types.Message, state: FSMContext) -> None:

    current_state = await state.get_state()
    if current_state is None:
        return
    if AddRecepie.product_for_change:
       AddRecepie.product_for_change = None
    await state.clear()
    await message.answer("Дію відмінено", reply_markup=ADMIN_KB)


# Повернутися на крок назад(на попередній стан)
@admin_router.message(StateFilter("*"), Command("назад"))
@admin_router.message(StateFilter("*"), F.text.casefold() == "назад")
async def back_step_handler(message: types.Message, state: FSMContext) -> None:
    current_state = await state.get_state()

    if current_state == AddRecepie.name:
        await message.answer(
            'Попереднього кроку немає. Введіть назву страви, або напишіть "відміна"'
        )
        return

    previous = None
    for step in AddRecepie.__all_states__:
        if step.state == current_state:
            await state.set_state(previous)
            await message.answer(
                f"Ви повернулися до попереднього кроку \n {AddRecepie.texts[previous.state]}"
            )
            return
        previous = step

#Відловлюємо дані для стану name потім змінюємо стан на recepie
@admin_router.message(AddRecepie.name, or_f(F.text, F.text == "."))
async def add_name(message: types.Message, state: FSMContext):

    if message.text == ".":
        await state.update_data(name=AddRecepie.product_for_change.name)
    else:
        if len(message.text) >= 100:
            await message.answer("Назва рецепту не повинна перевищувати 100 символів. \n Введіть заново:"
            )
            return
        await state.update_data(name=message.text)
    await message.answer("Введіть рецепт")
    await state.set_state(AddRecepie.recipie)  



@admin_router.message(AddRecepie.name)
async def add_name(message: types.Message, state: FSMContext):
    await message.answer("Ви ввели недопустимі дані")
   
#Відловлюємо дані для стану recipie і змінюємо на стан image
@admin_router.message( AddRecepie.recipie, or_f(F.text, F.text == "."))
async def add_recipie(message: types.Message, state: FSMContext):
    if message.text == ".":
         await state.update_data(recipie=AddRecepie.product_for_change.recipie)
    else:
     await state.update_data(recipie=message.text)
    await message.answer("Завантажте фото страви:")
    await state.set_state(AddRecepie.image)

@admin_router.message( AddRecepie.recipie)
async def add_recipie(message: types.Message, state: FSMContext):
    await message.answer("Ви ввели недопустимі дані")
 

#Відловлюємо дані для стану image і потім виходимо із станів
@admin_router.message(AddRecepie.image, or_f(F.photo, F.text == "."))
async def add_image(message: types.Message, state: FSMContext, session: AsyncSession):
    if message.text and message.text == ".":
        await state.update_data(image=AddRecepie.product_for_change.image)

    else:
        await state.update_data(image=message.photo[-1].file_id)
    data = await state.get_data()
    try:
        if AddRecepie.product_for_change:
            await orm_update_product(session, AddRecepie.product_for_change.id, data)
        else:
            await orm_add_product(session, data)
        await message.answer("Товар додано/змінено!", reply_markup=ADMIN_KB)
        await state.clear()
    
    except Exception as e:
        await message.answer(
            f"Помилка: \n{str(e)}\nЩось пішло не так",reply_markup=ADMIN_KB)
        await state.clear()


    AddRecepie.product_for_change=None

@admin_router.message(AddRecepie.image)
async def add_image(message: types.Message, state: FSMContext):
    await message.answer("Відправте фото страви:")
