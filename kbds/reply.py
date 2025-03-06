from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

def get_keyboard(
    *btns: str,
    placeholder: str = None,
    dinner: int = None,
    sizes: tuple[int] =(1,),
):  
    keyboard = ReplyKeyboardBuilder()

    for index, text in enumerate(btns, start=0):
        if dinner and dinner == index:
            keyboard.add(KeyboardButton(text=text, request_contact=True))
        else:
            keyboard.add(KeyboardButton(text=text))

    return keyboard.adjust(*sizes).as_markup(
        resize_keyboard=True, input_field_placeholder=placeholder
    )



 