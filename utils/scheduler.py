import asyncio
from datetime import datetime, timedelta
from aiogram import Bot

from utils.db_api.database import (
    get_expiring_subscriptions, get_expired_subscriptions,
    deactivate_subscription, update_last_notified, get_active_channels
)

async def check_subscriptions(bot: Bot):
    """
    Obunalarni tekshirish va xabar yuborish
    Har soatda bir marta ishlatiladi
    """
    # 3 kun ichida tugaydigan obunalar
    expiring_subs = get_expiring_subscriptions(3)
    
    for sub in expiring_subs:
        # Oxirgi ogohlantirish 24 soatdan oldin bo'lgan bo'lsa
        last_notified = sub['last_notified']
        
        if last_notified:
            last_time = datetime.strptime(last_notified, '%Y-%m-%d %H:%M:%S')
            if datetime.now() - last_time < timedelta(hours=24):
                continue
        
        expires_at = sub['expires_at']
        if expires_at:
            expires_date = datetime.strptime(expires_at, '%Y-%m-%d %H:%M:%S')
            days_left = (expires_date - datetime.now()).days
        else:
            days_left = 0
        
        text = f"""⚠️ <b>Obuna tugash muddati yaqinlashmoqda!</b>

📅 Tugash sanasi: {expires_at[:10] if expires_at else '-'}
⏳ Qolgan vaqt: <b>{days_left} kun</b>

💡 Obunani yangilash uchun /start buyrug'ini yuboring va "💳 To'lov qilish" tugmasini bosing.

❗️ Vaqtida to'lov qilmasangiz, premium kanaldan chiqarilasiz."""
        
        try:
            await bot.send_message(sub['user_id'], text)
            update_last_notified(sub['user_id'])
        except Exception as e:
            print(f"Xabar yuborishda xato (user {sub['user_id']}): {e}")
    
    # Muddati o'tgan obunalar
    expired_subs = get_expired_subscriptions()
    
    for sub in expired_subs:
        # Foydalanuvchiga xabar yuborish
        text = f"""❌ <b>Obunangiz muddati tugadi!</b>

📅 Tugagan sana: {sub['expires_at'][:10] if sub['expires_at'] else '-'}

😔 Siz premium kanaldan chiqarildingiz.

💡 Qayta obuna bo'lish uchun /start buyrug'ini yuboring va "💳 To'lov qilish" tugmasini bosing."""
        
        try:
            await bot.send_message(sub['user_id'], text)
        except:
            pass
        
        # Kanaldan chiqarish
        channels = get_active_channels()
        for channel in channels:
            try:
                await bot.kick_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=sub['user_id']
                )
                # Unban qilish (keyingi obunada kirish imkoniyati uchun)
                await bot.unban_chat_member(
                    chat_id=channel['channel_id'],
                    user_id=sub['user_id']
                )
            except Exception as e:
                print(f"Kanaldan chiqarishda xato (user {sub['user_id']}): {e}")
        
        # Obunani o'chirish
        deactivate_subscription(sub['user_id'])

async def subscription_scheduler(bot: Bot):
    """
    Obunalar tekshirish scheduleri
    Har 1 soatda ishlaydi
    """
    while True:
        try:
            await check_subscriptions(bot)
        except Exception as e:
            print(f"Scheduler xatosi: {e}")
        
        # 1 soat kutish
        await asyncio.sleep(3600)
