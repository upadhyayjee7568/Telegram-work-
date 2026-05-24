"""
=============================================================
  FREE MONEY EARNING ADDA (FMEA) BOT - Database Handler
=============================================================
"""

import sqlite3
import json
from datetime import datetime
from config import DB_FILE, TIMEZONE

def get_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_database():
    """Initialize all database tables"""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            points INTEGER DEFAULT 0,
            referral_code TEXT UNIQUE,
            referred_by INTEGER,
            total_referrals INTEGER DEFAULT 0,
            is_blocked INTEGER DEFAULT 0,
            joined_at TEXT,
            last_active TEXT
        )
    ''')
    
    # Scheduled posts table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS scheduled_posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            media_type TEXT DEFAULT 'text',
            media_file_id TEXT,
            schedule_time TEXT,
            is_recurring INTEGER DEFAULT 0,
            recurring_interval TEXT,
            status TEXT DEFAULT 'pending',
            created_by INTEGER,
            created_at TEXT,
            sent_at TEXT
        )
    ''')
    
    # Broadcast history
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS broadcasts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            message TEXT,
            media_type TEXT DEFAULT 'text',
            media_file_id TEXT,
            total_sent INTEGER DEFAULT 0,
            total_failed INTEGER DEFAULT 0,
            sent_by INTEGER,
            sent_at TEXT
        )
    ''')
    
    # Auto posts content library
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS content_library (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            content TEXT NOT NULL,
            category TEXT DEFAULT 'general',
            media_type TEXT DEFAULT 'text',
            media_file_id TEXT,
            is_active INTEGER DEFAULT 1,
            added_by INTEGER,
            added_at TEXT
        )
    ''')

    # User questions queue (for admin follow-up)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_questions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            question TEXT NOT NULL,
            status TEXT DEFAULT 'open',
            admin_reply TEXT,
            created_at TEXT,
            answered_at TEXT
        )
    ''')
    
    # Bot settings
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS settings (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TEXT
        )
    ''')
    
    # Insert default settings
    default_settings = [
        ('auto_post_enabled', 'true'),
        ('welcome_msg_enabled', 'true'),
        ('referral_enabled', 'true'),
        ('bot_status', 'active'),
        ('total_posts_sent', '0'),
        ('maintenance_mode', 'false'),
    ]
    
    for key, value in default_settings:
        cursor.execute('''
            INSERT OR IGNORE INTO settings (key, value, updated_at) 
            VALUES (?, ?, ?)
        ''', (key, value, datetime.now().isoformat()))
    
    conn.commit()
    conn.close()
    print("✅ Database initialized successfully!")

# ── USER FUNCTIONS ──────────────────────────────────────────

def add_user(user_id, username, first_name, last_name, referred_by=None):
    """Add new user to database"""
    conn = get_connection()
    cursor = conn.cursor()
    
    import random, string
    ref_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO users 
            (user_id, username, first_name, last_name, referral_code, referred_by, joined_at, last_active)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, username, first_name, last_name, ref_code, referred_by,
              datetime.now().isoformat(), datetime.now().isoformat()))
        
        if cursor.rowcount > 0 and referred_by:
            cursor.execute('''
                UPDATE users SET total_referrals = total_referrals + 1, 
                points = points + 10 WHERE user_id = ?
            ''', (referred_by,))
        
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()

def get_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE user_id = ?', (user_id,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def update_last_active(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET last_active = ? WHERE user_id = ?',
                   (datetime.now().isoformat(), user_id))
    conn.commit()
    conn.close()

def get_all_users(exclude_blocked=True):
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_blocked:
        cursor.execute('SELECT user_id FROM users WHERE is_blocked = 0')
    else:
        cursor.execute('SELECT user_id FROM users')
    users = [row['user_id'] for row in cursor.fetchall()]
    conn.close()
    return users

def get_user_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM users')
    total = cursor.fetchone()['total']
    cursor.execute('SELECT COUNT(*) as active FROM users WHERE is_blocked = 0')
    active = cursor.fetchone()['active']
    cursor.execute('SELECT COUNT(*) as today FROM users WHERE date(joined_at) = date("now")')
    today = cursor.fetchone()['today']
    conn.close()
    return {'total': total, 'active': active, 'today': today}

