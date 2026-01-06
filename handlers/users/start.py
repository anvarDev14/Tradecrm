from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import CommandStart

from loader import dp, bot
from data.config import ADMINS
from utils.db_api.database import add_user, get_user, get_subscription
from keyboards.default.keyboards import main_menu_keyboard, admin_menu_keyboard

@dp.message_handler(CommandStart(), state="*")
async def bot_start(message: types.Message, state: FSMContext):
    """Bot ishga tushganda"""
    await state.finish()
    
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Foydalanuvchini bazaga qo'shish
    add_user(user_id, username, full_name)
    
    # Admin yoki oddiy foydalanuvchi
    if str(user_id) in ADMINS:
        text = f"""🎉 <b>Xush kelibsiz, Admin {full_name}!</b>

🤖 Bu bot orqali siz:
• To'lovlarni boshqarishingiz
• Obunalarni nazorat qilishingiz
• Kanallarni sozlashingiz
• Video qo'llanmalar joylashingiz
• Reklama yuborishingiz mumkin

📊 Admin panelga kirish uchun quyidagi tugmani bosing."""
        keyboard = admin_menu_keyboard()
    else:
        # Obuna holatini tekshirish
        subscription = get_subscription(user_id)
        
        if subscription and subscription['is_active']:
            status = "✅ Sizda faol obuna mavjud"
        else:
            status = "❌ Sizda faol obuna yo'q"
        
        text = f"""🎉 <b>Xush kelibsiz, {full_name}!</b>

{status}

🤖 Bu bot orqali siz:
• Premium signallar kanaliga obuna bo'lishingiz
• Video qo'llanmalarni ko'rishingiz
• To'lovlarni amalga oshirishingiz mumkin

📌 Quyidagi tugmalardan foydalaning:"""
        keyboard = main_menu_keyboard()
    
    await message.answer(text, reply_markup=keyboard)

@dp.message_handler(text="🔙 Foydalanuvchi rejimi", state="*")
async def switch_to_user_mode(message: types.Message, state: FSMContext):
    """Admin foydalanuvchi rejimiga o'tish"""
    await state.finish()
    
    user_id = message.from_user.id
    full_name = message.from_user.full_name
    
    subscription = get_subscription(user_id)
    
    if subscription and subscription['is_active']:
        status = "✅ Sizda faol obuna mavjud"
    else:
        status = "❌ Sizda faol obuna yo'q"
    
    text = f"""👤 <b>Foydalanuvchi rejimi</b>

{status}

📌 Quyidagi tugmalardan foydalaning:"""
    
    await message.answer(text, reply_markup=main_menu_keyboard())

@dp.message_handler(text="🔙 Orqaga", state="*")
async def go_back(message: types.Message, state: FSMContext):
    """Orqaga qaytish"""
    await state.finish()
    
    user_id = message.from_user.id
    
    if str(user_id) in ADMINS:
        await message.answer("📊 Admin panel", reply_markup=admin_menu_keyboard())
    else:
        await message.answer("🏠 Asosiy menyu", reply_markup=main_menu_keyboard())

@dp.message_handler(text="❌ Bekor qilish", state="*")
async def cancel_action(message: types.Message, state: FSMContext):
    """Amalni bekor qilish"""
    await state.finish()
    
    user_id = message.from_user.id
    
    if str(user_id) in ADMINS:
        await message.answer("❌ Bekor qilindi", reply_markup=admin_menu_keyboard())
    else:
        await message.answer("❌ Bekor qilindi", reply_markup=main_menu_keyboard())
