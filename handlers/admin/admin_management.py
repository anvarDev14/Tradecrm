from aiogram import types
from aiogram.dispatcher import FSMContext

from loader import dp, bot
from data.config import ADMINS
from states.states import (
    AdminCardStates, AdminChannelStates, AdminVideoStates, AdminPriceStates
)
from utils.db_api.database import (
    add_card, get_all_cards, get_card, toggle_card, delete_card,
    add_channel, get_all_channels, get_channel, toggle_channel, delete_channel,
    update_channel_link, add_video, get_all_videos, get_video, delete_video,
    toggle_video_free, add_price, get_all_prices, get_price, delete_price,
    toggle_price
)
from keyboards.default.keyboards import (
    admin_menu_keyboard, admin_cards_keyboard, admin_channels_keyboard,
    admin_videos_keyboard, admin_prices_keyboard, cancel_keyboard,
    card_action_keyboard, channel_action_keyboard, video_action_keyboard,
    price_action_keyboard
)

def is_admin(user_id):
    return str(user_id) in ADMINS

# ============ KARTALAR BOSHQARUVI ============

@dp.message_handler(text="💰 Kartalar")
async def admin_cards_menu(message: types.Message):
    """Kartalar menyusi"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "💰 <b>Kartalar boshqaruvi</b>",
        reply_markup=admin_cards_keyboard()
    )

@dp.message_handler(text="➕ Karta qo'shish")
async def add_card_start(message: types.Message, state: FSMContext):
    """Karta qo'shish"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "💳 <b>Yangi karta qo'shish</b>\n\n"
        "Karta raqamini kiriting (16 ta raqam):",
        reply_markup=cancel_keyboard()
    )
    await AdminCardStates.enter_card_number.set()

@dp.message_handler(state=AdminCardStates.enter_card_number)
async def enter_card_number(message: types.Message, state: FSMContext):
    """Karta raqamini qabul qilish"""
    card_number = message.text.replace(" ", "")
    
    if not card_number.isdigit() or len(card_number) != 16:
        await message.answer("❌ Noto'g'ri format. 16 ta raqam kiriting:")
        return
    
    # Formatlash: XXXX XXXX XXXX XXXX
    formatted = " ".join([card_number[i:i+4] for i in range(0, 16, 4)])
    
    await state.update_data(card_number=formatted)
    await message.answer("👤 Karta egasining ismini kiriting (yoki 'skip'):")
    await AdminCardStates.enter_card_holder.set()

@dp.message_handler(state=AdminCardStates.enter_card_holder)
async def enter_card_holder(message: types.Message, state: FSMContext):
    """Karta egasini qabul qilish"""
    holder = None if message.text.lower() == 'skip' else message.text
    
    await state.update_data(card_holder=holder)
    await message.answer("🏦 Bank nomini kiriting (yoki 'skip'):")
    await AdminCardStates.enter_bank_name.set()

@dp.message_handler(state=AdminCardStates.enter_bank_name)
async def enter_bank_name(message: types.Message, state: FSMContext):
    """Bank nomini qabul qilish"""
    bank = None if message.text.lower() == 'skip' else message.text
    
    data = await state.get_data()
    
    card_id = add_card(
        card_number=data['card_number'],
        card_holder=data['card_holder'],
        bank_name=bank
    )
    
    await state.finish()
    
    await message.answer(
        f"""✅ <b>Karta qo'shildi!</b>

💳 Raqam: <code>{data['card_number']}</code>
👤 Egasi: {data['card_holder'] or '-'}
🏦 Bank: {bank or '-'}
🆔 ID: {card_id}""",
        reply_markup=admin_cards_keyboard()
    )

@dp.message_handler(text="📋 Barcha kartalar")
async def all_cards(message: types.Message):
    """Barcha kartalar"""
    if not is_admin(message.from_user.id):
        return
    
    cards = get_all_cards()
    
    if not cards:
        await message.answer("💳 Kartalar yo'q", reply_markup=admin_cards_keyboard())
        return
    
    for card in cards:
        status = "🟢 Faol" if card['is_active'] else "🔴 O'chirilgan"
        text = f"""💳 <b>Karta #{card['id']}</b>

📝 Raqam: <code>{card['card_number']}</code>
👤 Egasi: {card['card_holder'] or '-'}
🏦 Bank: {card['bank_name'] or '-'}
📊 Status: {status}"""
        
        await message.answer(text, reply_markup=card_action_keyboard(card['id'], card['is_active']))

