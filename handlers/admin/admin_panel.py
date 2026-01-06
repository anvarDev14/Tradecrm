from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from datetime import datetime

from loader import dp, bot
from data.config import ADMINS
from states.states import AdminPaymentStates, AdminNotifyStates
from utils.db_api.database import (
    get_statistics, get_pending_payments, get_payment, approve_payment,
    reject_payment, get_all_payments, get_user, get_active_channels,
    get_subscription, mark_channel_joined, get_expiring_subscriptions,
    get_expired_subscriptions, get_active_subscriptions, deactivate_subscription,
    update_last_notified, get_connection
)
from keyboards.default.keyboards import (
    admin_menu_keyboard, admin_payments_keyboard, admin_subscriptions_keyboard,
    payment_action_keyboard, subscription_action_keyboard, channel_link_keyboard,
    confirm_action_keyboard, admin_broadcast_keyboard
)


# Admin filteri
def is_admin(user_id):
    return str(user_id) in ADMINS


# ============ ADMIN PANEL ============

@dp.message_handler(text="📊 Statistika")
async def admin_statistics(message: types.Message):
    """Statistika"""
    if not is_admin(message.from_user.id):
        return

    stats = get_statistics()

    text = f"""📊 <b>Statistika</b>

👥 <b>Foydalanuvchilar:</b>
├ Jami: {stats['total_users']}
└ Bugun: {stats['today_users']}

📅 <b>Obunalar:</b>
├ Faol: {stats['active_subscriptions']}
└ Tugayotgan (3 kun): {stats['expiring_soon']}

💳 <b>To'lovlar:</b>
├ Kutayotgan: {stats['pending_payments']}
└ Tasdiqlangan: {stats['approved_payments']}

💰 <b>Daromad:</b>
├ Jami: {stats['total_revenue']:,.0f} so'm
└ Bu oy: {stats['month_revenue']:,.0f} so'm"""

    await message.answer(text, reply_markup=admin_menu_keyboard())


# ============ TO'LOVLAR BOSHQARUVI ============

@dp.message_handler(text="💳 To'lovlar")
async def admin_payments_menu(message: types.Message):
    """To'lovlar menyusi"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "💳 <b>To'lovlar boshqaruvi</b>",
        reply_markup=admin_payments_keyboard()
    )


@dp.message_handler(text="⏳ Kutayotgan to'lovlar")
async def pending_payments(message: types.Message):
    """Kutayotgan to'lovlar"""
    if not is_admin(message.from_user.id):
        return

    payments = get_pending_payments()

    if not payments:
        await message.answer(
            "✅ Kutayotgan to'lovlar yo'q",
            reply_markup=admin_payments_keyboard()
        )
        return

    await message.answer(f"⏳ <b>Kutayotgan to'lovlar:</b> {len(payments)} ta")

    for payment in payments[:20]:
        text = f"""📋 <b>To'lov #{payment['id']}</b>

👤 {payment['full_name']}
🆔 <code>{payment['user_id']}</code>
📱 @{payment['username'] or 'yoq'}
💰 {payment['amount']:,.0f} so'm
📅 {payment['subscription_days']} kun
🕐 {payment['created_at'][:16] if payment['created_at'] else '-'}"""

        if payment['receipt_photo']:
            await bot.send_photo(
                message.from_user.id,
                payment['receipt_photo'],
                caption=text,
                reply_markup=payment_action_keyboard(payment['id'])
            )
        else:
            await message.answer(text, reply_markup=payment_action_keyboard(payment['id']))


@dp.message_handler(text="📋 Barcha to'lovlar")
async def all_payments(message: types.Message):
    """Barcha to'lovlar"""
    if not is_admin(message.from_user.id):
        return

    payments = get_all_payments(50)

    if not payments:
        await message.answer("📋 To'lovlar yo'q", reply_markup=admin_payments_keyboard())
        return

    status_emoji = {
        'pending': '⏳',
        'approved': '✅',
        'rejected': '❌'
    }

    text = "📋 <b>Oxirgi 50 ta to'lov:</b>\n\n"

    for payment in payments:
        emoji = status_emoji.get(payment['status'], '❓')
        date = payment['created_at'][:10] if payment['created_at'] else '-'
        text += f"{emoji} #{payment['id']} | {payment['full_name'][:15]} | {payment['amount']:,.0f} | {date}\n"

    await message.answer(text, reply_markup=admin_payments_keyboard())


