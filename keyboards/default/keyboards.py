from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from utils.db_api.database import get_active_cards, get_active_prices, get_all_videos, get_free_videos

# ============ ASOSIY MENYU ============

def main_menu_keyboard():
    """Asosiy menyu klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("💳 To'lov qilish"),
        KeyboardButton("📊 Obuna holati")
    )
    keyboard.add(
        KeyboardButton("📚 Video qo'llanmalar"),
        KeyboardButton("📞 Aloqa")
    )
    keyboard.add(
        KeyboardButton("ℹ️ Bot haqida")
    )
    return keyboard

def back_keyboard():
    """Orqaga qaytish tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔙 Orqaga"))
    return keyboard

def cancel_keyboard():
    """Bekor qilish tugmasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("❌ Bekor qilish"))
    return keyboard

def back_and_cancel_keyboard():
    """Orqaga va bekor qilish tugmalari"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.add(KeyboardButton("🔙 Orqaga"), KeyboardButton("❌ Bekor qilish"))
    return keyboard

# ============ TO'LOV ============

def payment_menu_keyboard():
    """To'lov menyu klaviaturasi"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("💰 Yangi to'lov"),
        KeyboardButton("📋 To'lovlarim tarixi")
    )
    keyboard.add(KeyboardButton("🔙 Orqaga"))
    return keyboard

def prices_inline_keyboard():
    """Narxlar inline klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    prices = get_active_prices()
    
    for price in prices:
        text = f"📦 {price['days']} kun - {price['price']:,.0f} so'm"
        keyboard.add(InlineKeyboardButton(text, callback_data=f"select_price:{price['id']}"))
    
    return keyboard

def cards_inline_keyboard():
    """Kartalar inline klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    cards = get_active_cards()
    
    for card in cards:
        text = f"💳 {card['card_number']} ({card['bank_name'] or 'Karta'})"
        keyboard.add(InlineKeyboardButton(text, callback_data=f"select_card:{card['id']}"))
    
    return keyboard

def confirm_payment_keyboard():
    """To'lovni tasdiqlash inline klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Chek yuborish", callback_data="send_receipt"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_payment")
    )
    return keyboard

def skip_receipt_keyboard():
    """Chekni o'tkazib yuborish"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("⏩ Keyinroq yuboraman", callback_data="skip_receipt"))
    return keyboard

# ============ VIDEO QO'LLANMALAR ============

def videos_inline_keyboard(is_subscribed: bool = False):
    """Videolar ro'yxati inline klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    
    if is_subscribed:
        videos = get_all_videos()
    else:
        videos = get_free_videos()
    
    for video in videos:
        icon = "🆓" if video['is_free'] else "🔒"
        text = f"{icon} {video['name']}"
        keyboard.add(InlineKeyboardButton(text, callback_data=f"watch_video:{video['id']}"))
    
    if not is_subscribed and len(get_all_videos()) > len(videos):
        keyboard.add(InlineKeyboardButton("🔓 Premium videolar uchun obuna bo'ling", callback_data="subscribe_for_videos"))
    
    return keyboard

# ============ OBUNA HOLATI ============

def subscription_keyboard():
    """Obuna holati klaviaturasi"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("🔄 Obunani yangilash", callback_data="renew_subscription"),
        InlineKeyboardButton("📞 Yordam", callback_data="contact_support")
    )
    return keyboard

def channel_link_keyboard(invite_link: str):
    """Kanal havolasi klaviaturasi"""
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton("🔗 Kanalga qo'shilish", url=invite_link))
    return keyboard

# ============ ADMIN PANEL ============

def admin_menu_keyboard():
    """Admin panel asosiy menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📊 Statistika"),
        KeyboardButton("💳 To'lovlar")
    )
    keyboard.add(
        KeyboardButton("👥 Foydalanuvchilar"),
        KeyboardButton("📅 Obunalar")
    )
    keyboard.add(
        KeyboardButton("💰 Kartalar"),
        KeyboardButton("📺 Kanallar")
    )
    keyboard.add(
        KeyboardButton("🎬 Videolar"),
        KeyboardButton("💵 Narxlar")
    )
    keyboard.add(
        KeyboardButton("📢 Reklama"),
        KeyboardButton("⚙️ Sozlamalar")
    )
    keyboard.add(KeyboardButton("🔙 Foydalanuvchi rejimi"))
    return keyboard

def admin_payments_keyboard():
    """Admin to'lovlar menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("⏳ Kutayotgan to'lovlar"),
        KeyboardButton("✅ Tasdiqlangan to'lovlar")
    )
    keyboard.add(
        KeyboardButton("❌ Rad etilgan to'lovlar"),
        KeyboardButton("📋 Barcha to'lovlar")
    )
    keyboard.add(KeyboardButton("🔙 Admin panel"))
    return keyboard

def admin_subscriptions_keyboard():
    """Admin obunalar menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("✅ Faol obunalar"),
        KeyboardButton("⚠️ Tugayotgan obunalar")
    )
    keyboard.add(
        KeyboardButton("❌ O'tgan obunalar"),
        KeyboardButton("📋 Barcha obunalar")
    )
    keyboard.add(KeyboardButton("🔙 Admin panel"))
    return keyboard

