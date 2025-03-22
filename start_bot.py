from aiogram.utils import executor
from create_bot import dp, bot
from handlers import private
from database import sql
# from translations import set_user_language, register_handlers_translation
import translations

async def on_startup(_):
    sql.start_sql()
    users = sql.get_languages()
    user_language = dict(users)
    translations.set_user_languages(user_language)

private.register_handlers_private(dp)
translations.register_handlers_translation(dp)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True, on_startup=on_startup)