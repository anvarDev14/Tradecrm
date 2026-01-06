import asyncio
from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot
from data.config import ADMINS
from states.states import AdminBroadcastStates
from utils.db_api.database import (
    get_all_users, get_active_subscriptions, get_subscription,
    set_setting, get_setting
)
from keyboards.default.keyboards import (
    admin_menu_keyboard, admin_broadcast_keyboard, cancel_keyboard,
    broadcast_target_keyboard, broadcast_confirm_keyboard
)

def is_admin(user_id):
    return str(user_id) in ADMINS

# ============ REKLAMA BOSHQARUVI ============

@dp.message_handler(text="📢 Reklama")
async def admin_broadcast_menu(message: types.Message):
    """Reklama menyusi"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📢 <b>Reklama yuborish</b>\n\n"
        "Quyidagi variantlardan birini tanlang:",
        reply_markup=admin_broadcast_keyboard()
    )

@dp.message_handler(text="📝 Matn yuborish")
async def broadcast_text_start(message: types.Message, state: FSMContext):
    """Matnli reklama"""
    if not is_admin(message.from_user.id):
        return
    
    await state.update_data(broadcast_type='text')
    await message.answer(
        "👥 <b>Kimga yuborish kerak?</b>",
        reply_markup=broadcast_target_keyboard()
    )
    await AdminBroadcastStates.select_target.set()

@dp.message_handler(text="🖼 Rasm yuborish")
async def broadcast_photo_start(message: types.Message, state: FSMContext):
    """Rasmli reklama"""
    if not is_admin(message.from_user.id):
        return
    
    await state.update_data(broadcast_type='photo')
    await message.answer(
        "👥 <b>Kimga yuborish kerak?</b>",
        reply_markup=broadcast_target_keyboard()
    )
    await AdminBroadcastStates.select_target.set()

@dp.message_handler(text="🎬 Video yuborish")
async def broadcast_video_start(message: types.Message, state: FSMContext):
    """Videoli reklama"""
    if not is_admin(message.from_user.id):
        return
    
    await state.update_data(broadcast_type='video')
    await message.answer(
        "👥 <b>Kimga yuborish kerak?</b>",
        reply_markup=broadcast_target_keyboard()
    )
    await AdminBroadcastStates.select_target.set()

@dp.callback_query_handler(text_startswith="broadcast_", state=AdminBroadcastStates.select_target)
async def select_broadcast_target(call: types.CallbackQuery, state: FSMContext):
    """Maqsadni tanlash"""
    target = call.data.replace("broadcast_", "")
    
    await state.update_data(target=target)
    data = await state.get_data()
    
    target_text = {
        'all': 'barcha foydalanuvchilar',
        'subscribers': 'faqat obunadorlar',
        'non_subscribers': 'obunasi yo\'qlar'
    }
    
    await call.message.edit_text(
        f"✅ Maqsad: <b>{target_text.get(target, target)}</b>\n\n"
        f"Endi {'xabar matnini' if data['broadcast_type'] == 'text' else 'mediafaylni'} yuboring:"
    )
    
    if data['broadcast_type'] == 'text':
        await AdminBroadcastStates.enter_message.set()
    elif data['broadcast_type'] == 'photo':
        await AdminBroadcastStates.enter_photo.set()
    else:
        await AdminBroadcastStates.enter_video.set()

@dp.message_handler(state=AdminBroadcastStates.enter_message)
async def enter_broadcast_message(message: types.Message, state: FSMContext):
    """Xabar matnini qabul qilish"""
    await state.update_data(message_text=message.text)
    
    data = await state.get_data()
    
    # Oldindan ko'rsatish
    await message.answer(
        "📋 <b>Xabar oldindan ko'rish:</b>\n\n"
        f"{message.text}\n\n"
        "Yuborishni tasdiqlaysizmi?",
        reply_markup=broadcast_confirm_keyboard()
    )
    await AdminBroadcastStates.confirm_broadcast.set()

@dp.message_handler(content_types=['photo'], state=AdminBroadcastStates.enter_photo)
async def enter_broadcast_photo(message: types.Message, state: FSMContext):
    """Rasmni qabul qilish"""
    photo_id = message.photo[-1].file_id
    caption = message.caption or ""
    
    await state.update_data(photo_id=photo_id, caption=caption)
    
    # Oldindan ko'rsatish
    await bot.send_photo(
        message.from_user.id,
        photo_id,
        caption=f"📋 <b>Oldindan ko'rish:</b>\n\n{caption}\n\nYuborishni tasdiqlaysizmi?"
    )
    await message.answer("Tasdiqlang:", reply_markup=broadcast_confirm_keyboard())
    await AdminBroadcastStates.confirm_broadcast.set()

@dp.message_handler(content_types=['video'], state=AdminBroadcastStates.enter_video)
async def enter_broadcast_video(message: types.Message, state: FSMContext):
    """Videoni qabul qilish"""
    video_id = message.video.file_id
    caption = message.caption or ""
    
    await state.update_data(video_id=video_id, caption=caption)
    
    # Oldindan ko'rsatish
    await bot.send_video(
        message.from_user.id,
        video_id,
        caption=f"📋 <b>Oldindan ko'rish:</b>\n\n{caption}\n\nYuborishni tasdiqlaysizmi?"
    )
    await message.answer("Tasdiqlang:", reply_markup=broadcast_confirm_keyboard())
    await AdminBroadcastStates.confirm_broadcast.set()

@dp.callback_query_handler(text="confirm_broadcast", state=AdminBroadcastStates.confirm_broadcast)
async def confirm_broadcast(call: types.CallbackQuery, state: FSMContext):
    """Reklamani yuborish"""
    data = await state.get_data()
    target = data['target']
    broadcast_type = data['broadcast_type']
    
    # Maqsadli foydalanuvchilarni olish
    all_users = get_all_users()
    
    if target == 'all':
        users = all_users
    elif target == 'subscribers':
        users = [u for u in all_users if get_subscription(u['user_id']) and get_subscription(u['user_id'])['is_active']]
    else:  # non_subscribers
        users = [u for u in all_users if not get_subscription(u['user_id']) or not get_subscription(u['user_id'])['is_active']]
    
    await call.message.edit_text(f"📤 Yuborilmoqda... (0/{len(users)})")
    
    sent = 0
    failed = 0
    
    for user in users:
        try:
            if broadcast_type == 'text':
                await bot.send_message(user['user_id'], data['message_text'])
            elif broadcast_type == 'photo':
                await bot.send_photo(user['user_id'], data['photo_id'], caption=data.get('caption', ''))
            else:
                await bot.send_video(user['user_id'], data['video_id'], caption=data.get('caption', ''))
            
            sent += 1
        except Exception as e:
            failed += 1
        
        # Har 20 ta xabardan keyin yangilash
        if (sent + failed) % 20 == 0:
            try:
                await call.message.edit_text(f"📤 Yuborilmoqda... ({sent + failed}/{len(users)})")
            except:
                pass
        
        await asyncio.sleep(0.05)  # Flood limitdan himoya
    
    await state.finish()
    
    await call.message.edit_text(
        f"""✅ <b>Reklama yuborildi!</b>

