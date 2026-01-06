import sqlite3
from datetime import datetime, timedelta
import os

DB_PATH = os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'bot_database.db')

def get_connection():
    """Database ulanishini qaytaradi"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Database jadvallarini yaratadi"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Foydalanuvchilar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            full_name TEXT,
            phone TEXT,
            registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_blocked INTEGER DEFAULT 0,
            language TEXT DEFAULT 'uz'
        )
    ''')
    
    # To'lovlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS payments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            amount REAL,
            receipt_photo TEXT,
            card_id INTEGER,
            status TEXT DEFAULT 'pending',
            subscription_days INTEGER DEFAULT 30,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            approved_at TIMESTAMP,
            expires_at TIMESTAMP,
            admin_note TEXT,
            FOREIGN KEY (user_id) REFERENCES users(user_id),
            FOREIGN KEY (card_id) REFERENCES cards(id)
        )
    ''')
    
    # Obunalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS subscriptions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER UNIQUE,
            is_active INTEGER DEFAULT 0,
            started_at TIMESTAMP,
            expires_at TIMESTAMP,
            channel_joined INTEGER DEFAULT 0,
            last_notified TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(user_id)
        )
    ''')
    
    # Kartalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS cards (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            card_number TEXT NOT NULL,
            card_holder TEXT,
            bank_name TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Kanallar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS channels (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            channel_id TEXT,
            channel_name TEXT,
            invite_link TEXT,
            is_active INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Video qo'llanmalar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            file_id TEXT NOT NULL,
            description TEXT,
            is_free INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Reklama xabarlari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message_text TEXT,
            photo_id TEXT,
            video_id TEXT,
            sent_count INTEGER DEFAULT 0,
            failed_count INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Bot sozlamalari jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT
        )
    ''')
    
    # Narxlar jadvali
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS prices (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            days INTEGER NOT NULL,
            price REAL NOT NULL,
            description TEXT,
            is_active INTEGER DEFAULT 1
        )
    ''')
    
    conn.commit()
    conn.close()

# ============ USERS ============

def add_user(user_id: int, username: str = None, full_name: str = None):
    """Yangi foydalanuvchi qo'shadi"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO users (user_id, username, full_name)
            VALUES (?, ?, ?)
        ''', (user_id, username, full_name))
        conn.commit()
    finally:
        conn.close()

def get_user(user_id: int):
    """Foydalanuvchi ma'lumotlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return user

def get_all_users():
    """Barcha foydalanuvchilarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users')
    users = cursor.fetchall()
    conn.close()
    return users

def get_users_count():
    """Foydalanuvchilar sonini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) FROM users')
    count = cursor.fetchone()[0]
    conn.close()
    return count

def update_user_phone(user_id: int, phone: str):
    """Foydalanuvchi telefonini yangilaydi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET phone = ? WHERE user_id = ?', (phone, user_id))
    conn.commit()
    conn.close()

# ============ PAYMENTS ============

def add_payment(user_id: int, amount: float, receipt_photo: str, card_id: int, subscription_days: int = 30):
    """Yangi to'lov qo'shadi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO payments (user_id, amount, receipt_photo, card_id, subscription_days)
        VALUES (?, ?, ?, ?, ?)
    ''', (user_id, amount, receipt_photo, card_id, subscription_days))
    payment_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return payment_id

def get_pending_payments():
    """Kutayotgan to'lovlarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.full_name 
        FROM payments p 
        JOIN users u ON p.user_id = u.user_id 
        WHERE p.status = 'pending'
        ORDER BY p.created_at DESC
    ''')
    payments = cursor.fetchall()
    conn.close()
    return payments

def get_payment(payment_id: int):
    """To'lov ma'lumotlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.full_name 
        FROM payments p 
        JOIN users u ON p.user_id = u.user_id 
        WHERE p.id = ?
    ''', (payment_id,))
    payment = cursor.fetchone()
    conn.close()
    return payment


def approve_payment(payment_id: int, admin_note: str = None):
    """To'lovni tasdiqlaydi"""
    conn = get_connection()
    cursor = conn.cursor()

    # To'lov ma'lumotlarini olish (barcha ustunlar)
    cursor.execute('SELECT * FROM payments WHERE id = ?', (payment_id,))
    payment = cursor.fetchone()

    if payment:
        user_id = payment['user_id']
        days = payment['subscription_days']
        expires_at = datetime.now() + timedelta(days=days)

        # To'lovni tasdiqlash
        cursor.execute('''
            UPDATE payments 
            SET status = 'approved', approved_at = CURRENT_TIMESTAMP, 
                expires_at = ?, admin_note = ?
            WHERE id = ?
        ''', (expires_at, admin_note, payment_id))

        # Obunani yangilash yoki yaratish
        cursor.execute('''
            INSERT OR REPLACE INTO subscriptions 
            (user_id, is_active, started_at, expires_at, channel_joined)
            VALUES (?, 1, CURRENT_TIMESTAMP, ?, 0)
        ''', (user_id, expires_at))

        conn.commit()

        # Yangilangan to'lov ma'lumotlarini qaytarish
        payment = dict(payment)
        payment['subscription_days'] = days

    conn.close()
    return payment

def reject_payment(payment_id: int, admin_note: str = None):
    """To'lovni rad etadi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE payments 
        SET status = 'rejected', admin_note = ?
        WHERE id = ?
    ''', (admin_note, payment_id))
    conn.commit()
    conn.close()