@dp.callback_query_handler(text_startswith="toggle_card:")
async def toggle_card_callback(call: types.CallbackQuery):
    """Karta holatini o'zgartirish"""
    if not is_admin(call.from_user.id):
        return
    
    card_id = int(call.data.split(":")[1])
    toggle_card(card_id)
    
    card = get_card(card_id)
    status = "🟢 Faol" if card['is_active'] else "🔴 O'chirilgan"
    
    await call.message.edit_text(
        f"""💳 <b>Karta #{card['id']}</b>

📝 Raqam: <code>{card['card_number']}</code>
👤 Egasi: {card['card_holder'] or '-'}
🏦 Bank: {card['bank_name'] or '-'}
📊 Status: {status}""",
        reply_markup=card_action_keyboard(card['id'], card['is_active'])
    )
    await call.answer("✅ Status o'zgartirildi")

@dp.callback_query_handler(text_startswith="delete_card:")
async def delete_card_callback(call: types.CallbackQuery):
    """Kartani o'chirish"""
    if not is_admin(call.from_user.id):
        return
    
    card_id = int(call.data.split(":")[1])
    delete_card(card_id)
    
    await call.message.edit_text("🗑 Karta o'chirildi!")
    await call.answer()

# ============ KANALLAR BOSHQARUVI ============

@dp.message_handler(text="📺 Kanallar")
async def admin_channels_menu(message: types.Message):
    """Kanallar menyusi"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📺 <b>Kanallar boshqaruvi</b>",
        reply_markup=admin_channels_keyboard()
    )

@dp.message_handler(text="➕ Kanal qo'shish")
async def add_channel_start(message: types.Message, state: FSMContext):
    """Kanal qo'shish"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "📺 <b>Yangi kanal qo'shish</b>\n\n"
        "Kanal ID'sini kiriting (masalan: -1001234567890):",
        reply_markup=cancel_keyboard()
    )
    await AdminChannelStates.enter_channel_id.set()

@dp.message_handler(state=AdminChannelStates.enter_channel_id)
async def enter_channel_id(message: types.Message, state: FSMContext):
    """Kanal ID qabul qilish"""
    await state.update_data(channel_id=message.text)
    await message.answer("📝 Kanal nomini kiriting:")
    await AdminChannelStates.enter_channel_name.set()

@dp.message_handler(state=AdminChannelStates.enter_channel_name)
async def enter_channel_name(message: types.Message, state: FSMContext):
    """Kanal nomini qabul qilish"""
    await state.update_data(channel_name=message.text)
    await message.answer("🔗 Kanal havolasini kiriting (invite link):")
    await AdminChannelStates.enter_invite_link.set()

@dp.message_handler(state=AdminChannelStates.enter_invite_link)
async def enter_invite_link(message: types.Message, state: FSMContext):
    """Kanal havolasini qabul qilish"""
    data = await state.get_data()
    
    add_channel(
        channel_id=data['channel_id'],
        channel_name=data['channel_name'],
        invite_link=message.text
    )
    
    await state.finish()
    
    await message.answer(
        f"""✅ <b>Kanal qo'shildi!</b>

📺 Nom: {data['channel_name']}
🆔 ID: {data['channel_id']}
🔗 Havola: {message.text}""",
        reply_markup=admin_channels_keyboard()
    )

@dp.message_handler(text="📋 Barcha kanallar")
async def all_channels(message: types.Message):
    """Barcha kanallar"""
    if not is_admin(message.from_user.id):
        return
    
    channels = get_all_channels()
    
    if not channels:
        await message.answer("📺 Kanallar yo'q", reply_markup=admin_channels_keyboard())
        return
    
    for channel in channels:
        status = "🟢 Faol" if channel['is_active'] else "🔴 O'chirilgan"
        text = f"""📺 <b>{channel['channel_name']}</b>

🆔 ID: <code>{channel['channel_id']}</code>
🔗 Havola: {channel['invite_link']}
📊 Status: {status}"""
        
        await message.answer(text, reply_markup=channel_action_keyboard(channel['id'], channel['is_active']))

