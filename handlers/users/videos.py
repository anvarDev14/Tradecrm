from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot
from data.config import ADMINS
from states.states import ContactStates
from utils.db_api.database import (
    get_all_videos, get_free_videos, get_video, get_subscription,
    get_setting
)
from keyboards.default.keyboards import (
    main_menu_keyboard, videos_inline_keyboard, back_keyboard
)

# ============ VIDEO QO'LLANMALAR ============

@dp.message_handler(text="📚 Video qo'llanmalar")
async def video_tutorials(message: types.Message):
    """Video qo'llanmalar"""
    user_id = message.from_user.id
    subscription = get_subscription(user_id)
    is_subscribed = subscription and subscription['is_active']
    
    videos = get_all_videos() if is_subscribed else get_free_videos()
    
    if not videos:
        await message.answer(
            "📚 Hozirda video qo'llanmalar mavjud emas.\n"
            "Iltimos, keyinroq tekshiring.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    if is_subscribed:
        text = "📚 <b>Video qo'llanmalar</b>\n\n✅ Sizda premium obuna bor. Barcha videolar ochiq!"
    else:
        total_videos = len(get_all_videos())
        free_videos = len(videos)
        text = f"📚 <b>Video qo'llanmalar</b>\n\n🆓 Bepul videolar: {free_videos}\n🔒 Premium videolar: {total_videos - free_videos}"
    
    await message.answer(text, reply_markup=videos_inline_keyboard(is_subscribed))

@dp.callback_query_handler(text_startswith="watch_video:")
async def watch_video(call: types.CallbackQuery):
    """Videoni ko'rish"""
    video_id = int(call.data.split(":")[1])
    video = get_video(video_id)
    
    if not video:
        await call.answer("❌ Video topilmadi", show_alert=True)
        return
    
    user_id = call.from_user.id
    subscription = get_subscription(user_id)
    is_subscribed = subscription and subscription['is_active']
    
    # Premium video uchun obuna tekshirish
    if not video['is_free'] and not is_subscribed:
        await call.answer(
            "🔒 Bu premium video!\n"
            "Ko'rish uchun obuna bo'ling.",
            show_alert=True
        )
        return
    
    await call.answer()
    
    caption = f"📹 <b>{video['name']}</b>"
    if video['description']:
        caption += f"\n\n{video['description']}"
    
    try:
        await bot.send_video(
            call.from_user.id,
            video['file_id'],
            caption=caption
        )
    except Exception as e:
        await call.message.answer(f"❌ Videoni yuborishda xato: {e}")

# ============ ALOQA ============

@dp.message_handler(text="📞 Aloqa")
async def contact_menu(message: types.Message):
    """Aloqa menyusi"""
    support_info = get_setting('support_info')
    
    if support_info:
        text = f"📞 <b>Bog'lanish</b>\n\n{support_info}"
    else:
        text = """📞 <b>Bog'lanish</b>

Savollaringiz bo'lsa, quyidagi usullardan foydalaning:

💬 Adminga yozish uchun pastdagi tugmani bosing.
📧 Yoki xabaringizni shu yerga yozing."""
    
    await message.answer(text, reply_markup=back_keyboard())
    await ContactStates.waiting_message.set()

@dp.message_handler(state=ContactStates.waiting_message)
async def receive_contact_message(message: types.Message, state: FSMContext):
    """Foydalanuvchi xabarini qabul qilish"""
    if message.text == "🔙 Orqaga":
        await state.finish()
        await message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_keyboard())
        return
    
    user_id = message.from_user.id
    username = message.from_user.username
    full_name = message.from_user.full_name
    
    # Adminlarga xabar yuborish
    admin_text = f"""📩 <b>Yangi xabar!</b>

👤 Foydalanuvchi: {full_name}
🆔 ID: <code>{user_id}</code>
📱 Username: @{username or 'yoq'}

💬 Xabar:
{message.text}"""
    
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, admin_text)
        except:
            pass
    
    await message.answer(
        "✅ Xabaringiz adminga yuborildi!\n"
        "Tez orada javob olasiz.",
        reply_markup=main_menu_keyboard()
    )
    await state.finish()

# ============ BOT HAQIDA ============

@dp.message_handler(text="ℹ️ Bot haqida")
async def about_bot(message: types.Message):
    """Bot haqida"""
    about_text = get_setting('about_text')
    
    if about_text:
        text = about_text
    else:
        text = """ℹ️ <b>Bot haqida</b>

🤖 Bu bot professional trader signallari kanaliga kirish uchun yaratilgan.

📌 <b>Imkoniyatlar:</b>
• Premium signallar kanaliga obuna
• Video qo'llanmalar
• 24/7 qo'llab-quvvatlash

💳 <b>To'lov:</b>
Oson va qulay to'lov tizimi

📞 Savollar uchun: /start → 📞 Aloqa"""
    
    await message.answer(text, reply_markup=main_menu_keyboard())