def get_user_payments(user_id: int):
    """Foydalanuvchi to'lovlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM payments 
        WHERE user_id = ? 
        ORDER BY created_at DESC
    ''', (user_id,))
    payments = cursor.fetchall()
    conn.close()
    return payments

def get_all_payments(limit: int = 50):
    """Barcha to'lovlarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT p.*, u.username, u.full_name 
        FROM payments p 
        JOIN users u ON p.user_id = u.user_id 
        ORDER BY p.created_at DESC
        LIMIT ?
    ''', (limit,))
    payments = cursor.fetchall()
    conn.close()
    return payments

# ============ SUBSCRIPTIONS ============

def get_subscription(user_id: int):
    """Foydalanuvchi obunasini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM subscriptions WHERE user_id = ?', (user_id,))
    sub = cursor.fetchone()
    conn.close()
    return sub

def get_active_subscriptions():
    """Faol obunalarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, u.username, u.full_name 
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.is_active = 1
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_expiring_subscriptions(days: int = 3):
    """Muddati tugayotgan obunalarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    check_date = datetime.now() + timedelta(days=days)
    cursor.execute('''
        SELECT s.*, u.username, u.full_name 
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.is_active = 1 
        AND s.expires_at <= ?
        AND s.expires_at > CURRENT_TIMESTAMP
    ''', (check_date,))
    subs = cursor.fetchall()
    conn.close()
    return subs

def get_expired_subscriptions():
    """Muddati o'tgan obunalarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT s.*, u.username, u.full_name 
        FROM subscriptions s
        JOIN users u ON s.user_id = u.user_id
        WHERE s.is_active = 1 
        AND s.expires_at <= CURRENT_TIMESTAMP
    ''')
    subs = cursor.fetchall()
    conn.close()
    return subs

def deactivate_subscription(user_id: int):
    """Obunani o'chiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE subscriptions 
        SET is_active = 0, channel_joined = 0
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def mark_channel_joined(user_id: int):
    """Foydalanuvchi kanalga qo'shilganini belgilaydi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE subscriptions 
        SET channel_joined = 1
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

def update_last_notified(user_id: int):
    """Oxirgi ogohlantirish vaqtini yangilaydi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE subscriptions 
        SET last_notified = CURRENT_TIMESTAMP
        WHERE user_id = ?
    ''', (user_id,))
    conn.commit()
    conn.close()

# ============ CARDS ============

def add_card(card_number: str, card_holder: str = None, bank_name: str = None):
    """Yangi karta qo'shadi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO cards (card_number, card_holder, bank_name)
        VALUES (?, ?, ?)
    ''', (card_number, card_holder, bank_name))
    card_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return card_id

def get_active_cards():
    """Faol kartalarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cards WHERE is_active = 1')
    cards = cursor.fetchall()
    conn.close()
    return cards

def get_all_cards():
    """Barcha kartalarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cards ORDER BY created_at DESC')
    cards = cursor.fetchall()
    conn.close()
    return cards

def get_card(card_id: int):
    """Karta ma'lumotlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM cards WHERE id = ?', (card_id,))
    card = cursor.fetchone()
    conn.close()
    return card

def toggle_card(card_id: int):
    """Karta holatini o'zgartiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE cards SET is_active = NOT is_active WHERE id = ?', (card_id,))
    conn.commit()
    conn.close()

def delete_card(card_id: int):
    """Kartani o'chiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM cards WHERE id = ?', (card_id,))
    conn.commit()
    conn.close()

# ============ CHANNELS ============

def add_channel(channel_id: str, channel_name: str, invite_link: str):
    """Yangi kanal qo'shadi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO channels (channel_id, channel_name, invite_link)
        VALUES (?, ?, ?)
    ''', (channel_id, channel_name, invite_link))
    conn.commit()
    conn.close()

def get_active_channels():
    """Faol kanallarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels WHERE is_active = 1')
    channels = cursor.fetchall()
    conn.close()
    return channels

def get_all_channels():
    """Barcha kanallarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels ORDER BY created_at DESC')
    channels = cursor.fetchall()
    conn.close()
    return channels

def get_channel(channel_id: int):
    """Kanal ma'lumotlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM channels WHERE id = ?', (channel_id,))
    channel = cursor.fetchone()
    conn.close()
    return channel

def toggle_channel(channel_id: int):
    """Kanal holatini o'zgartiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE channels SET is_active = NOT is_active WHERE id = ?', (channel_id,))
    conn.commit()
    conn.close()

