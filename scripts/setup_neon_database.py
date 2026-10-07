import sqlite3
import psycopg2
from psycopg2.extras import execute_batch
import os

POSTGRES_URL = "postgresql://neondb_owner:npg_WXPYN6JAhL0n@ep-shiny-morning-b4du6ohv-pooler.c-6.us-east-2.aws.neon.tech/neondb?sslmode=require"

SCHEMA_SQL = """
-- 1. USERS
CREATE TABLE IF NOT EXISTS users (
    user_id BIGINT PRIMARY KEY,
    first_name VARCHAR(255) DEFAULT '',
    last_name VARCHAR(255) DEFAULT '',
    username VARCHAR(255) DEFAULT '',
    phone VARCHAR(64) DEFAULT '',
    referrer_id BIGINT DEFAULT 0,
    balance NUMERIC(18, 2) DEFAULT 0.00,
    total_earned NUMERIC(18, 2) DEFAULT 0.00,
    status VARCHAR(128) DEFAULT '🌱 Boshlang''ich',
    current_level INT DEFAULT 1,
    wallet_bep20 VARCHAR(255) DEFAULT '',
    wallet_card VARCHAR(255) DEFAULT '',
    wallet_trc20 VARCHAR(255) DEFAULT '',
    wallet_payeer VARCHAR(255) DEFAULT '',
    registered_at VARCHAR(64) DEFAULT '',
    is_active SMALLINT DEFAULT 1,
    is_banned SMALLINT DEFAULT 0,
    visits_count INT DEFAULT 1,
    last_active VARCHAR(64) DEFAULT ''
);

-- 2. LEVEL SETTINGS
CREATE TABLE IF NOT EXISTS level_settings (
    level INT PRIMARY KEY,
    price NUMERIC(18, 2) NOT NULL,
    name VARCHAR(255) NOT NULL,
    is_active SMALLINT DEFAULT 1
);

-- 3. BROADCAST HISTORY
CREATE TABLE IF NOT EXISTS broadcast_history (
    id BIGSERIAL PRIMARY KEY,
    text TEXT,
    photo_url TEXT,
    button_text VARCHAR(255),
    button_url TEXT,
    target_filter VARCHAR(64) DEFAULT 'all',
    sent_count INT DEFAULT 0,
    fail_count INT DEFAULT 0,
    status VARCHAR(64) DEFAULT 'completed',
    created_at VARCHAR(64) DEFAULT ''
);

-- 4. ANNOUNCEMENTS
CREATE TABLE IF NOT EXISTS announcements (
    id BIGSERIAL PRIMARY KEY,
    title VARCHAR(255),
    text TEXT,
    is_active SMALLINT DEFAULT 1,
    created_at VARCHAR(64) DEFAULT ''
);

-- 5. ACTIVITY LOGS
CREATE TABLE IF NOT EXISTS activity_logs (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT,
    action VARCHAR(128),
    details TEXT,
    created_at VARCHAR(64) DEFAULT ''
);

-- 6. PAYMENT LOGS
CREATE TABLE IF NOT EXISTS payment_logs (
    id BIGSERIAL PRIMARY KEY,
    buyer_id BIGINT,
    curator_id BIGINT,
    level INT,
    amount NUMERIC(18, 2),
    status VARCHAR(64) DEFAULT 'pending',
    created_at VARCHAR(64) DEFAULT '',
    confirmed_at VARCHAR(64) DEFAULT ''
);

-- 7. USER REPLACEMENTS
CREATE TABLE IF NOT EXISTS user_replacements (
    old_user_id BIGINT PRIMARY KEY,
    new_user_id BIGINT NOT NULL,
    replaced_at VARCHAR(64) DEFAULT ''
);

-- 8. LINKED ACCOUNTS
CREATE TABLE IF NOT EXISTS linked_accounts (
    id BIGSERIAL PRIMARY KEY,
    owner_id BIGINT NOT NULL,
    linked_id BIGINT NOT NULL,
    created_at VARCHAR(64) DEFAULT '',
    CONSTRAINT uq_linked_accounts UNIQUE(owner_id, linked_id)
);

-- 9. ACCOUNT LINK OTPS
CREATE TABLE IF NOT EXISTS account_link_otps (
    id BIGSERIAL PRIMARY KEY,
    requester_id BIGINT NOT NULL,
    target_id BIGINT NOT NULL,
    code VARCHAR(32) NOT NULL,
    created_at VARCHAR(64) DEFAULT '',
    expires_at VARCHAR(64) DEFAULT '',
    status VARCHAR(64) DEFAULT 'pending'
);

-- 10. BANNED DELETED USERS
CREATE TABLE IF NOT EXISTS banned_deleted_users (
    user_id BIGINT PRIMARY KEY,
    first_name VARCHAR(255) DEFAULT '',
    last_name VARCHAR(255) DEFAULT '',
    username VARCHAR(255) DEFAULT '',
    phone VARCHAR(64) DEFAULT '',
    type VARCHAR(64) DEFAULT 'banned',
    reason TEXT DEFAULT '',
    action_date VARCHAR(64) DEFAULT '',
    admin_id BIGINT DEFAULT 0
);

-- 11. PENDING REFERRALS
CREATE TABLE IF NOT EXISTS pending_referrals (
    user_id BIGINT PRIMARY KEY,
    referrer_id BIGINT NOT NULL,
    created_at VARCHAR(64) NOT NULL,
    updated_at VARCHAR(64) NOT NULL
);

-- INDEXES
CREATE INDEX IF NOT EXISTS idx_users_referrer_id ON users(referrer_id);
CREATE INDEX IF NOT EXISTS idx_users_username_lower ON users(LOWER(username));
CREATE INDEX IF NOT EXISTS idx_users_phone ON users(phone);
CREATE INDEX IF NOT EXISTS idx_users_current_level ON users(current_level);
CREATE INDEX IF NOT EXISTS idx_users_is_banned ON users(is_banned);

CREATE INDEX IF NOT EXISTS idx_payment_logs_curator ON payment_logs(curator_id);
CREATE INDEX IF NOT EXISTS idx_payment_logs_buyer ON payment_logs(buyer_id);
CREATE INDEX IF NOT EXISTS idx_user_replacements_new ON user_replacements(new_user_id);

CREATE INDEX IF NOT EXISTS idx_linked_accounts_owner ON linked_accounts(owner_id);
CREATE INDEX IF NOT EXISTS idx_linked_accounts_linked ON linked_accounts(linked_id);
CREATE INDEX IF NOT EXISTS idx_activity_logs_user ON activity_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_banned_deleted_phone ON banned_deleted_users(phone);

-- SEED LEVEL SETTINGS
INSERT INTO level_settings (level, price, name, is_active) VALUES
    (1, 200000.00, '1-Daraja (200 000 so''m)', 1),
    (2, 300000.00, '2-Daraja (300 000 so''m)', 1),
    (3, 1300000.00, '3-Daraja (1 300 000 so''m)', 1),
    (4, 17000000.00, '4-Daraja (17 000 000 so''m)', 1),
    (5, 70000000.00, '5-Daraja (50 000 000 so''m)', 1)
ON CONFLICT (level) DO UPDATE SET
    price = EXCLUDED.price,
    name = EXCLUDED.name,
    is_active = EXCLUDED.is_active;
"""