@dp.callback_query_handler(text_startswith="toggle_channel:")
async def toggle_channel_callback(call: types.CallbackQuery):
    """Kanal holatini o'zgartirish"""
    if not is_admin(call.from_user.id):
        return
    
    channel_id = int(call.data.split(":")[1])
    toggle_channel(channel_id)
    
    channel = get_channel(channel_id)
    status = "🟢 Faol" if channel['is_active'] else "🔴 O'chirilgan"
    
    await call.message.edit_text(
        f"""📺 <b>{channel['channel_name']}</b>

🆔 ID: <code>{channel['channel_id']}</code>
🔗 Havola: {channel['invite_link']}
📊 Status: {status}""",
        reply_markup=channel_action_keyboard(channel['id'], channel['is_active'])
    )
    await call.answer("✅ Status o'zgartirildi")

@dp.callback_query_handler(text_startswith="edit_channel_link:")
async def edit_channel_link_start(call: types.CallbackQuery, state: FSMContext):
    """Kanal havolasini tahrirlash"""
    if not is_admin(call.from_user.id):
        return
    
    channel_id = int(call.data.split(":")[1])
    await state.update_data(edit_channel_id=channel_id)
    
    await call.message.answer("🔗 Yangi havolani kiriting:")
    await AdminChannelStates.edit_invite_link.set()
    await call.answer()

@dp.message_handler(state=AdminChannelStates.edit_invite_link)
async def edit_channel_link_save(message: types.Message, state: FSMContext):
    """Yangi havolani saqlash"""
    data = await state.get_data()
    channel_id = data['edit_channel_id']
    
    update_channel_link(channel_id, message.text)
    await state.finish()
    
    await message.answer("✅ Havola yangilandi!", reply_markup=admin_channels_keyboard())

@dp.callback_query_handler(text_startswith="delete_channel:")
async def delete_channel_callback(call: types.CallbackQuery):
    """Kanalni o'chirish"""
    if not is_admin(call.from_user.id):
        return
    
    channel_id = int(call.data.split(":")[1])
    delete_channel(channel_id)
    
    await call.message.edit_text("🗑 Kanal o'chirildi!")
    await call.answer()

# ============ VIDEOLAR BOSHQARUVI ============

@dp.message_handler(text="🎬 Videolar")
async def admin_videos_menu(message: types.Message):
    """Videolar menyusi"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🎬 <b>Videolar boshqaruvi</b>",
        reply_markup=admin_videos_keyboard()
    )

@dp.message_handler(text="➕ Video qo'shish")
async def add_video_start(message: types.Message, state: FSMContext):
    """Video qo'shish"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "🎬 <b>Yangi video qo'shish</b>\n\n"
        "Videoni yuboring:",
        reply_markup=cancel_keyboard()
    )
    await AdminVideoStates.send_video.set()

@dp.message_handler(content_types=['video'], state=AdminVideoStates.send_video)
async def receive_video(message: types.Message, state: FSMContext):
    """Videoni qabul qilish"""
    video_id = message.video.file_id
    
    await state.update_data(file_id=video_id)
    await message.answer("📝 Video nomini kiriting:")
    await AdminVideoStates.enter_video_name.set()

@dp.message_handler(state=AdminVideoStates.send_video)
async def wrong_video_format(message: types.Message):
    """Noto'g'ri format"""
    await message.answer("❌ Iltimos, video yuboring!")

@dp.message_handler(state=AdminVideoStates.enter_video_name)
async def enter_video_name(message: types.Message, state: FSMContext):
    """Video nomini qabul qilish"""
    await state.update_data(video_name=message.text)
    await message.answer("📄 Video tavsifini kiriting (yoki 'skip'):")
    await AdminVideoStates.enter_video_description.set()