@dp.message_handler(text="✅ Tasdiqlangan to'lovlar")
async def approved_payments(message: types.Message):
    """Tasdiqlangan to'lovlar"""
    if not is_admin(message.from_user.id):
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.full_name 
        FROM payments p 
        JOIN users u ON p.user_id = u.user_id 
        WHERE p.status = 'approved'
        ORDER BY p.approved_at DESC
        LIMIT 30
    ''')
    payments = cursor.fetchall()
    conn.close()

    if not payments:
        await message.answer("✅ Tasdiqlangan to'lovlar yo'q", reply_markup=admin_payments_keyboard())
        return

    text = "✅ <b>Tasdiqlangan to'lovlar:</b>\n\n"

    for payment in payments:
        date = payment['approved_at'][:10] if payment['approved_at'] else '-'
        text += f"#{payment['id']} | {payment['full_name'][:15]} | {payment['amount']:,.0f} | {date}\n"

    await message.answer(text, reply_markup=admin_payments_keyboard())


@dp.message_handler(text="❌ Rad etilgan to'lovlar")
async def rejected_payments(message: types.Message):
    """Rad etilgan to'lovlar"""
    if not is_admin(message.from_user.id):
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.full_name 
        FROM payments p 
        JOIN users u ON p.user_id = u.user_id 
        WHERE p.status = 'rejected'
        ORDER BY p.created_at DESC
        LIMIT 30
    ''')
    payments = cursor.fetchall()
    conn.close()

    if not payments:
        await message.answer("❌ Rad etilgan to'lovlar yo'q", reply_markup=admin_payments_keyboard())
        return

    text = "❌ <b>Rad etilgan to'lovlar:</b>\n\n"

    for payment in payments:
        date = payment['created_at'][:10] if payment['created_at'] else '-'
        note = f" ({payment['admin_note'][:20]}...)" if payment['admin_note'] else ""
        text += f"#{payment['id']} | {payment['full_name'][:15]} | {payment['amount']:,.0f} | {date}{note}\n"

    await message.answer(text, reply_markup=admin_payments_keyboard())


# ============ TO'LOV CALLBACK'LARI ============

@dp.callback_query_handler(text_startswith="approve_payment:")
async def approve_payment_callback(call: types.CallbackQuery):
    """To'lovni tasdiqlash"""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda ruxsat yo'q", show_alert=True)
        return

    payment_id = int(call.data.split(":")[1])
    payment = approve_payment(payment_id)

    if not payment:
        await call.answer("❌ To'lov topilmadi", show_alert=True)
        return

    user_id = payment['user_id']

    # Caption None bo'lishi mumkin
    current_caption = call.message.caption or ""
    await call.message.edit_caption(
        current_caption + "\n\n✅ <b>TASDIQLANDI</b>",
        reply_markup=None
    )

    # Foydalanuvchiga xabar yuborish
    channels = get_active_channels()

    user_text = f"""🎉 <b>To'lovingiz tasdiqlandi!</b>

📋 To'lov ID: #{payment_id}
💰 Summa: {payment['amount']:,.0f} so'm
📅 Obuna: {payment['subscription_days']} kun

"""

    if channels:
        user_text += "🔗 Quyidagi tugma orqali maxsus kanalga qo'shiling:"
        keyboard = channel_link_keyboard(channels[0]['invite_link'])
    else:
        user_text += "⚠️ Kanal havolasi hali qo'shilmagan. Admin bilan bog'laning."
        keyboard = None

    try:
        await bot.send_message(user_id, user_text, reply_markup=keyboard)
        await call.answer("✅ To'lov tasdiqlandi va foydalanuvchiga xabar yuborildi")
    except Exception as e:
        await call.answer(f"✅ Tasdiqlandi, lekin xabar yuborishda xato: {e}", show_alert=True)


@dp.callback_query_handler(text_startswith="reject_payment:")
async def reject_payment_start(call: types.CallbackQuery, state: FSMContext):
    """To'lovni rad etish - sabab so'rash"""
    if not is_admin(call.from_user.id):
        await call.answer("⛔ Sizda ruxsat yo'q", show_alert=True)
        return

    payment_id = int(call.data.split(":")[1])

    await state.update_data(payment_id=payment_id)
    await call.message.answer(
        "❌ <b>Rad etish sababi:</b>\n\n"
        "Sabab kiriting yoki 'skip' yozing:"
    )
    await AdminPaymentStates.enter_reject_reason.set()
    await call.answer()