👥 Jami: {len(users)}
✅ Yuborildi: {sent}
❌ Xato: {failed}"""
    )
    await call.message.answer("📢 Reklama menyusi:", reply_markup=admin_broadcast_keyboard())

@dp.callback_query_handler(text="cancel_broadcast", state=AdminBroadcastStates.confirm_broadcast)
async def cancel_broadcast(call: types.CallbackQuery, state: FSMContext):
    """Reklamani bekor qilish"""
    await state.finish()
    await call.message.edit_text("❌ Reklama bekor qilindi")
    await call.message.answer("📢 Reklama menyusi:", reply_markup=admin_broadcast_keyboard())

# ============ FOYDALANUVCHILAR ============

@dp.message_handler(text="👥 Foydalanuvchilar")
async def admin_users(message: types.Message):
    """Foydalanuvchilar ro'yxati"""
    if not is_admin(message.from_user.id):
        return
    
    users = get_all_users()
    
    text = f"👥 <b>Foydalanuvchilar:</b> {len(users)} ta\n\n"
    
    # Oxirgi 20 ta foydalanuvchi
    for user in users[:20]:
        subscription = get_subscription(user['user_id'])
        sub_status = "✅" if subscription and subscription['is_active'] else "❌"
        text += f"{sub_status} {user['full_name'][:20]} | @{user['username'] or '-'}\n"
    
    if len(users) > 20:
        text += f"\n... va yana {len(users) - 20} ta"
    
    await message.answer(text, reply_markup=admin_menu_keyboard())