@dp.message_handler(state=AdminVideoStates.enter_video_description)
async def enter_video_description(message: types.Message, state: FSMContext):
    """Video tavsifini qabul qilish"""
    description = None if message.text.lower() == 'skip' else message.text
    
    await state.update_data(description=description)
    
    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
    keyboard = InlineKeyboardMarkup()
    keyboard.add(
        InlineKeyboardButton("🆓 Bepul", callback_data="video_type:free"),
        InlineKeyboardButton("💰 Premium", callback_data="video_type:premium")
    )
    
    await message.answer("📊 Video turini tanlang:", reply_markup=keyboard)
    await AdminVideoStates.select_video_type.set()

@dp.callback_query_handler(text_startswith="video_type:", state=AdminVideoStates.select_video_type)
async def select_video_type(call: types.CallbackQuery, state: FSMContext):
    """Video turini tanlash"""
    video_type = call.data.split(":")[1]
    is_free = 1 if video_type == 'free' else 0
    
    data = await state.get_data()
    
    video_id = add_video(
        name=data['video_name'],
        file_id=data['file_id'],
        description=data['description'],
        is_free=is_free
    )
    
    await state.finish()
    
    type_text = "🆓 Bepul" if is_free else "💰 Premium"
    
    await call.message.edit_text(
        f"""✅ <b>Video qo'shildi!</b>

📹 Nom: {data['video_name']}
📄 Tavsif: {data['description'] or '-'}
📊 Turi: {type_text}
🆔 ID: {video_id}"""
    )
    await call.message.answer("🎬 Videolar menyusi:", reply_markup=admin_videos_keyboard())

@dp.message_handler(text="📋 Barcha videolar")
async def all_videos(message: types.Message):
    """Barcha videolar"""
    if not is_admin(message.from_user.id):
        return
    
    videos = get_all_videos()
    
    if not videos:
        await message.answer("🎬 Videolar yo'q", reply_markup=admin_videos_keyboard())
        return
    
    for video in videos:
        type_text = "🆓 Bepul" if video['is_free'] else "💰 Premium"
        text = f"""🎬 <b>{video['name']}</b>

📄 Tavsif: {video['description'] or '-'}
📊 Turi: {type_text}
🆔 ID: {video['id']}"""
        
        await message.answer(text, reply_markup=video_action_keyboard(video['id'], video['is_free']))

@dp.callback_query_handler(text_startswith="toggle_video_free:")
async def toggle_video_free_callback(call: types.CallbackQuery):
    """Video turini o'zgartirish"""
    if not is_admin(call.from_user.id):
        return
    
    video_id = int(call.data.split(":")[1])
    toggle_video_free(video_id)
    
    video = get_video(video_id)
    type_text = "🆓 Bepul" if video['is_free'] else "💰 Premium"
    
    await call.message.edit_text(
        f"""🎬 <b>{video['name']}</b>

📄 Tavsif: {video['description'] or '-'}
📊 Turi: {type_text}
🆔 ID: {video['id']}""",
        reply_markup=video_action_keyboard(video['id'], video['is_free'])
    )
    await call.answer("✅ Turi o'zgartirildi")

@dp.callback_query_handler(text_startswith="preview_video:")
async def preview_video(call: types.CallbackQuery):
    """Videoni ko'rish"""
    if not is_admin(call.from_user.id):
        return
    
    video_id = int(call.data.split(":")[1])
    video = get_video(video_id)
    
    if video:
        await bot.send_video(call.from_user.id, video['file_id'], caption=f"📹 {video['name']}")
    await call.answer()

@dp.callback_query_handler(text_startswith="delete_video:")
async def delete_video_callback(call: types.CallbackQuery):
    """Videoni o'chirish"""
    if not is_admin(call.from_user.id):
        return
    
    video_id = int(call.data.split(":")[1])
    delete_video(video_id)
    
    await call.message.edit_text("🗑 Video o'chirildi!")
    await call.answer()

# ============ NARXLAR BOSHQARUVI ============

