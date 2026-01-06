from aiogram.dispatcher.filters.state import State, StatesGroup

# ============ USER STATES ============

class PaymentStates(StatesGroup):
    """To'lov holatlari"""
    select_price = State()
    select_card = State()
    send_receipt = State()
    confirm_payment = State()

class ContactStates(StatesGroup):
    """Aloqa holatlari"""
    waiting_message = State()

# ============ ADMIN STATES ============

class AdminCardStates(StatesGroup):
    """Karta qo'shish holatlari"""
    enter_card_number = State()
    enter_card_holder = State()
    enter_bank_name = State()

class AdminChannelStates(StatesGroup):
    """Kanal qo'shish holatlari"""
    enter_channel_id = State()
    enter_channel_name = State()
    enter_invite_link = State()
    edit_invite_link = State()

class AdminVideoStates(StatesGroup):
    """Video qo'shish holatlari"""
    send_video = State()
    enter_video_name = State()
    enter_video_description = State()
    select_video_type = State()

class AdminPriceStates(StatesGroup):
    """Narx qo'shish holatlari"""
    enter_days = State()
    enter_price = State()
    enter_description = State()

class AdminBroadcastStates(StatesGroup):
    """Reklama holatlari"""
    select_target = State()
    enter_message = State()
    enter_photo = State()
    enter_video = State()
    confirm_broadcast = State()

class AdminPaymentStates(StatesGroup):
    """To'lov boshqarish holatlari"""
    enter_reject_reason = State()
    enter_note = State()

class AdminNotifyStates(StatesGroup):
    """Foydalanuvchiga xabar yuborish holatlari"""
    enter_message = State()