def block_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_blocked = 1 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def unblock_user(user_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET is_blocked = 0 WHERE user_id = ?', (user_id,))
    conn.commit()
    conn.close()

def add_points(user_id, points):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('UPDATE users SET points = points + ? WHERE user_id = ?', (points, user_id))
    conn.commit()
    conn.close()

def get_top_referrers(limit=10):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT user_id, first_name, username, total_referrals, points 
        FROM users ORDER BY total_referrals DESC LIMIT ?
    ''', (limit,))
    result = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return result

def get_user_by_referral(ref_code):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM users WHERE referral_code = ?', (ref_code,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

# ── SCHEDULED POST FUNCTIONS ─────────────────────────────────

def add_scheduled_post(content, schedule_time, media_type='text', media_file_id=None,
                        is_recurring=False, recurring_interval=None, created_by=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO scheduled_posts 
        (content, media_type, media_file_id, schedule_time, is_recurring, 
         recurring_interval, created_by, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (content, media_type, media_file_id, schedule_time, int(is_recurring),
          recurring_interval, created_by, datetime.now().isoformat()))
    post_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return post_id

def get_pending_posts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM scheduled_posts 
        WHERE status = 'pending' 
        ORDER BY schedule_time ASC
    ''')
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts

def get_all_scheduled_posts():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM scheduled_posts ORDER BY created_at DESC LIMIT 20
    ''')
    posts = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return posts

def mark_post_sent(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE scheduled_posts SET status = 'sent', sent_at = ? WHERE id = ?
    ''', (datetime.now().isoformat(), post_id))
    conn.commit()
    conn.close()

def delete_scheduled_post(post_id):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM scheduled_posts WHERE id = ?', (post_id,))
    conn.commit()
    conn.close()

# ── CONTENT LIBRARY ──────────────────────────────────────────

def add_content(title, content, category='general', media_type='text', 
                media_file_id=None, added_by=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO content_library 
        (title, content, category, media_type, media_file_id, added_by, added_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (title, content, category, media_type, media_file_id, added_by, 
          datetime.now().isoformat()))
    content_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return content_id

def get_content_list():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM content_library WHERE is_active = 1 ORDER BY added_at DESC')
    content = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return content

def get_random_content(category=None):
    conn = get_connection()
    cursor = conn.cursor()
    if category:
        cursor.execute('''
            SELECT * FROM content_library WHERE is_active = 1 AND category = ?
            ORDER BY RANDOM() LIMIT 1
        ''', (category,))
    else:
        cursor.execute('''
            SELECT * FROM content_library WHERE is_active = 1 
            ORDER BY RANDOM() LIMIT 1
        ''')
    content = cursor.fetchone()
    conn.close()
    return dict(content) if content else None

# ── SETTINGS ─────────────────────────────────────────────────

def get_setting(key):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT value FROM settings WHERE key = ?', (key,))
    row = cursor.fetchone()
    conn.close()
    return row['value'] if row else None

def set_setting(key, value):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO settings (key, value, updated_at) 
        VALUES (?, ?, ?)
    ''', (key, str(value), datetime.now().isoformat()))
    conn.commit()
    conn.close()

def get_broadcast_stats():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('SELECT COUNT(*) as total FROM broadcasts')
    total = cursor.fetchone()['total']
    conn.close()
    return {'total_broadcasts': total}

def log_broadcast(message, total_sent, total_failed, sent_by, media_type='text', media_file_id=None):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO broadcasts 
        (message, media_type, media_file_id, total_sent, total_failed, sent_by, sent_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (message, media_type, media_file_id, total_sent, total_failed, 
          sent_by, datetime.now().isoformat()))
    conn.commit()
    conn.close()

# ── USER QUESTION QUEUE ─────────────────────────────────────

def add_user_question(user_id, username, question):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO user_questions (user_id, username, question, created_at)
        VALUES (?, ?, ?, ?)
    ''', (user_id, username, question, datetime.now().isoformat()))
    qid = cursor.lastrowid
    conn.commit()
    conn.close()
    return qid

def get_open_questions(limit=20):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        SELECT * FROM user_questions WHERE status = 'open'
        ORDER BY created_at ASC LIMIT ?
    ''', (limit,))
    rows = [dict(r) for r in cursor.fetchall()]
    conn.close()
    return rows

def close_user_question(question_id, admin_reply):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE user_questions
        SET status = 'answered', admin_reply = ?, answered_at = ?
        WHERE id = ?
    ''', (admin_reply, datetime.now().isoformat(), question_id))
    conn.commit()
    conn.close()
