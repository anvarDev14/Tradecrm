from aiogram import types
from aiogram.dispatcher import FSMContext
from datetime import datetime

from loader import dp, bot
from data.config import ADMINS
from states.states import PaymentStates
from utils.db_api.database import (
    get_active_prices, get_active_cards, get_card, get_price,
    add_payment, get_user_payments, get_subscription, get_active_channels,
    mark_channel_joined
)
from keyboards.default.keyboards import (
    main_menu_keyboard, payment_menu_keyboard, back_keyboard,
    prices_inline_keyboard, cards_inline_keyboard, confirm_payment_keyboard,
    channel_link_keyboard, cancel_keyboard
)

@dp.message_handler(text="💳 To'lov qilish")
async def payment_menu(message: types.Message):
    """To'lov menyusi"""
    await message.answer(
        "💳 <b>To'lov bo'limi</b>\n\n"
        "Quyidagi variantlardan birini tanlang:",
        reply_markup=payment_menu_keyboard()
    )

@dp.message_handler(text="💰 Yangi to'lov")
async def new_payment(message: types.Message):
    """Yangi to'lov boshlash"""
    prices = get_active_prices()
    
    if not prices:
        await message.answer(
            "❌ Hozirda narxlar mavjud emas.\n"
            "Iltimos, keyinroq urinib ko'ring.",
            reply_markup=payment_menu_keyboard()
        )
        return
    
    await message.answer(
        "📦 <b>Obuna turini tanlang:</b>\n\n"
        "Quyidagi variantlardan birini tanlang:",
        reply_markup=prices_inline_keyboard()
    )
    await PaymentStates.select_price.set()

@dp.callback_query_handler(text_startswith="select_price:", state=PaymentStates.select_price)
async def select_price(call: types.CallbackQuery, state: FSMContext):
    """Narx tanlash"""
    price_id = int(call.data.split(":")[1])
    price = get_price(price_id)
    
    if not price:
        await call.answer("❌ Narx topilmadi", show_alert=True)
        return
    
    await state.update_data(price_id=price_id, days=price['days'], amount=price['price'])
    
    cards = get_active_cards()
    
    if not cards:
        await call.message.edit_text(
            "❌ Hozirda to'lov kartalari mavjud emas.\n"
            "Iltimos, keyinroq urinib ko'ring."
        )
        await state.finish()
        return
    
    await call.message.edit_text(
        f"✅ <b>Tanlangan obuna:</b> {price['days']} kun - {price['price']:,.0f} so'm\n\n"
        "💳 <b>To'lov kartasini tanlang:</b>",
        reply_markup=cards_inline_keyboard()
    )
    await PaymentStates.select_card.set()

@dp.callback_query_handler(text_startswith="select_card:", state=PaymentStates.select_card)
async def select_card(call: types.CallbackQuery, state: FSMContext):
    """Karta tanlash"""
    card_id = int(call.data.split(":")[1])
    card = get_card(card_id)
    
    if not card:
        await call.answer("❌ Karta topilmadi", show_alert=True)
        return
    
    await state.update_data(card_id=card_id)
    data = await state.get_data()
    
    text = f"""💳 <b>To'lov ma'lumotlari:</b>

📦 Obuna: <b>{data['days']} kun</b>
💰 Narx: <b>{data['amount']:,.0f} so'm</b>

🏦 To'lov kartasi:
<code>{card['card_number']}</code>
👤 {card['card_holder'] or 'Karta egasi'}
🏛 {card['bank_name'] or 'Bank'}

⚠️ <b>Muhim:</b>
1. Yuqoridagi kartaga to'lov qiling
2. To'lov chekini (screenshot) shu yerga yuboring
3. Admin tasdiqlangandan keyin kanalga kirish havolasini olasiz

📸 To'lov chekini yuboring:"""
    
    await call.message.edit_text(text)
    await call.message.answer("📸 To'lov chekini (screenshot) yuboring:", reply_markup=cancel_keyboard())
    await PaymentStates.send_receipt.set()

@dp.message_handler(content_types=['photo'], state=PaymentStates.send_receipt)
async def receive_receipt(message: types.Message, state: FSMContext):
    """To'lov chekini qabul qilish"""
    photo_id = message.photo[-1].file_id
    
    data = await state.get_data()
    user_id = message.from_user.id
    
    # To'lovni bazaga qo'shish
    payment_id = add_payment(
        user_id=user_id,
        amount=data['amount'],
        receipt_photo=photo_id,
        card_id=data['card_id'],
        subscription_days=data['days']
    )
    
    await state.finish()
    
    await message.answer(
        f"""✅ <b>To'lov so'rovi yuborildi!</b>

📋 To'lov ID: <code>#{payment_id}</code>
💰 Summa: {data['amount']:,.0f} so'm
📅 Obuna: {data['days']} kun

⏳ Admin tomonidan tekshirilmoqda...
Tasdiqlangandan keyin sizga xabar beriladi.

🏠 Asosiy menyuga qaytish:""",
        reply_markup=main_menu_keyboard()
    )
    
    # Adminlarga xabar yuborish
    from utils.db_api.database import get_user
    user = get_user(user_id)
    
    admin_text = f"""🆕 <b>Yangi to'lov so'rovi!</b>

👤 Foydalanuvchi: {message.from_user.full_name}
🆔 ID: <code>{user_id}</code>
📱 Username: @{message.from_user.username or 'yoq'}

💰 Summa: {data['amount']:,.0f} so'm
📅 Obuna: {data['days']} kun
📋 To'lov ID: <code>#{payment_id}</code>

⬇️ To'lov cheki quyida:"""
    
    from keyboards.default.keyboards import payment_action_keyboard
    
    for admin_id in ADMINS:
        try:
            await bot.send_message(admin_id, admin_text)
            await bot.send_photo(
                admin_id, 
                photo_id,
                reply_markup=payment_action_keyboard(payment_id)
            )
        except Exception as e:
            print(f"Admin {admin_id} ga xabar yuborishda xato: {e}")

