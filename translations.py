import json
from aiogram import types, Dispatcher
from aiogram.dispatcher.filters import Regexp
from database.sql import set_language
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

async def set_language_handler(call: types.CallbackQuery):
    language_code = str(call.data).split('_')[1]
    await set_language(call.message.chat.id, language_code)    
    user_languages[call.message.chat.id] = language_code
    start_kb = InlineKeyboardMarkup()
    start_button = InlineKeyboardButton(text=await get_translation(call.message, 'start_btn'), callback_data='start')
    start_kb.add(start_button)
    await call.message.answer(await get_translation(call.message, 'language_changed'), reply_markup=start_kb)
    await call.message.delete()
    
def set_user_languages(value):
    global user_languages
    user_languages = value

async def set_user_language(user_id, language_code):
    user_languages[user_id] = language_code
    

async def choose_language(message_or_callback: types.Message | types.CallbackQuery):
    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.delete()
        message = message_or_callback.message
    else:
        message = message_or_callback
    if message.chat.type == 'private':
        language_kb = InlineKeyboardMarkup(row_width=2)
        uk_button = InlineKeyboardButton(text='Українська', callback_data='lc_uk')
        ru_button = InlineKeyboardButton(text='Русский', callback_data='lc_ru')
        language_kb.add(uk_button, ru_button)
        await message.answer(await get_translation(message, 'choose_language') , reply_markup=language_kb)
    
async def get_translation(message, text_key):
    if message.from_user.language_code in ['uk', 'ru']:
        default = message.from_user.language_code
    else:
        default = 'ru'
    language = user_languages.get(message.chat.id, default)
    with open(f'locales/{language}.json', 'r', encoding='utf-8') as f:
        translations = json.load(f)
    return translations.get(text_key, text_key)

def register_handlers_translation(dp: Dispatcher):
    dp.register_message_handler(choose_language, commands=['choose_language'])
    dp.register_callback_query_handler(set_language_handler, Regexp(r'^lc_'))
