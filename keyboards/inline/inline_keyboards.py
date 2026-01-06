# Inline klaviaturalar
# Asosiy inline klaviaturalar keyboards/default/keyboards.py faylida
# Bu fayl qo'shimcha inline klaviaturalar uchun

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def inline_back_button(callback_data: str = "back"):
    """Orqaga qaytish inline tugmasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔙 Orqaga", callback_data=callback_data))
    return keyboard

def yes_no_keyboard(yes_data: str, no_data: str):
    """Ha/Yo'q inline tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=yes_data),
        InlineKeyboardButton("❌ Yo'q", callback_data=no_data)
    )
    return keyboard