@dp.message_handler(state=AdminPaymentStates.enter_reject_reason)
async def reject_payment_reason(message: types.Message, state: FSMContext):
    """Rad etish sababini qabul qilish"""
    data = await state.get_data()
    payment_id = data['payment_id']

    reason = None if message.text.lower() == 'skip' else message.text

    payment = get_payment(payment_id)
    reject_payment(payment_id, reason)

    await state.finish()

    # Foydalanuvchiga xabar yuborish
    user_text = f"""❌ <b>To'lovingiz rad etildi</b>

📋 To'lov ID: #{payment_id}
"""
    if reason:
        user_text += f"\n📝 Sabab: {reason}"

    user_text += "\n\nIltimos, to'lov ma'lumotlarini tekshiring va qaytadan urinib ko'ring."

    try:
        await bot.send_message(payment['user_id'], user_text)
        await message.answer("❌ To'lov rad etildi va foydalanuvchiga xabar yuborildi",
                             reply_markup=admin_payments_keyboard())
    except:
        await message.answer("❌ To'lov rad etildi, lekin xabar yuborishda xato", reply_markup=admin_payments_keyboard())


@dp.callback_query_handler(text_startswith="view_user_payment:")
async def view_user_from_payment(call: types.CallbackQuery):
    """To'lovdan foydalanuvchini ko'rish"""
    if not is_admin(call.from_user.id):
        return

    payment_id = int(call.data.split(":")[1])
    payment = get_payment(payment_id)

    if not payment:
        await call.answer("❌ Topilmadi", show_alert=True)
        return

    user = get_user(payment['user_id'])
    subscription = get_subscription(payment['user_id'])

    sub_status = "✅ Faol" if subscription and subscription['is_active'] else "❌ Faol emas"

    text = f"""👤 <b>Foydalanuvchi ma'lumotlari:</b>

🆔 ID: <code>{payment['user_id']}</code>
👤 Ism: {user['full_name'] if user else '-'}
📱 Username: @{user['username'] or 'yoq' if user else '-'}
📞 Telefon: {user['phone'] or 'yoq' if user else '-'}
📅 Ro'yxatdan: {user['registered_at'][:10] if user and user['registered_at'] else '-'}

📊 Obuna: {sub_status}"""

    await call.message.answer(text)
    await call.answer()


# ============ OBUNALAR BOSHQARUVI ============

@dp.message_handler(text="📅 Obunalar")
async def admin_subscriptions_menu(message: types.Message):
    """Obunalar menyusi"""
    if not is_admin(message.from_user.id):
        return

    await message.answer(
        "📅 <b>Obunalar boshqaruvi</b>",
        reply_markup=admin_subscriptions_keyboard()
    )


@dp.message_handler(text="✅ Faol obunalar")
async def active_subscriptions(message: types.Message):
    """Faol obunalar"""
    if not is_admin(message.from_user.id):
        return

    subs = get_active_subscriptions()

    if not subs:
        await message.answer("✅ Faol obunalar yo'q", reply_markup=admin_subscriptions_keyboard())
        return

    text = f"✅ <b>Faol obunalar:</b> {len(subs)} ta\n\n"

    for sub in subs[:30]:
        expires = sub['expires_at'][:10] if sub['expires_at'] else '-'
        text += f"👤 {sub['full_name'][:15]} | Tugashi: {expires}\n"

    await message.answer(text, reply_markup=admin_subscriptions_keyboard())


@dp.message_handler(text="⚠️ Tugayotgan obunalar")
async def expiring_subscriptions(message: types.Message):
    """Tugayotgan obunalar"""
    if not is_admin(message.from_user.id):
        return

    subs = get_expiring_subscriptions(3)

    if not subs:
        await message.answer("⚠️ 3 kun ichida tugaydigan obunalar yo'q", reply_markup=admin_subscriptions_keyboard())
        return

    await message.answer(f"⚠️ <b>3 kun ichida tugaydigan obunalar:</b> {len(subs)} ta")

    for sub in subs:
        expires = sub['expires_at'][:10] if sub['expires_at'] else '-'
        text = f"""⚠️ <b>Obuna tugayapti!</b>

👤 {sub['full_name']}
🆔 <code>{sub['user_id']}</code>
📱 @{sub['username'] or 'yoq'}
📅 Tugashi: {expires}"""

        await message.answer(text, reply_markup=subscription_action_keyboard(sub['user_id']))