def admin_cards_keyboard():
    """Admin kartalar menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("➕ Karta qo'shish"),
        KeyboardButton("📋 Barcha kartalar")
    )
    keyboard.add(KeyboardButton("🔙 Admin panel"))
    return keyboard

def admin_channels_keyboard():
    """Admin kanallar menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("➕ Kanal qo'shish"),
        KeyboardButton("📋 Barcha kanallar")
    )
    keyboard.add(KeyboardButton("🔙 Admin panel"))
    return keyboard

def admin_videos_keyboard():
    """Admin videolar menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("➕ Video qo'shish"),
        KeyboardButton("📋 Barcha videolar")
    )
    keyboard.add(KeyboardButton("🔙 Admin panel"))
    return keyboard

def admin_prices_keyboard():
    """Admin narxlar menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("➕ Narx qo'shish"),
        KeyboardButton("📋 Barcha narxlar")
    )
    keyboard.add(KeyboardButton("🔙 Admin panel"))
    return keyboard

def admin_broadcast_keyboard():
    """Admin reklama menyu"""
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    keyboard.add(
        KeyboardButton("📝 Matn yuborish"),
        KeyboardButton("🖼 Rasm yuborish")
    )
    keyboard.add(
        KeyboardButton("🎬 Video yuborish"),
        KeyboardButton("📊 Reklama tarixi")
    )
    keyboard.add(KeyboardButton("🔙 Admin panel"))
    return keyboard

# ============ INLINE ADMIN TUGMALAR ============

def payment_action_keyboard(payment_id: int):
    """To'lov uchun admin tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"approve_payment:{payment_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"reject_payment:{payment_id}")
    )
    keyboard.add(
        InlineKeyboardButton("👤 Foydalanuvchi", callback_data=f"view_user_payment:{payment_id}")
    )
    return keyboard

def card_action_keyboard(card_id: int, is_active: bool):
    """Karta uchun admin tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    status_text = "🔴 O'chirish" if is_active else "🟢 Yoqish"
    keyboard.add(
        InlineKeyboardButton(status_text, callback_data=f"toggle_card:{card_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_card:{card_id}")
    )
    return keyboard

def channel_action_keyboard(channel_id: int, is_active: bool):
    """Kanal uchun admin tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    status_text = "🔴 O'chirish" if is_active else "🟢 Yoqish"
    keyboard.add(
        InlineKeyboardButton(status_text, callback_data=f"toggle_channel:{channel_id}"),
        InlineKeyboardButton("🔗 Havola", callback_data=f"edit_channel_link:{channel_id}")
    )
    keyboard.add(
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_channel:{channel_id}")
    )
    return keyboard

def video_action_keyboard(video_id: int, is_free: bool):
    """Video uchun admin tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    free_text = "💰 Pullik qilish" if is_free else "🆓 Bepul qilish"
    keyboard.add(
        InlineKeyboardButton(free_text, callback_data=f"toggle_video_free:{video_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_video:{video_id}")
    )
    keyboard.add(
        InlineKeyboardButton("▶️ Ko'rish", callback_data=f"preview_video:{video_id}")
    )
    return keyboard

def price_action_keyboard(price_id: int, is_active: bool):
    """Narx uchun admin tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    status_text = "🔴 O'chirish" if is_active else "🟢 Yoqish"
    keyboard.add(
        InlineKeyboardButton(status_text, callback_data=f"toggle_price:{price_id}"),
        InlineKeyboardButton("🗑 O'chirish", callback_data=f"delete_price:{price_id}")
    )
    return keyboard

def subscription_action_keyboard(user_id: int):
    """Obuna uchun admin tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("📤 Xabar yuborish", callback_data=f"notify_user:{user_id}"),
        InlineKeyboardButton("❌ Obunani o'chirish", callback_data=f"deactivate_sub:{user_id}")
    )
    return keyboard

def confirm_action_keyboard(action: str, item_id: int):
    """Tasdiqlash tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Ha", callback_data=f"confirm_{action}:{item_id}"),
        InlineKeyboardButton("❌ Yo'q", callback_data=f"cancel_{action}:{item_id}")
    )
    return keyboard

def broadcast_confirm_keyboard():
    """Reklama tasdiqlash tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=2)
    keyboard.add(
        InlineKeyboardButton("✅ Yuborish", callback_data="confirm_broadcast"),
        InlineKeyboardButton("❌ Bekor qilish", callback_data="cancel_broadcast")
    )
    return keyboard

def broadcast_target_keyboard():
    """Reklama maqsadi tugmalari"""
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("👥 Barcha foydalanuvchilar", callback_data="broadcast_all"),
        InlineKeyboardButton("✅ Faqat obunadorlar", callback_data="broadcast_subscribers"),
        InlineKeyboardButton("❌ Obunasi yo'qlar", callback_data="broadcast_non_subscribers")
    )
    return keyboard