def delete_channel(channel_id: int):
    """Kanalni o'chiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM channels WHERE id = ?', (channel_id,))
    conn.commit()
    conn.close()

def update_channel_link(channel_id: int, invite_link: str):
    """Kanal havolasini yangilaydi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE channels SET invite_link = ? WHERE id = ?', (invite_link, channel_id))
    conn.commit()
    conn.close()

# ============ VIDEOS ============

def add_video(name: str, file_id: str, description: str = None, is_free: int = 0):
    """Yangi video qo'shadi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO videos (name, file_id, description, is_free)
        VALUES (?, ?, ?, ?)
    ''', (name, file_id, description, is_free))
    video_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return video_id

def get_all_videos():
    """Barcha videolarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM videos ORDER BY created_at DESC')
    videos = cursor.fetchall()
    conn.close()
    return videos

def get_free_videos():
    """Bepul videolarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM videos WHERE is_free = 1 ORDER BY created_at DESC')
    videos = cursor.fetchall()
    conn.close()
    return videos

def get_video(video_id: int):
    """Video ma'lumotlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM videos WHERE id = ?', (video_id,))
    video = cursor.fetchone()
    conn.close()
    return video

def delete_video(video_id: int):
    """Videoni o'chiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM videos WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()

def toggle_video_free(video_id: int):
    """Video bepul/pullik holatini o'zgartiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE videos SET is_free = NOT is_free WHERE id = ?', (video_id,))
    conn.commit()
    conn.close()

# ============ PRICES ============

def add_price(days: int, price: float, description: str = None):
    """Yangi narx qo'shadi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO prices (days, price, description)
        VALUES (?, ?, ?)
    ''', (days, price, description))
    conn.commit()
    conn.close()

def get_active_prices():
    """Faol narxlarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prices WHERE is_active = 1 ORDER BY days')
    prices = cursor.fetchall()
    conn.close()
    return prices

def get_all_prices():
    """Barcha narxlarni qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prices ORDER BY days')
    prices = cursor.fetchall()
    conn.close()
    return prices

def get_price(price_id: int):
    """Narx ma'lumotlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM prices WHERE id = ?', (price_id,))
    price = cursor.fetchone()
    conn.close()
    return price

def delete_price(price_id: int):
    """Narxni o'chiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM prices WHERE id = ?', (price_id,))
    conn.commit()
    conn.close()

def toggle_price(price_id: int):
    """Narx holatini o'zgartiradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE prices SET is_active = NOT is_active WHERE id = ?', (price_id,))
    conn.commit()
    conn.close()

# ============ SETTINGS ============

def get_setting(key: str):
    """Sozlama qiymatini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    result = cursor.fetchone()
    conn.close()
    return result['value'] if result else None

def set_setting(key: str, value: str):
    """Sozlamani saqlaydi"""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value)
        VALUES (?, ?)
    ''', (key, value))
    conn.commit()
    conn.close()

# ============ STATISTICS ============

def get_statistics():
    """Statistika ma'lumotlarini qaytaradi"""
    conn = get_connection()
    cursor = conn.cursor()
    
    stats = {}
    
    # Foydalanuvchilar soni
    cursor.execute('SELECT COUNT(*) FROM users')
    stats['total_users'] = cursor.fetchone()[0]
    
    # Bugungi yangi foydalanuvchilar
    cursor.execute('''
        SELECT COUNT(*) FROM users 
        WHERE DATE(registered_at) = DATE('now')
    ''')
    stats['today_users'] = cursor.fetchone()[0]
    
    # Faol obunalar
    cursor.execute('SELECT COUNT(*) FROM subscriptions WHERE is_active = 1')
    stats['active_subscriptions'] = cursor.fetchone()[0]
    
    # Kutayotgan to'lovlar
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'pending'")
    stats['pending_payments'] = cursor.fetchone()[0]
    
    # Tasdiqlangan to'lovlar
    cursor.execute("SELECT COUNT(*) FROM payments WHERE status = 'approved'")
    stats['approved_payments'] = cursor.fetchone()[0]
    
    # Jami to'lovlar summasi
    cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM payments WHERE status = 'approved'")
    stats['total_revenue'] = cursor.fetchone()[0]
    
    # Bu oydagi to'lovlar
    cursor.execute('''
        SELECT COALESCE(SUM(amount), 0) FROM payments 
        WHERE status = 'approved' 
        AND strftime('%Y-%m', approved_at) = strftime('%Y-%m', 'now')
    ''')
    stats['month_revenue'] = cursor.fetchone()[0]
    
    # Muddati tugayotgan obunalar (3 kun ichida)
    check_date = datetime.now() + timedelta(days=3)
    cursor.execute('''
        SELECT COUNT(*) FROM subscriptions 
        WHERE is_active = 1 
        AND expires_at <= ? 
        AND expires_at > CURRENT_TIMESTAMP
    ''', (check_date,))
    stats['expiring_soon'] = cursor.fetchone()[0]
    
    conn.close()
    return stats

# Initialize database
init_db()