@dp.message_handler(text="❌ O'tgan obunalar")
async def expired_subscriptions(message: types.Message):
    """O'tgan obunalar"""
    if not is_admin(message.from_user.id):
        return

    subs = get_expired_subscriptions()

    if not subs:
        await message.answer("❌ Muddati o'tgan obunalar yo'q", reply_markup=admin_subscriptions_keyboard())
        return

    await message.answer(f"❌ <b>Muddati o'tgan obunalar:</b> {len(subs)} ta")

    for sub in subs[:20]:
        expires = sub['expires_at'][:10] if sub['expires_at'] else '-'
        text = f"""❌ <b>Obuna tugagan!</b>

👤 {sub['full_name']}
🆔 <code>{sub['user_id']}</code>
📅 Tugagan: {expires}"""

        await message.answer(text, reply_markup=subscription_action_keyboard(sub['user_id']))


@dp.message_handler(text="📋 Barcha obunalar")
async def all_subscriptions(message: types.Message):
    """Barcha obunalar tarixi"""
    if not is_admin(message.from_user.id):
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, u.full_name, u.username 
        FROM subscriptions s 
        JOIN users u ON s.user_id = u.user_id 
        ORDER BY s.expires_at DESC 
        LIMIT 50
    ''')
    subs = cursor.fetchall()
    conn.close()

    if not subs:
        await message.answer("📋 Obunalar yo'q", reply_markup=admin_subscriptions_keyboard())
        return

    text = f"📋 <b>Barcha obunalar:</b> {len(subs)} ta\n\n"

    for sub in subs:
        status = "✅" if sub['is_active'] else "❌"
        expires = sub['expires_at'][:10] if sub['expires_at'] else '-'
        name = sub['full_name'][:15] if sub['full_name'] else '-'
        text += f"{status} {name} | {expires}\n"

    await message.answer(text, reply_markup=admin_subscriptions_keyboard())


@dp.callback_query_handler(text_startswith="notify_user:")
async def notify_user_start(call: types.CallbackQuery, state: FSMContext):
    """Foydalanuvchiga xabar yuborish"""
    if not is_admin(call.from_user.id):
        return

    user_id = int(call.data.split(":")[1])
    await state.update_data(notify_user_id=user_id)

    await call.message.answer("💬 Foydalanuvchiga yuboriladigan xabarni kiriting:")
    await AdminNotifyStates.enter_message.set()
    await call.answer()


@dp.message_handler(state=AdminNotifyStates.enter_message)
async def notify_user_send(message: types.Message, state: FSMContext):
    """Xabarni yuborish"""
    data = await state.get_data()
    user_id = data['notify_user_id']

    try:
        await bot.send_message(user_id, message.text)
        await message.answer("✅ Xabar yuborildi!", reply_markup=admin_subscriptions_keyboard())
    except Exception as e:
        await message.answer(f"❌ Xabar yuborishda xato: {e}", reply_markup=admin_subscriptions_keyboard())

    await state.finish()


@dp.callback_query_handler(text_startswith="deactivate_sub:")
async def deactivate_subscription_callback(call: types.CallbackQuery):
    """Obunani o'chirish"""
    if not is_admin(call.from_user.id):
        return

    user_id = int(call.data.split(":")[1])
    deactivate_subscription(user_id)

    await call.message.edit_text(
        call.message.text + "\n\n❌ <b>Obuna o'chirildi</b>"
    )
    await call.answer("Obuna o'chirildi")


# ============ REKLAMA TARIXI ============

@dp.message_handler(text="📊 Reklama tarixi")
async def broadcast_history(message: types.Message):
    """Reklama tarixi"""
    if not is_admin(message.from_user.id):
        return

    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM broadcasts 
        ORDER BY created_at DESC 
        LIMIT 20
    ''')
    broadcasts = cursor.fetchall()
    conn.close()

    if not broadcasts:
        await message.answer("📊 Reklama tarixi bo'sh", reply_markup=admin_broadcast_keyboard())
        return

    target_names = {
        'all': '👥 Barchaga',
        'subscribers': '✅ Obunadorlar',
        'non_subscribers': '❌ Obunasizlar'
    }

    text = "📊 <b>Oxirgi 20 ta reklama:</b>\n\n"

    for b in broadcasts:
        date = b['created_at'][:16] if b['created_at'] else '-'
        target = target_names.get(b['target'], b['target'])
        success = b['success_count'] or 0
        fail = b['fail_count'] or 0
        text += f"📅 {date}\n   {target} | ✅{success} ❌{fail}\n\n"

    await message.answer(text, reply_markup=admin_broadcast_keyboard())