# ============ SOZLAMALAR ============

@dp.message_handler(text="⚙️ Sozlamalar")
async def admin_settings(message: types.Message):
    """Sozlamalar"""
    if not is_admin(message.from_user.id):
        return
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    
    keyboard = InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        InlineKeyboardButton("📝 Bot haqida matnini o'zgartirish", callback_data="edit_about"),
        InlineKeyboardButton("📞 Aloqa ma'lumotlarini o'zgartirish", callback_data="edit_support"),
        InlineKeyboardButton("🔔 Ogohlantirish sozlamalari", callback_data="edit_notifications")
    )
    
    await message.answer(
        "⚙️ <b>Bot sozlamalari</b>\n\n"
        "Quyidagi sozlamalardan birini tanlang:",
        reply_markup=keyboard
    )

@dp.callback_query_handler(text="edit_about")
async def edit_about_start(call: types.CallbackQuery, state: FSMContext):
    """Bot haqida matnini tahrirlash"""
    if not is_admin(call.from_user.id):
        return
    
    current = get_setting('about_text')
    
    await call.message.answer(
        f"📝 <b>Joriy 'Bot haqida' matni:</b>\n\n{current or 'Ornatilmagan'}\n\n"
        "Yangi matnni kiriting:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state("edit_about_text")
    await call.answer()

@dp.message_handler(state="edit_about_text")
async def edit_about_save(message: types.Message, state: FSMContext):
    """Bot haqida matnini saqlash"""
    set_setting('about_text', message.text)
    await state.finish()
    await message.answer("✅ 'Bot haqida' matni yangilandi!", reply_markup=admin_menu_keyboard())

@dp.callback_query_handler(text="edit_support")
async def edit_support_start(call: types.CallbackQuery, state: FSMContext):
    """Aloqa ma'lumotlarini tahrirlash"""
    if not is_admin(call.from_user.id):
        return
    
    current = get_setting('support_info')
    
    await call.message.answer(
        f"📞 <b>Joriy aloqa ma'lumotlari:</b>\n\n{current or 'Ornatilmagan'}\n\n"
        "Yangi ma'lumotlarni kiriting:",
        reply_markup=cancel_keyboard()
    )
    await state.set_state("edit_support_info")
    await call.answer()

@dp.message_handler(state="edit_support_info")
async def edit_support_save(message: types.Message, state: FSMContext):
    """Aloqa ma'lumotlarini saqlash"""
    set_setting('support_info', message.text)
    await state.finish()
    await message.answer("✅ Aloqa ma'lumotlari yangilandi!", reply_markup=admin_menu_keyboard())

@dp.message_handler(text="🔙 Admin panel")
async def back_to_admin(message: types.Message, state: FSMContext):
    """Admin panelga qaytish"""
    if not is_admin(message.from_user.id):
        return
    
    await state.finish()
    await message.answer("📊 Admin panel", reply_markup=admin_menu_keyboard())
