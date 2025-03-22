from aiogram import Bot
from aiogram.dispatcher import Dispatcher
from aiogram.contrib.fsm_storage.memory import MemoryStorage

ADMINS = [

]

ALLOWED_USERS = [

]

bot = Bot('TOKEN')
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)
