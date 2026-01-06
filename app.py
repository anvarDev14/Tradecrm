import asyncio
from aiogram import executor

from loader import dp, bot
import middlewares, filters, handlers
from utils.notify_admins import on_startup_notify
from utils.set_bot_commands import set_default_commands
from utils.scheduler import subscription_scheduler
from utils.db_api.database import init_db

async def on_startup(dispatcher):
    # Database ni yaratish
    init_db()
    
    # Birlamchi komandalar (/start va /help)
    await set_default_commands(dispatcher)

    # Bot ishga tushgani haqida adminga xabar berish
    await on_startup_notify(dispatcher)
    
    # Obunalar tekshirish schedulerini ishga tushirish
    asyncio.create_task(subscription_scheduler(bot))
    
    print("Bot ishga tushdi!")

async def on_shutdown(dispatcher):
    print("Bot to'xtatildi!")

if __name__ == '__main__':
    executor.start_polling(
        dp, 
        on_startup=on_startup,
        on_shutdown=on_shutdown,
        skip_updates=True
    )