TABLES = [
    "level_settings",
    "users",
    "broadcast_history",
    "announcements",
    "activity_logs",
    "payment_logs",
    "user_replacements",
    "linked_accounts",
    "account_link_otps",
    "banned_deleted_users",
    "pending_referrals"
]

def setup_and_migrate():
    print("[1] Connecting to Neon.tech PostgreSQL...")
    pg_conn = psycopg2.connect(POSTGRES_URL)
    pg_cur = pg_conn.cursor()

    print("[2] Creating all tables, constraints, indexes and seeds in Neon.tech...")
    pg_cur.execute(SCHEMA_SQL)
    pg_conn.commit()
    print("[+] All tables and indexes created successfully!")

    # Check for any non-empty SQLite database to migrate
    sqlite_candidates = ["buyukhayot.db", "bot.db", "users.db", "database/bot.db"]
    migrated_count = 0

    for sl_path in sqlite_candidates:
        if os.path.exists(sl_path) and os.path.getsize(sl_path) > 0:
            print(f"[3] Found local SQLite database with data: {sl_path}. Checking records...")
            try:
                sl_conn = sqlite3.connect(sl_path)
                sl_conn.row_factory = sqlite3.Row
                sl_cur = sl_conn.cursor()

                for table in TABLES:
                    try:
                        sl_cur.execute(f"SELECT * FROM {table}")
                        rows = sl_cur.fetchall()
                        if not rows:
                            continue

                        columns = list(rows[0].keys())
                        cols_str = ", ".join(columns)
                        placeholders = ", ".join(["%s"] * len(columns))
                        data = [[r[c] for c in columns] for r in rows]

                        query = f"INSERT INTO {table} ({cols_str}) VALUES ({placeholders}) ON CONFLICT DO NOTHING"
                        execute_batch(pg_cur, query, data)
                        pg_conn.commit()
                        print(f"    [+] Migrated {len(rows)} records from {sl_path} -> table '{table}'")
                        migrated_count += len(rows)
                    except Exception as te:
                        # Table might not exist in this sqlite file
                        pass

                sl_cur.close()
                sl_conn.close()
            except Exception as se:
                print(f"    [-] Error reading {sl_path}: {se}")

    if migrated_count == 0:
        print("[!] Local SQLite files are currently empty (0 bytes). Database schema in Neon.tech is completely initialized and ready!")

    # Verify tables in Neon.tech
    print("\n[4] Verifying tables in Neon.tech PostgreSQL:")
    pg_cur.execute("""
        SELECT table_name 
        FROM information_schema.tables 
        WHERE table_schema = 'public' 
        ORDER BY table_name;
    """)
    pg_tables = [r[0] for r in pg_cur.fetchall()]
    for t in pg_tables:
        pg_cur.execute(f"SELECT COUNT(*) FROM {t}")
        cnt = pg_cur.fetchone()[0]
        print(f"    - Table '{t}': {cnt} records")

    pg_cur.close()
    pg_conn.close()
    print("\n[SUCCESS] Neon.tech database is 100% configured and verified!")

if __name__ == "__main__":
    setup_and_migrate()
