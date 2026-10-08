import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import sqlite3
import psycopg2
from config import DATABASE_URL

print("Updating SQLite databases...")
for db_name in ['buyukhayot.db', 'bot.db', r'database\bot.db']:
    try:
        conn = sqlite3.connect(db_name)
        cur = conn.cursor()
        cur.execute('''
            INSERT INTO users (user_id, first_name, last_name, username, referrer_id, current_level, balance, total_earned, status, registered_at, is_active, is_banned)
            VALUES (985223973, 'Gulnora', '', 'gulnora0765', 6047933818, 2, 1500000.0, 1500000.0, '⚡️ 2-Bosqich Hamkor', '2026-10-08 10:00:00', 1, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name='Gulnora',
                username='gulnora0765',
                referrer_id=6047933818,
                current_level=2,
                balance=1500000.0,
                total_earned=1500000.0,
                status='⚡️ 2-Bosqich Hamkor'
        ''')
        cur.execute('''
            INSERT INTO users (user_id, first_name, last_name, username, referrer_id, current_level, balance, total_earned, status, registered_at, is_active, is_banned)
            VALUES (8395137235, 'Gulnora', '', 'gulnora0765', 6047933818, 2, 1500000.0, 1500000.0, '⚡️ 2-Bosqich Hamkor', '2026-10-08 10:00:00', 1, 0)
            ON CONFLICT(user_id) DO UPDATE SET
                first_name='Gulnora',
                username='gulnora0765',
                referrer_id=6047933818,
                current_level=2,
                balance=1500000.0,
                total_earned=1500000.0,
                status='⚡️ 2-Bosqich Hamkor'
        ''')
        cur.execute('''
            UPDATE users SET referrer_id = 985223973 
            WHERE referrer_id IN (8960353418, 8395137235) AND user_id != 985223973
        ''')
        cur.execute('DELETE FROM user_replacements WHERE old_user_id IN (8960353418, 8395137235, 985223973)')
        cur.execute('INSERT OR REPLACE INTO user_replacements (old_user_id, new_user_id, replaced_at) VALUES (8960353418, 985223973, CURRENT_TIMESTAMP)')
        cur.execute('INSERT OR REPLACE INTO user_replacements (old_user_id, new_user_id, replaced_at) VALUES (8395137235, 985223973, CURRENT_TIMESTAMP)')
        conn.commit()
        conn.close()
        print(f"  {db_name}: OK")
    except Exception as e:
        print(f"  {db_name} error: {e}")

print("Updating Neon PostgreSQL...")
try:
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute('''
        INSERT INTO users (user_id, first_name, last_name, username, referrer_id, current_level, balance, total_earned, status, registered_at, is_active, is_banned)
        VALUES (985223973, 'Gulnora', '', 'gulnora0765', 6047933818, 2, 1500000.00, 1500000.00, '⚡️ 2-Bosqich Hamkor', '2026-10-08 10:00:00', 1, 0)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name='Gulnora',
            username='gulnora0765',
            referrer_id=6047933818,
            current_level=2,
            balance=1500000.00,
            total_earned=1500000.00,
            status='⚡️ 2-Bosqich Hamkor'
    ''')
    cur.execute('''
        INSERT INTO users (user_id, first_name, last_name, username, referrer_id, current_level, balance, total_earned, status, registered_at, is_active, is_banned)
        VALUES (8395137235, 'Gulnora', '', 'gulnora0765', 6047933818, 2, 1500000.00, 1500000.00, '⚡️ 2-Bosqich Hamkor', '2026-10-08 10:00:00', 1, 0)
        ON CONFLICT(user_id) DO UPDATE SET
            first_name='Gulnora',
            username='gulnora0765',
            referrer_id=6047933818,
            current_level=2,
            balance=1500000.00,
            total_earned=1500000.00,
            status='⚡️ 2-Bosqich Hamkor'
    ''')
    cur.execute('''
        UPDATE users SET referrer_id = 985223973 
        WHERE referrer_id IN (8960353418, 8395137235) AND user_id != 985223973
    ''')
    cur.execute('DELETE FROM user_replacements WHERE old_user_id IN (8960353418, 8395137235, 985223973)')
    cur.execute('''
        INSERT INTO user_replacements (old_user_id, new_user_id, replaced_at)
        VALUES (8960353418, 985223973, NOW()), (8395137235, 985223973, NOW())
        ON CONFLICT(old_user_id) DO UPDATE SET new_user_id = EXCLUDED.new_user_id, replaced_at = EXCLUDED.replaced_at
    ''')
    conn.commit()
    conn.close()
    print("  Neon: OK")
except Exception as e:
    print(f"  Neon error: {e}")