@dp.message_handler(state=PaymentStates.send_receipt)
async def wrong_receipt_format(message: types.Message):
    """Noto'g'ri format"""
    await message.answer(
        "❌ Iltimos, to'lov chekining <b>rasmini</b> yuboring.\n"
        "📸 Faqat rasm qabul qilinadi.",
        reply_markup=cancel_keyboard()
    )

@dp.message_handler(text="📋 To'lovlarim tarixi")
async def payment_history(message: types.Message):
    """To'lovlar tarixi"""
    user_id = message.from_user.id
    payments = get_user_payments(user_id)
    
    if not payments:
        await message.answer(
            "📋 Sizda hali to'lovlar mavjud emas.",
            reply_markup=payment_menu_keyboard()
        )
        return
    
    text = "📋 <b>To'lovlarim tarixi:</b>\n\n"
    
    status_emoji = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌'
    }
    
    status_text = {
        'pending': 'Kutilmoqda',
        'approved': 'Tasdiqlangan',
        'rejected': 'Rad etilgan'
    }
    
    for payment in payments[:10]:  # Oxirgi 10 ta
        emoji = status_emoji.get(payment['status'], '❓')
        status = status_text.get(payment['status'], 'Noma\'lum')
        date = payment['created_at'][:10] if payment['created_at'] else '-'
        
        text += f"{emoji} #{payment['id']} | {payment['amount']:,.0f} so'm | {status} | {date}\n"
    
    await message.answer(text, reply_markup=payment_menu_keyboard())

@dp.message_handler(text="📊 Obuna holati")
async def subscription_status(message: types.Message):
    """Obuna holati"""
    user_id = message.from_user.id
    subscription = get_subscription(user_id)
    
    if not subscription or not subscription['is_active']:
        await message.answer(
            "❌ <b>Sizda faol obuna yo'q</b>\n\n"
            "Obuna bo'lish uchun 💳 To'lov qilish tugmasini bosing.",
            reply_markup=main_menu_keyboard()
        )
        return
    
    expires_at = subscription['expires_at']
    if expires_at:
        expires_date = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
        days_left = (expires_date - datetime.now()).days
        expires_text = expires_at[:10]
    else:
        days_left = 0
        expires_text = '-'
    
    if days_left < 0:
        status_text = "⚠️ Muddati o'tgan"
    elif days_left <= 3:
        status_text = f"⚠️ {days_left} kun qoldi"
    else:
        status_text = f"✅ {days_left} kun qoldi"
    
    text = f"""📊 <b>Obuna holati</b>

✅ Status: <b>Faol</b>
📅 Tugash sanasi: <b>{expires_text}</b>
⏳ Qolgan vaqt: <b>{status_text}</b>

"""
    
    # Kanal havolasini ko'rsatish
    if subscription['channel_joined']:
        text += "🔗 Siz allaqachon kanalga qo'shilgansiz."
    else:
        channels = get_active_channels()
        if channels:
            text += "🔗 Premium kanalga qo'shilish:"
            keyboard = channel_link_keyboard(channels[0]['invite_link'])
            await message.answer(text, reply_markup=keyboard)
            return
    
    await message.answer(text, reply_markup=main_menu_keyboard())

@dp.callback_query_handler(text="renew_subscription")
async def renew_subscription(call: types.CallbackQuery):
    """Obunani yangilash"""
    await call.message.edit_text("🔄 Obunani yangilash uchun to'lov qiling:")
    await new_payment(call.message)

@dp.callback_query_handler(text="subscribe_for_videos")
async def subscribe_for_videos(call: types.CallbackQuery):
    """Videolar uchun obuna"""
    await call.answer("Premium videolar uchun obuna bo'ling!", show_alert=True)
    await new_payment(call.message)

@dp.callback_query_handler(text="cancel_payment", state="*")
async def cancel_payment(call: types.CallbackQuery, state: FSMContext):
    """To'lovni bekor qilish"""
    await state.finish()
    await call.message.edit_text("❌ To'lov bekor qilindi.")
    await call.message.answer("🏠 Asosiy menyu:", reply_markup=main_menu_keyboard())