@dp.message_handler(text="💵 Narxlar")
async def admin_prices_menu(message: types.Message):
    """Narxlar menyusi"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "💵 <b>Narxlar boshqaruvi</b>",
        reply_markup=admin_prices_keyboard()
    )

@dp.message_handler(text="➕ Narx qo'shish")
async def add_price_start(message: types.Message, state: FSMContext):
    """Narx qo'shish"""
    if not is_admin(message.from_user.id):
        return
    
    await message.answer(
        "💵 <b>Yangi narx qo'shish</b>\n\n"
        "Kunlar sonini kiriting (masalan: 30):",
        reply_markup=cancel_keyboard()
    )
    await AdminPriceStates.enter_days.set()

@dp.message_handler(state=AdminPriceStates.enter_days)
async def enter_price_days(message: types.Message, state: FSMContext):
    """Kunlar sonini qabul qilish"""
    try:
        days = int(message.text)
        if days <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Musbat son kiriting:")
        return
    
    await state.update_data(days=days)
    await message.answer("💰 Narxni kiriting (so'mda):")
    await AdminPriceStates.enter_price.set()

@dp.message_handler(state=AdminPriceStates.enter_price)
async def enter_price_amount(message: types.Message, state: FSMContext):
    """Narxni qabul qilish"""
    try:
        price = float(message.text.replace(",", "").replace(" ", ""))
        if price <= 0:
            raise ValueError
    except ValueError:
        await message.answer("❌ Noto'g'ri format. Musbat son kiriting:")
        return
    
    await state.update_data(price=price)
    await message.answer("📄 Tavsif kiriting (yoki 'skip'):")
    await AdminPriceStates.enter_description.set()

@dp.message_handler(state=AdminPriceStates.enter_description)
async def enter_price_description(message: types.Message, state: FSMContext):
    """Tavsif qabul qilish"""
    description = None if message.text.lower() == 'skip' else message.text
    
    data = await state.get_data()
    
    add_price(
        days=data['days'],
        price=data['price'],
        description=description
    )
    
    await state.finish()
    
    await message.answer(
        f"""✅ <b>Narx qo'shildi!</b>

📅 Kunlar: {data['days']}
💰 Narx: {data['price']:,.0f} so'm
📄 Tavsif: {description or '-'}""",
        reply_markup=admin_prices_keyboard()
    )

@dp.message_handler(text="📋 Barcha narxlar")
async def all_prices(message: types.Message):
    """Barcha narxlar"""
    if not is_admin(message.from_user.id):
        return
    
    prices = get_all_prices()
    
    if not prices:
        await message.answer("💵 Narxlar yo'q", reply_markup=admin_prices_keyboard())
        return
    
    for price in prices:
        status = "🟢 Faol" if price['is_active'] else "🔴 O'chirilgan"
        text = f"""💵 <b>{price['days']} kun</b>

💰 Narx: {price['price']:,.0f} so'm
📄 Tavsif: {price['description'] or '-'}
📊 Status: {status}"""
        
        await message.answer(text, reply_markup=price_action_keyboard(price['id'], price['is_active']))

@dp.callback_query_handler(text_startswith="toggle_price:")
async def toggle_price_callback(call: types.CallbackQuery):
    """Narx holatini o'zgartirish"""
    if not is_admin(call.from_user.id):
        return
    
    price_id = int(call.data.split(":")[1])
    toggle_price(price_id)
    
    price = get_price(price_id)
    status = "🟢 Faol" if price['is_active'] else "🔴 O'chirilgan"
    
    await call.message.edit_text(
        f"""💵 <b>{price['days']} kun</b>

💰 Narx: {price['price']:,.0f} so'm
📄 Tavsif: {price['description'] or '-'}
📊 Status: {status}""",
        reply_markup=price_action_keyboard(price['id'], price['is_active'])
    )
    await call.answer("✅ Status o'zgartirildi")

@dp.callback_query_handler(text_startswith="delete_price:")
async def delete_price_callback(call: types.CallbackQuery):
    """Narxni o'chirish"""
    if not is_admin(call.from_user.id):
        return
    
    price_id = int(call.data.split(":")[1])
    delete_price(price_id)
    
    await call.message.edit_text("🗑 Narx o'chirildi!")
    await call.answer()
