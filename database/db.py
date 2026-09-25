import os
import random
import aiosqlite
from datetime import datetime, timedelta
from config import DB_NAME, ADMINS

class Database:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            # 1. Main Users Table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    phone TEXT DEFAULT '',
                    referrer_id INTEGER DEFAULT 0,
                    balance REAL DEFAULT 0.0,
                    total_earned REAL DEFAULT 0.0,
                    status TEXT DEFAULT '🌱 Boshlang''ich',
                    current_level INTEGER DEFAULT 1,
                    wallet_bep20 TEXT DEFAULT '',
                    wallet_card TEXT DEFAULT '',
                    wallet_trc20 TEXT DEFAULT '',
                    wallet_payeer TEXT DEFAULT '',
                    registered_at TEXT,
                    is_active INTEGER DEFAULT 1,
                    is_banned INTEGER DEFAULT 0,
                    visits_count INTEGER DEFAULT 1,
                    last_active TEXT DEFAULT ''
                )
                """
            )

            # Ensure all columns exist if table was created previously
            for col_sql in [
                "ALTER TABLE users ADD COLUMN phone TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN status TEXT DEFAULT '🌱 Boshlang''ich'",
                "ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0.0",
                "ALTER TABLE users ADD COLUMN total_earned REAL DEFAULT 0.0",
                "ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0",
                "ALTER TABLE users ADD COLUMN visits_count INTEGER DEFAULT 1",
                "ALTER TABLE users ADD COLUMN last_active TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN wallet_bep20 TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN wallet_card TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN wallet_trc20 TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN wallet_payeer TEXT DEFAULT ''",
                "ALTER TABLE users ADD COLUMN current_level INTEGER DEFAULT 1"
            ]:
                try:
                    await db.execute(col_sql)
                except Exception:
                    pass
            await db.commit()

            # 2. Level Settings Table (5 Levels in So'm)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS level_settings (
                    level INTEGER PRIMARY KEY,
                    price REAL NOT NULL,
                    name TEXT,
                    is_active INTEGER DEFAULT 1
                )
                """
            )

            # Delete level 6 if present and seed exact 5 levels
            await db.execute("DELETE FROM level_settings WHERE level > 5")

            default_levels = [
                (1, 200000, "1-Daraja (200 000 so'm)"),
                (2, 300000, "2-Daraja (300 000 so'm)"),
                (3, 1300000, "3-Daraja (1 300 000 so'm)"),
                (4, 17000000, "4-Daraja (17 000 000 so'm)"),
                (5, 70000000, "5-Daraja (70 000 000 so'm)"),
            ]
            for lvl, prc, name in default_levels:
                await db.execute(
                    "INSERT OR REPLACE INTO level_settings (level, price, name, is_active) VALUES (?, ?, ?, 1)",
                    (lvl, prc, name)
                )

            # 3. Broadcast History Table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS broadcast_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    text TEXT,
                    photo_url TEXT,
                    button_text TEXT,
                    button_url TEXT,
                    target_filter TEXT DEFAULT 'all',
                    sent_count INTEGER DEFAULT 0,
                    fail_count INTEGER DEFAULT 0,
                    status TEXT DEFAULT 'completed',
                    created_at TEXT
                )
                """
            )

            # 4. Mini App Announcements Table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS announcements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    title TEXT,
                    text TEXT,
                    is_active INTEGER DEFAULT 1,
                    created_at TEXT
                )
                """
            )

            # 5. Activity Logs Table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS activity_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER,
                    action TEXT,
                    details TEXT,
                    created_at TEXT
                )
                """
            )

            # 6. Payment Logs Table (to'lovlar tarixi)
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    buyer_id INTEGER,
                    curator_id INTEGER,
                    level INTEGER,
                    amount REAL,
                    status TEXT DEFAULT 'pending',
                    created_at TEXT,
                    confirmed_at TEXT DEFAULT ''
                )
                """
            )

            # 7. User Replacements & Referral Aliases Table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS user_replacements (
                    old_user_id INTEGER PRIMARY KEY,
                    new_user_id INTEGER NOT NULL,
                    replaced_at TEXT
                )
                """
            )

            # 8. Linked Multi-Accounts Table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS linked_accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    owner_id INTEGER NOT NULL,
                    linked_id INTEGER NOT NULL,
                    created_at TEXT,
                    UNIQUE(owner_id, linked_id)
                )
                """
            )

            # 9. Account Link OTPs Table
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS account_link_otps (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    requester_id INTEGER NOT NULL,
                    target_id INTEGER NOT NULL,
                    code TEXT NOT NULL,
                    created_at TEXT,
                    expires_at TEXT,
                    status TEXT DEFAULT 'pending'
                )
                """
            )

            # Ensure Admin exists
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for admin_id in ADMINS:
                cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (admin_id,))
                user = await cursor.fetchone()
                if not user:
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO users 
                        (user_id, first_name, last_name, username, referrer_id, status, current_level, registered_at, last_active) 
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (admin_id, "Admin", "Buyuk Hayot", "admin", 0, "👑 Asoschi (Admin)", 5, now, now)
                    )
            await db.commit()
        await self.sync_all_replacements()

    async def get_user(self, user_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def register_user(self, user_id: int, first_name: str, last_name: str, username: str, referrer_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            status = "👑 Admin" if user_id in ADMINS else "🌱 Boshlang'ich"
            default_level = 5 if user_id in ADMINS else 0

            # Guard: check if referrer already has 3 or more direct referrals
            if referrer_id and referrer_id != 0:
                cursor = await db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ? AND user_id != ?", (referrer_id, user_id))
                cnt = (await cursor.fetchone())[0]
                if cnt >= 3:
                    # Referrer is full (max 3 allowed)
                    cursor = await db.execute("SELECT referrer_id FROM users WHERE user_id = ?", (user_id,))
                    row = await cursor.fetchone()
                    if not row or row[0] != referrer_id:
                        referrer_id = 0

            await db.execute(
                """
                INSERT INTO users (user_id, first_name, last_name, username, referrer_id, status, current_level, registered_at, last_active, visits_count)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 1)
                ON CONFLICT(user_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    username = excluded.username,
                    referrer_id = CASE WHEN excluded.referrer_id != 0 THEN excluded.referrer_id ELSE users.referrer_id END,
                    last_active = excluded.last_active,
                    visits_count = users.visits_count + 1
                """,
                (user_id, first_name, last_name, username, referrer_id, status, default_level, now, now)
            )
            await db.commit()
            await self.update_user_rank(user_id)
            if referrer_id:
                await self.update_user_rank(referrer_id)
            await self.log_activity(user_id, "REGISTER", f"Ro'yxatdan o'tdi. Kurator ID: {referrer_id}")

    async def update_user_full(self, user_id: int, first_name: str, last_name: str, username: str, level: int, balance: float, total_earned: float, status: str, wallet_bep20: str, wallet_card: str, wallet_trc20: str, wallet_payeer: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE users SET
                    first_name = ?,
                    last_name = ?,
                    username = ?,
                    current_level = ?,
                    balance = ?,
                    total_earned = ?,
                    status = ?,
                    wallet_bep20 = ?,
                    wallet_card = ?,
                    wallet_trc20 = ?,
                    wallet_payeer = ?
                WHERE user_id = ?
                """,
                (first_name, last_name, username, level, balance, total_earned, status, wallet_bep20, wallet_card, wallet_trc20, wallet_payeer, user_id)
            )
            await db.commit()
            await self.log_activity(user_id, "ADMIN_EDIT", f"Profil admin tomonidan tahrirlandi: Level {level}, Balans ${balance}")

    async def set_user_ban_status(self, user_id: int, is_banned: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET is_banned = ? WHERE user_id = ?", (is_banned, user_id))
            await db.commit()
            action = "BAN" if is_banned else "UNBAN"
            await self.log_activity(user_id, action, f"Foydalanuvchi {'bloklandi' if is_banned else 'blokdan chiqarildi'}")

    async def delete_user(self, user_id: int):
        """Foydalanuvchini bazadan butunlay o'chiradi va uning referallarini kuratoriga o'tkazadi."""
        async with aiosqlite.connect(self.db_path) as db:
            user = await self.get_user(user_id)
            referrer_id = user.get("referrer_id", 0) if user else 0

            # Referallarni o'chirilgan foydalanuvchining kuratoriga biriktirish (zanjir uzilmasligi uchun)
            await db.execute("UPDATE users SET referrer_id = ? WHERE referrer_id = ?", (referrer_id, user_id))
            await db.execute("DELETE FROM users WHERE user_id = ?", (user_id,))
            await db.commit()

            if referrer_id:
                await self.update_user_rank(referrer_id)

            await self.log_activity(user_id, "USER_DELETED", f"Foydalanuvchi bazadan butunlay o'chirildi. Referallari kurator {referrer_id} ga o'tkazildi.")

    async def resolve_and_sync_user(self, user_id: int, username: str = "", first_name: str = "", last_name: str = "", phone: str = "") -> dict:
        """
        Resolves, migrates, and synchronizes a user by real numeric user_id and/or @username.
        If the admin added/replaced someone using @username or pseudo ID (>=900000000),
        this automatically merges/migrates all tables (users, user_replacements, linked_accounts, account_link_otps, payment_logs)
        to their real Telegram user_id and synchronizes level, balance, and tree connections.
        """
        if not user_id:
            return None

        clean_uname = str(username).strip().lstrip("@").lower() if username else ""
        clean_fname = str(first_name).strip().lstrip("@").lower() if first_name else ""
        clean_phone = "".join(ch for ch in str(phone) if ch.isdigit()) if phone else ""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # 1. Fetch record with real user_id
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            user_row = await cursor.fetchone()
            user_data = dict(user_row) if user_row else None

            # 2. Check if a pseudo/placeholder record exists with this username, first_name, phone, or in replacements/linked accounts
            pseudo_data = None
            if clean_uname or clean_fname:
                cursor = await db.execute(
                    """
                    SELECT * FROM users 
                    WHERE user_id != ? AND (
                        user_id >= 900000000 
                        OR status = '🌱 Boshlang''ich'
                        OR current_level >= 1
                    ) AND (
                        (? != '' AND (LOWER(username) = ? OR REPLACE(LOWER(username), '@', '') = ? OR LOWER(first_name) = ?))
                        OR (? != '' AND (LOWER(username) = ? OR LOWER(first_name) = ? OR REPLACE(LOWER(username), '@', '') = ?))
                    )
                    ORDER BY current_level DESC, balance DESC, user_id DESC LIMIT 1
                    """,
                    (user_id, clean_uname, clean_uname, clean_uname, clean_uname, clean_fname, clean_fname, clean_fname, clean_fname)
                )
                p_row = await cursor.fetchone()
                if p_row:
                    pseudo_data = dict(p_row)

            if not pseudo_data and clean_phone and len(clean_phone) >= 7:
                cursor = await db.execute(
                    """
                    SELECT * FROM users 
                    WHERE user_id != ? AND phone != '' AND (
                        phone = ? 
                        OR REPLACE(REPLACE(REPLACE(phone, '+', ''), ' ', ''), '-', '') = ?
                    )
                    ORDER BY current_level DESC, balance DESC, user_id DESC LIMIT 1
                    """,
                    (user_id, phone, clean_phone)
                )
                p_row = await cursor.fetchone()
                if p_row:
                    pseudo_data = dict(p_row)

            # Check if any pseudo ID >= 900000000 is linked to this user or in replacements
            if not pseudo_data:
                cursor = await db.execute(
                    """
                    SELECT u.* FROM users u
                    WHERE u.user_id >= 900000000 AND u.user_id != ? AND (
                        u.user_id IN (SELECT linked_id FROM linked_accounts WHERE owner_id = ?)
                        OR u.user_id IN (SELECT owner_id FROM linked_accounts WHERE linked_id = ?)
                        OR u.user_id IN (SELECT target_id FROM account_link_otps WHERE requester_id = ?)
                        OR u.user_id IN (SELECT requester_id FROM account_link_otps WHERE target_id = ?)
                        OR u.user_id IN (SELECT new_user_id FROM user_replacements WHERE old_user_id = ?)
                        OR u.user_id IN (SELECT old_user_id FROM user_replacements WHERE new_user_id = ?)
                    )
                    LIMIT 1
                    """,
                    (user_id, user_id, user_id, user_id, user_id, user_id, user_id)
                )
                p_row = await cursor.fetchone()
                if p_row:
                    pseudo_data = dict(p_row)

            # Case A: Real user_id was NOT in DB, but pseudo_data was created (e.g. Admin replaced with @username)
            if not user_data and pseudo_data:
                pseudo_id = pseudo_data["user_id"]
                fn = first_name or pseudo_data.get("first_name", "")
                ln = last_name or pseudo_data.get("last_name", "")
                un = clean_uname or pseudo_data.get("username", "")

                # Migrate pseudo_id -> real user_id
                await db.execute(
                    """
                    UPDATE users SET
                        user_id = ?,
                        first_name = ?,
                        last_name = ?,
                        username = ?,
                        last_active = ?
                    WHERE user_id = ?
                    """,
                    (user_id, fn, ln, un, now_str, pseudo_id)
                )
                await db.execute("UPDATE users SET referrer_id = ? WHERE referrer_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE user_replacements SET new_user_id = ? WHERE new_user_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE user_replacements SET old_user_id = ? WHERE old_user_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE linked_accounts SET owner_id = ? WHERE owner_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE linked_accounts SET linked_id = ? WHERE linked_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE account_link_otps SET requester_id = ? WHERE requester_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE account_link_otps SET target_id = ? WHERE target_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE payment_logs SET curator_id = ? WHERE curator_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE payment_logs SET buyer_id = ? WHERE buyer_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE activity_logs SET user_id = ? WHERE user_id = ?", (user_id, pseudo_id))
                # Clean up self-links
                await db.execute("DELETE FROM linked_accounts WHERE owner_id = linked_id")
                await db.commit()

                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                res_row = await cursor.fetchone()
                user_data = dict(res_row) if res_row else None

            # Case B: Both real user_id and pseudo_data exist -> Merge pseudo into real
            elif user_data and pseudo_data:
                pseudo_id = pseudo_data["user_id"]
                final_level = max(int(user_data.get("current_level", 1) or 1), int(pseudo_data.get("current_level", 1) or 1))
                final_balance = float(user_data.get("balance", 0.0) or 0.0) + float(pseudo_data.get("balance", 0.0) or 0.0)
                final_total = float(user_data.get("total_earned", 0.0) or 0.0) + float(pseudo_data.get("total_earned", 0.0) or 0.0)
                final_ref = pseudo_data.get("referrer_id", 0) or user_data.get("referrer_id", 0)
                final_card = user_data.get("wallet_card") or pseudo_data.get("wallet_card") or ""
                final_bep20 = user_data.get("wallet_bep20") or pseudo_data.get("wallet_bep20") or ""
                final_trc20 = user_data.get("wallet_trc20") or pseudo_data.get("wallet_trc20") or ""
                final_payeer = user_data.get("wallet_payeer") or pseudo_data.get("wallet_payeer") or ""
                fn = first_name or user_data.get("first_name", "") or pseudo_data.get("first_name", "")
                ln = last_name or user_data.get("last_name", "") or pseudo_data.get("last_name", "")
                un = clean_uname or user_data.get("username", "") or pseudo_data.get("username", "")

                await db.execute(
                    """
                    UPDATE users SET
                        current_level = ?,
                        balance = ?,
                        total_earned = ?,
                        referrer_id = ?,
                        wallet_card = ?,
                        wallet_bep20 = ?,
                        wallet_trc20 = ?,
                        wallet_payeer = ?,
                        first_name = ?,
                        last_name = ?,
                        username = ?,
                        last_active = ?
                    WHERE user_id = ?
                    """,
                    (final_level, final_balance, final_total, final_ref, final_card, final_bep20, final_trc20, final_payeer, fn, ln, un, now_str, user_id)
                )
                await db.execute("UPDATE users SET referrer_id = ? WHERE referrer_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE user_replacements SET new_user_id = ? WHERE new_user_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE user_replacements SET old_user_id = ? WHERE old_user_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE linked_accounts SET owner_id = ? WHERE owner_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE linked_accounts SET linked_id = ? WHERE linked_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE account_link_otps SET requester_id = ? WHERE requester_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE account_link_otps SET target_id = ? WHERE target_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE payment_logs SET curator_id = ? WHERE curator_id = ?", (user_id, pseudo_id))
                await db.execute("UPDATE payment_logs SET buyer_id = ? WHERE buyer_id = ?", (user_id, pseudo_id))
                await db.execute("DELETE FROM users WHERE user_id = ?", (pseudo_id,))
                await db.execute("DELETE FROM linked_accounts WHERE owner_id = linked_id")
                await db.commit()

                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                res_row = await cursor.fetchone()
                user_data = dict(res_row) if res_row else None

            # Case C: Only real user exists, update names if passed
            elif user_data:
                fn = first_name or user_data.get("first_name", "")
                ln = last_name or user_data.get("last_name", "")
                un = clean_uname or user_data.get("username", "")
                await db.execute(
                    """
                    UPDATE users SET
                        first_name = CASE WHEN ? != '' THEN ? ELSE first_name END,
                        last_name = CASE WHEN ? != '' THEN ? ELSE last_name END,
                        username = CASE WHEN ? != '' THEN ? ELSE username END,
                        last_active = ?
                    WHERE user_id = ?
                    """,
                    (fn, fn, ln, ln, un, un, now_str, user_id)
                )
                await db.commit()
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                res_row = await cursor.fetchone()
                user_data = dict(res_row) if res_row else None

            # Case D: User not in users table yet, but referenced in replacements, linked accounts, or as curator
            if not user_data:
                # Check if this user is in replacements, linked accounts, or has referrals
                cursor = await db.execute(
                    """
                    SELECT (
                        (SELECT COUNT(*) FROM user_replacements WHERE old_user_id = ? OR new_user_id = ?) +
                        (SELECT COUNT(*) FROM linked_accounts WHERE owner_id = ? OR linked_id = ?) +
                        (SELECT COUNT(*) FROM users WHERE referrer_id = ?)
                    ) as ref_count
                    """,
                    (user_id, user_id, user_id, user_id, user_id)
                )
                c_row = await cursor.fetchone()
                ref_activity = c_row[0] if c_row else 0

                if ref_activity > 0 or user_id in ADMINS:
                    status = "👑 Admin" if user_id in ADMINS else "🌱 Boshlang'ich"
                    def_level = 5 if user_id in ADMINS else 1
                    fn = first_name or f"User_{str(user_id)[-4:]}"
                    ln = last_name or ""
                    un = clean_uname or ""
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO users 
                        (user_id, first_name, last_name, username, referrer_id, current_level, status, registered_at, last_active, visits_count)
                        VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, 1)
                        """,
                        (user_id, fn, ln, un, def_level, status, now_str, now_str)
                    )
                    await db.commit()
                    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
                    res_row = await cursor.fetchone()
                    user_data = dict(res_row) if res_row else None

        if user_data:
            await self.update_user_rank(user_id)
            user_data = await self.get_user(user_id)

        return user_data

    async def find_or_create_user_by_identifier(self, identifier: str) -> dict:
        """Finds user by user_id, @username, or phone number, or registers placeholder if valid numeric ID."""
        clean_id = str(identifier).strip().lstrip("@")
        if not clean_id:
            return None

        clean_uname = clean_id.lower()
        digits_only = "".join(ch for ch in str(identifier) if ch.isdigit())

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            # 1. Try finding by numeric user_id
            if clean_id.isdigit():
                uid = int(clean_id)
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                # If not found, create new user entry
                now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute(
                    """
                    INSERT OR IGNORE INTO users (user_id, first_name, last_name, username, referrer_id, current_level, registered_at)
                    VALUES (?, ?, ?, ?, 0, 1, ?)
                    """,
                    (uid, f"User_{clean_id[-4:]}", "", "", now_str)
                )
                await db.commit()
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (uid,))
                new_row = await cursor.fetchone()
                return dict(new_row) if new_row else None

            # 2. Try finding by username (case-insensitive, with or without @)
            cursor = await db.execute(
                "SELECT * FROM users WHERE LOWER(username) = ? OR REPLACE(LOWER(username), '@', '') = ?",
                (clean_uname, clean_uname)
            )
            row = await cursor.fetchone()
            if row:
                return dict(row)

            # 3. Try finding by phone number
            if digits_only and len(digits_only) >= 7:
                cursor = await db.execute(
                    """
                    SELECT * FROM users 
                    WHERE phone != '' AND (
                        phone = ? 
                        OR REPLACE(REPLACE(REPLACE(phone, '+', ''), ' ', ''), '-', '') = ?
                        OR phone LIKE ?
                    )
                    LIMIT 1
                    """,
                    (identifier, digits_only, f"%{digits_only}%")
                )
                row = await cursor.fetchone()
                if row:
                    return dict(row)

            # 4. If username not found, generate a pseudo user_id based on hash or random ID to register them
            pseudo_id = 900000000 + abs(hash(clean_id)) % 99999999
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                """
                INSERT OR IGNORE INTO users (user_id, first_name, last_name, username, referrer_id, current_level, registered_at)
                VALUES (?, ?, ?, ?, 0, 1, ?)
                """,
                (pseudo_id, clean_id, "", clean_uname, now_str)
            )
            await db.commit()
            cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (pseudo_id,))
            new_row = await cursor.fetchone()
            return dict(new_row) if new_row else None

    async def is_user_in_subtree(self, root_id: int, target_id: int, max_depth: int = 15) -> bool:
        """Checks if target_id is equal to or a descendant of root_id."""
        if root_id == target_id:
            return True
        curr = target_id
        depth = 0
        while curr and curr != 0 and depth < max_depth:
            user = await self.get_user(curr)
            if not user:
                break
            ref = user.get("referrer_id", 0)
            if ref == root_id:
                return True
            curr = ref
            depth += 1
        return False

    async def get_user_by_username(self, username: str):
        clean_name = str(username).strip().lstrip("@")
        if not clean_name:
            return None
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (clean_name,))
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def get_all_replacements(self):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute("SELECT * FROM user_replacements ORDER BY replaced_at DESC")
                rows = await cursor.fetchall()
                return [dict(r) for r in rows]
        except Exception:
            return []

    async def get_replacement_map(self) -> dict[int, int]:
        """Returns map of old_user_id -> new_user_id for all replaced/transferred users."""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute("SELECT old_user_id, new_user_id FROM user_replacements")
                rows = await cursor.fetchall()
                rep_map = {}
                for r in rows:
                    if r[0] is not None and r[1] is not None:
                        rep_map[int(r[0])] = int(r[1])

                # Resolve multi-hop replacements (e.g. A -> B -> C)
                resolved = {}
                for k in rep_map:
                    curr = k
                    visited = set()
                    while curr in rep_map and curr not in visited:
                        visited.add(curr)
                        curr = rep_map[curr]
                    resolved[k] = curr
                return resolved
        except Exception:
            return {}

    async def get_effective_referrer_id(self, referrer_id: int) -> int:
        """Returns the active user ID if referrer_id was replaced by someone else."""
        if not referrer_id:
            return 0
        rep_map = await self.get_replacement_map()
        return rep_map.get(referrer_id, referrer_id)

    async def sync_all_replacements(self) -> dict:
        """Synchronizes all replaced users: transfers balance, total_earned, level, wallets, referrals and payment logs."""
        try:
            replacements = await self.get_all_replacements()
            if not replacements:
                return {"success": True, "count": 0, "message": "Almashtirilgan foydalanuvchilar topilmadi"}

            synced_count = 0
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                for r in replacements:
                    old_id = r.get("old_user_id")
                    new_id = r.get("new_user_id")
                    if not old_id or not new_id or old_id == new_id:
                        continue

                    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (old_id,))
                    old_u_row = await cursor.fetchone()
                    cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (new_id,))
                    new_u_row = await cursor.fetchone()

                    if not old_u_row or not new_u_row:
                        continue

                    old_u = dict(old_u_row)
                    new_u = dict(new_u_row)

                    old_balance = float(old_u.get("balance", 0.0) or 0.0)
                    old_total = float(old_u.get("total_earned", 0.0) or 0.0)
                    old_level = int(old_u.get("current_level", 0) or 0)
                    old_visits = int(old_u.get("visits_count", 1) or 1)

                    new_balance = float(new_u.get("balance", 0.0) or 0.0)
                    new_total = float(new_u.get("total_earned", 0.0) or 0.0)
                    new_level = int(new_u.get("current_level", 1) or 1)
                    new_visits = int(new_u.get("visits_count", 1) or 1)

                    final_level = max(new_level, old_level)
                    final_balance = new_balance + old_balance
                    final_total = new_total + old_total
                    final_visits = max(new_visits, old_visits)

                    final_card = new_u.get("wallet_card") or old_u.get("wallet_card") or ""
                    final_bep20 = new_u.get("wallet_bep20") or old_u.get("wallet_bep20") or ""
                    final_trc20 = new_u.get("wallet_trc20") or old_u.get("wallet_trc20") or ""
                    final_payeer = new_u.get("wallet_payeer") or old_u.get("wallet_payeer") or ""

                    # Update new user with combined earnings, highest level, and wallet data
                    await db.execute(
                        """
                        UPDATE users SET
                            current_level = ?,
                            balance = ?,
                            total_earned = ?,
                            wallet_card = ?,
                            wallet_bep20 = ?,
                            wallet_trc20 = ?,
                            wallet_payeer = ?,
                            visits_count = ?,
                            is_banned = 0
                        WHERE user_id = ?
                        """,
                        (final_level, final_balance, final_total, final_card, final_bep20, final_trc20, final_payeer, final_visits, new_id)
                    )

                    # Reset old detached user
                    await db.execute(
                        """
                        UPDATE users SET
                            current_level = 0,
                            balance = 0.0,
                            total_earned = 0.0,
                            referrer_id = 0,
                            status = '🌱 Boshlang''ich'
                        WHERE user_id = ?
                        """,
                        (old_id,)
                    )

                    # Reassign all old children
                    await db.execute(
                        "UPDATE users SET referrer_id = ? WHERE (referrer_id = ? OR CAST(referrer_id AS TEXT) = ?) AND user_id != ?",
                        (new_id, old_id, str(old_id), new_id)
                    )

                    # Update payment logs
                    await db.execute("UPDATE payment_logs SET curator_id = ? WHERE curator_id = ?", (new_id, old_id))
                    await db.execute("UPDATE payment_logs SET buyer_id = ? WHERE buyer_id = ?", (new_id, old_id))

                    synced_count += 1

                await db.commit()

            # Refresh ranks
            for r in replacements:
                if r.get("new_user_id"):
                    await self.update_user_rank(int(r["new_user_id"]))
                if r.get("old_user_id"):
                    await self.update_user_rank(int(r["old_user_id"]))

            return {
                "success": True,
                "count": synced_count,
                "message": f"{synced_count} ta a'zoning barcha darajalari, ishlagan pullari va strukturalari muvaffaqiyatli sinxronlandi!"
            }
        except Exception as e:
            return {"success": False, "error": str(e)}

    async def replace_user_in_tree(self, target_user_id: int, new_user_identifier: str, requester_id: int) -> dict:
        """Replaces target_user with new_user in the referral tree and transfers all balance, earnings, level, wallets, and structure."""
        new_user = await self.find_or_create_user_by_identifier(new_user_identifier)
        if not new_user:
            return {"success": False, "error": "Yangi foydalanuvchi topilmadi yoki kiritilmadi"}

        new_user_id = new_user["user_id"]
        if new_user_id == target_user_id:
            return {"success": False, "error": "Ayni bir xil foydalanuvchini almashtirib bo'lmaydi"}

        target_user = await self.get_user(target_user_id)
        if not target_user:
            return {"success": False, "error": "Almashtiriluvchi foydalanuvchi topilmadi"}

        # Check authorization (strictly only ADMINS or web admin panel)
        if requester_id not in ADMINS and requester_id not in (1001, 0) and ADMINS:
            return {"success": False, "error": "Faqatgina adminlar a'zolarni almashtirish huquqiga ega"}

        parent_id = target_user.get("referrer_id", 0)

        # Read old user stats to transfer
        target_level = int(target_user.get("current_level", 1) or 1)
        target_balance = float(target_user.get("balance", 0.0) or 0.0)
        target_total_earned = float(target_user.get("total_earned", 0.0) or 0.0)
        target_visits = int(target_user.get("visits_count", 1) or 1)
        target_card = target_user.get("wallet_card", "") or ""
        target_bep20 = target_user.get("wallet_bep20", "") or ""
        target_trc20 = target_user.get("wallet_trc20", "") or ""
        target_payeer = target_user.get("wallet_payeer", "") or ""

        # Calculate merged new stats
        new_level = int(new_user.get("current_level", 1) or 1)
        new_balance = float(new_user.get("balance", 0.0) or 0.0)
        new_total_earned = float(new_user.get("total_earned", 0.0) or 0.0)
        new_visits = int(new_user.get("visits_count", 1) or 1)

        final_level = max(new_level, target_level)
        final_balance = new_balance + target_balance
        final_total_earned = new_total_earned + target_total_earned
        final_visits = max(new_visits, target_visits)

        final_card = new_user.get("wallet_card") or target_card
        final_bep20 = new_user.get("wallet_bep20") or target_bep20
        final_trc20 = new_user.get("wallet_trc20") or target_trc20
        final_payeer = new_user.get("wallet_payeer") or target_payeer

        async with aiosqlite.connect(self.db_path) as db:
            # 1. Update new_user with target's position, level, balance, earnings, wallets
            await db.execute(
                """
                UPDATE users SET
                    referrer_id = ?,
                    current_level = ?,
                    balance = ?,
                    total_earned = ?,
                    wallet_card = ?,
                    wallet_bep20 = ?,
                    wallet_trc20 = ?,
                    wallet_payeer = ?,
                    visits_count = ?,
                    is_banned = 0
                WHERE user_id = ?
                """,
                (
                    parent_id,
                    final_level,
                    final_balance,
                    final_total_earned,
                    final_card,
                    final_bep20,
                    final_trc20,
                    final_payeer,
                    final_visits,
                    new_user_id
                )
            )

            # 2. Reassign target's children to new_user
            await db.execute(
                "UPDATE users SET referrer_id = ? WHERE (referrer_id = ? OR CAST(referrer_id AS TEXT) = ?) AND user_id != ?",
                (new_user_id, target_user_id, str(target_user_id), new_user_id)
            )

            # 3. Transfer payment logs where target was curator or buyer
            await db.execute("UPDATE payment_logs SET curator_id = ? WHERE curator_id = ?", (new_user_id, target_user_id))
            await db.execute("UPDATE payment_logs SET buyer_id = ? WHERE buyer_id = ?", (new_user_id, target_user_id))

            # 4. Detach and reset target_user
            await db.execute(
                """
                UPDATE users SET
                    referrer_id = 0,
                    current_level = 0,
                    balance = 0.0,
                    total_earned = 0.0,
                    status = '🌱 Boshlang''ich'
                WHERE user_id = ?
                """,
                (target_user_id,)
            )

            # 5. Record in user_replacements table
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "INSERT OR REPLACE INTO user_replacements (old_user_id, new_user_id, replaced_at) VALUES (?, ?, ?)",
                (target_user_id, new_user_id, now)
            )
            await db.commit()

        if parent_id:
            await self.update_user_rank(parent_id)
        await self.update_user_rank(new_user_id)
        await self.update_user_rank(target_user_id)

        target_name = f"{target_user.get('first_name', '')} {target_user.get('last_name', '')}".strip() or str(target_user_id)
        new_name = f"{new_user.get('first_name', '')} {new_user.get('last_name', '')}".strip() or str(new_user_id)

        await self.log_activity(
            requester_id,
            "TREE_REPLACE_USER",
            f"{target_name} (ID: {target_user_id}) o'rniga {new_name} (ID: {new_user_id}) to'liq almashtirildi: "
            f"Daraja: {final_level}, Balans: {final_balance:,.0f} so'm, Jami daromad: {final_total_earned:,.0f} so'm, "
            f"barcha bolalari va to'lovlari o'tkazildi"
        )

        return {
            "success": True,
            "message": (
                f"Foydalanuvchi muvaffaqiyatli almashtirildi!\n"
                f"👤 Yangi a'zo: {new_name} (ID: {new_user_id})\n"
                f"⚡️ Daraja: {final_level}-bosqich\n"
                f"💰 O'tkazilgan balans: {final_balance:,.0f} so'm\n"
                f"📈 Jami daromad: {final_total_earned:,.0f} so'm\n"
                f"👥 Barcha referallar va to'lovlar biriktirildi."
            ),
            "new_user": new_user
        }

    async def transfer_referrals(self, from_user_identifier: str, to_user_identifier: str, requester_id: int) -> dict:
        """Transfers all referrals, level, balance, earnings, and payment logs of from_user to to_user and saves alias."""
        if requester_id not in ADMINS and requester_id not in (1001, 0) and ADMINS:
            return {"success": False, "error": "Faqatgina adminlar referallarni ko'chirish huquqiga ega"}

        from_user_id = 0
        from_name = ""
        clean_from = str(from_user_identifier).strip().replace("@", "")
        if clean_from.isdigit():
            from_user_id = int(clean_from)
            from_user = await self.get_user(from_user_id)
            from_name = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip() if from_user else f"ID: {from_user_id}"
        else:
            from_user = await self.get_user_by_username(clean_from)
            if from_user:
                from_user_id = from_user["user_id"]
                from_name = f"{from_user.get('first_name', '')} {from_user.get('last_name', '')}".strip() or f"@{clean_from}"
            else:
                return {"success": False, "error": f"Eski foydalanuvchi (@{clean_from}) topilmadi"}

        to_user = await self.find_or_create_user_by_identifier(to_user_identifier)
        if not to_user:
            return {"success": False, "error": "Yangi foydalanuvchi topilmadi"}

        to_user_id = to_user["user_id"]
        to_name = f"{to_user.get('first_name', '')} {to_user.get('last_name', '')}".strip() or str(to_user_id)

        if from_user_id == to_user_id:
            return {"success": False, "error": "Bir xil foydalanuvchiga ko'chirib bo'lmaydi"}

        # Transfer stats & balance if from_user exists
        from_balance = float(from_user.get("balance", 0.0) or 0.0) if from_user else 0.0
        from_total = float(from_user.get("total_earned", 0.0) or 0.0) if from_user else 0.0
        from_level = int(from_user.get("current_level", 0) or 0) if from_user else 0

        to_balance = float(to_user.get("balance", 0.0) or 0.0) + from_balance
        to_total = float(to_user.get("total_earned", 0.0) or 0.0) + from_total
        to_level = max(int(to_user.get("current_level", 1) or 1), from_level)

        final_card = to_user.get("wallet_card") or (from_user.get("wallet_card") if from_user else "") or ""
        final_bep20 = to_user.get("wallet_bep20") or (from_user.get("wallet_bep20") if from_user else "") or ""
        final_trc20 = to_user.get("wallet_trc20") or (from_user.get("wallet_trc20") if from_user else "") or ""
        final_payeer = to_user.get("wallet_payeer") or (from_user.get("wallet_payeer") if from_user else "") or ""

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM users WHERE (referrer_id = ? OR CAST(referrer_id AS TEXT) = ?) AND user_id != ?",
                (from_user_id, str(from_user_id), to_user_id)
            )
            count = (await cursor.fetchone())[0]

            # 1. Update referrals to point to to_user_id
            await db.execute(
                "UPDATE users SET referrer_id = ? WHERE (referrer_id = ? OR CAST(referrer_id AS TEXT) = ?) AND user_id != ?",
                (to_user_id, from_user_id, str(from_user_id), to_user_id)
            )

            # 2. Update to_user with merged stats & wallets
            await db.execute(
                """
                UPDATE users SET
                    current_level = ?,
                    balance = ?,
                    total_earned = ?,
                    wallet_card = ?,
                    wallet_bep20 = ?,
                    wallet_trc20 = ?,
                    wallet_payeer = ?
                WHERE user_id = ?
                """,
                (to_level, to_balance, to_total, final_card, final_bep20, final_trc20, final_payeer, to_user_id)
            )

            # 3. Reset from_user
            if from_user:
                await db.execute(
                    """
                    UPDATE users SET
                        current_level = 0,
                        balance = 0.0,
                        total_earned = 0.0,
                        referrer_id = 0,
                        status = '🌱 Boshlang''ich'
                    WHERE user_id = ?
                    """,
                    (from_user_id,)
                )

            # 4. Transfer payment logs
            await db.execute("UPDATE payment_logs SET curator_id = ? WHERE curator_id = ?", (to_user_id, from_user_id))
            await db.execute("UPDATE payment_logs SET buyer_id = ? WHERE buyer_id = ?", (to_user_id, from_user_id))

            # 5. Record in user_replacements table
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "INSERT OR REPLACE INTO user_replacements (old_user_id, new_user_id, replaced_at) VALUES (?, ?, ?)",
                (from_user_id, to_user_id, now)
            )
            await db.commit()

        if from_user_id:
            await self.update_user_rank(from_user_id)
        await self.update_user_rank(to_user_id)

        await self.log_activity(
            requester_id,
            "TREE_TRANSFER_REFERRALS",
            f"{count} ta referal, daraja ({to_level}), balans ({to_balance:,.0f} so'm) {from_name} ({from_user_id}) dan {to_name} ({to_user_id}) ga biriktirildi"
        )

        return {
            "success": True,
            "count": count,
            "message": (
                f"{count} ta referal, {to_level}-daraja va {to_balance:,.0f} so'm daromad "
                f"muvaffaqiyatli {to_name} (ID: {to_user_id}) ga biriktirildi!"
            ),
            "to_user": to_user
        }

    async def insert_user_in_between(self, target_user_id: int, new_user_identifier: str, requester_id: int, mode: str = "above") -> dict:
        """Inserts new_user between parent and target ('above') or between target and target's children ('below')."""
        new_user = await self.find_or_create_user_by_identifier(new_user_identifier)
        if not new_user:
            return {"success": False, "error": "Yangi foydalanuvchi topilmadi"}

        new_user_id = new_user["user_id"]
        if new_user_id == target_user_id:
            return {"success": False, "error": "Ayni bir xil foydalanuvchini qo'shib bo'lmaydi"}

        target_user = await self.get_user(target_user_id)
        if not target_user:
            return {"success": False, "error": "Maqsadli foydalanuvchi topilmadi"}

        if requester_id not in ADMINS and requester_id not in (1001, 0) and ADMINS:
            return {"success": False, "error": "Faqatgina adminlar zanjirga a'zo qo'shish huquqiga ega"}

        async with aiosqlite.connect(self.db_path) as db:
            if mode == "above":
                # Parent -> new_user -> target_user
                parent_id = target_user.get("referrer_id", 0)
                await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (parent_id, new_user_id))
                await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (new_user_id, target_user_id))
            else:
                # Target_user -> new_user -> target's children
                await db.execute("UPDATE users SET referrer_id = ? WHERE referrer_id = ? AND user_id != ?", (new_user_id, target_user_id, new_user_id))
                await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (target_user_id, new_user_id))
            await db.commit()

        await self.update_user_rank(new_user_id)
        await self.update_user_rank(target_user_id)

        await self.log_activity(requester_id, "TREE_INSERT_USER", f"Zanjir orasiga yangi a'zo {new_user_id} ({mode}) qo'shildi")
        return {"success": True, "message": f"Zanjirga yangi hamkor muvaffaqiyatli qo'shildi: {new_user.get('first_name', '')} (ID: {new_user_id})", "new_user": new_user}

    async def move_user_to_new_curator(self, target_user_id: int, new_curator_identifier: str, requester_id: int, force: bool = False) -> dict:
        """Moves target_user and their whole subtree under a new curator."""
        if requester_id not in ADMINS and requester_id not in (1001, 0) and ADMINS:
            return {"success": False, "error": "Faqatgina adminlar kuratorni o'zgartirish huquqiga ega"}

        target_user = await self.get_user(target_user_id)
        if not target_user:
            return {"success": False, "error": "Ko'chiriluvchi foydalanuvchi topilmadi"}

        new_curator = await self.find_or_create_user_by_identifier(new_curator_identifier)
        if not new_curator:
            return {"success": False, "error": "Yangi kurator topilmadi yoki kiritilmadi"}

        new_curator_id = new_curator["user_id"]
        if new_curator_id == target_user_id:
            return {"success": False, "error": "Foydalanuvchini o'ziga kurator qilib bo'lmaydi"}

        # Check for circular loops
        if await self.is_user_in_subtree(target_user_id, new_curator_id):
            return {"success": False, "error": "Xatolik: Yangi kurator ushbu a'zoning quyi tarmog'ida joylashgan (aylana zanjir bo'lib qoladi)."}

        # Check direct referral count of new curator (trio limit is 3)
        direct_count = await self.get_referral_count(new_curator_id)
        curator_name = f"{new_curator.get('first_name', '')} {new_curator.get('last_name', '')}".strip() or str(new_curator_id)
        if direct_count >= 3 and not force:
            return {
                "success": False,
                "is_full": True,
                "direct_count": direct_count,
                "error": f"⚠️ Kurator ({curator_name} [ID: {new_curator_id}]) ning 1-darajali shajarasi to'lgan (hozirda {direct_count} ta to'g'ridan-to'g'ri referali bor!).",
                "curator": new_curator
            }

        old_parent_id = target_user.get("referrer_id", 0)

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (new_curator_id, target_user_id))
            await db.commit()

        if old_parent_id:
            await self.update_user_rank(old_parent_id)
        await self.update_user_rank(new_curator_id)
        await self.update_user_rank(target_user_id)

        target_name = f"{target_user.get('first_name', '')} {target_user.get('last_name', '')}".strip() or str(target_user_id)

        await self.log_activity(requester_id, "TREE_MOVE_CURATOR", f"Foydalanuvchi {target_name} ({target_user_id}) yangi kurator {curator_name} ({new_curator_id}) tagiga ko'chirildi")
        return {
            "success": True,
            "message": f"Foydalanuvchi ({target_name}) muvaffaqiyatli yangi kurator ({curator_name} [ID: {new_curator_id}]) tagiga ko'chirildi.",
            "curator": new_curator
        }

    async def remove_user_from_chain_and_reconnect(self, target_user_id: int, requester_id: int) -> dict:
        """Removes target_user from the middle of the referral tree and reconnects target's children directly to target's parent."""
        if requester_id not in ADMINS and requester_id not in (1001, 0) and ADMINS:
            return {"success": False, "error": "Faqatgina adminlar zanjirni tahrirlash huquqiga ega"}

        target_user = await self.get_user(target_user_id)
        if not target_user:
            return {"success": False, "error": "Foydalanuvchi topilmadi"}

        parent_id = target_user.get("referrer_id", 0)

        async with aiosqlite.connect(self.db_path) as db:
            # 1. Reassign target's children to target's parent
            await db.execute("UPDATE users SET referrer_id = ? WHERE referrer_id = ? AND user_id != ?", (parent_id, target_user_id, parent_id))

            # 2. Detach target_user
            await db.execute("UPDATE users SET referrer_id = 0 WHERE user_id = ?", (target_user_id,))
            await db.commit()

        if parent_id:
            await self.update_user_rank(parent_id)
        await self.update_user_rank(target_user_id)

        target_name = f"{target_user.get('first_name', '')} {target_user.get('last_name', '')}".strip() or str(target_user_id)
        parent_user = await self.get_user(parent_id) if parent_id else None
        parent_name = f"{parent_user.get('first_name', '')} {parent_user.get('last_name', '')}".strip() if parent_user else f"Bosh Admin (ID: {parent_id})"

        await self.log_activity(requester_id, "TREE_REMOVE_AND_RECONNECT", f"Foydalanuvchi {target_name} ({target_user_id}) zanjir orasidan chiqarildi va bolalari {parent_id} ga ulandi")
        return {
            "success": True,
            "message": f"Foydalanuvchi ({target_name}) zanjir orasidan xavfsiz chiqarildi. Uning bolalari to'g'ridan-to'g'ri kuratori ({parent_name})ga ulandi."
        }

    async def change_user_referrer(self, user_id: int, new_referrer_id: int):
        async with aiosqlite.connect(self.db_path) as db:
            old_user = await self.get_user(user_id)
            old_ref = old_user.get("referrer_id", 0) if old_user else 0
            await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (new_referrer_id, user_id))
            await db.commit()
            if old_ref:
                await self.update_user_rank(old_ref)
            if new_referrer_id:
                await self.update_user_rank(new_referrer_id)
            await self.log_activity(user_id, "CHANGE_REFERRER", f"Kurator o'zgartirildi: {old_ref} -> {new_referrer_id}")

    async def update_wallet(self, user_id: int, wallet_type: str, wallet_value: str):
        allowed = ["wallet_bep20", "wallet_card", "wallet_trc20", "wallet_payeer"]
        if wallet_type not in allowed:
            return
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(f"UPDATE users SET {wallet_type} = ? WHERE user_id = ?", (wallet_value, user_id))
            await db.commit()

    async def set_user_level(self, user_id: int, level: int):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET current_level = ? WHERE user_id = ?", (level, user_id))
            await db.commit()

    async def add_user_earnings(self, user_id: int, amount: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                UPDATE users SET
                    balance = balance + ?,
                    total_earned = total_earned + ?
                WHERE user_id = ?
                """,
                (amount, amount, user_id)
            )
            await db.commit()
            await self.log_activity(user_id, "EARN", f"Daromad tushdi: +{amount} so'm")

    async def get_referrals(self, user_id: int, offset: int = 0, limit: int = 100):
        rep_map = await self.get_replacement_map()
        alias_ids = [user_id]
        for old_id, new_id in rep_map.items():
            if new_id == user_id and old_id not in alias_ids:
                alias_ids.append(old_id)

        placeholders = ",".join("?" for _ in alias_ids)
        str_placeholders = ",".join("?" for _ in alias_ids)
        params = list(alias_ids) + [str(i) for i in alias_ids] + [limit, offset]

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                f"""
                SELECT * FROM users 
                WHERE (referrer_id IN ({placeholders}) OR CAST(referrer_id AS TEXT) IN ({str_placeholders}))
                ORDER BY registered_at DESC 
                LIMIT ? OFFSET ?
                """, 
                params
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_referral_count(self, user_id: int) -> int:
        rep_map = await self.get_replacement_map()
        alias_ids = [user_id]
        for old_id, new_id in rep_map.items():
            if new_id == user_id and old_id not in alias_ids:
                alias_ids.append(old_id)

        placeholders = ",".join("?" for _ in alias_ids)
        str_placeholders = ",".join("?" for _ in alias_ids)
        params = list(alias_ids) + [str(i) for i in alias_ids]

        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                f"SELECT COUNT(*) FROM users WHERE (referrer_id IN ({placeholders}) OR CAST(referrer_id AS TEXT) IN ({str_placeholders})) AND (is_banned IS NULL OR is_banned = 0)",
                params
            )
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_multi_tier_stats(self, user_id: int) -> dict:
        """Calculates multi-tier team statistics for all 5 marketing levels with replacement support."""
        rep_map = await self.get_replacement_map()
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT user_id, referrer_id FROM users WHERE is_banned IS NULL OR is_banned = 0")
            rows = await cursor.fetchall()

            # Build children lookup map in memory
            children_map: dict[int, list[int]] = {}
            for r in rows:
                u_id = r["user_id"]
                raw_ref = r["referrer_id"]
                ref_id = int(raw_ref) if raw_ref and str(raw_ref).isdigit() else 0
                ref_id = rep_map.get(ref_id, ref_id)
                if ref_id not in children_map:
                    children_map[ref_id] = []
                children_map[ref_id].append(u_id)

            visited = set([user_id])
            current_tier = children_map.get(user_id, [])
            for c in current_tier:
                visited.add(c)

            l1_ids = list(current_tier)
            
            # Level 2
            l2_ids = []
            for p in l1_ids:
                for c in children_map.get(p, []):
                    if c not in visited:
                        visited.add(c)
                        l2_ids.append(c)

            # Level 3
            l3_ids = []
            for p in l2_ids:
                for c in children_map.get(p, []):
                    if c not in visited:
                        visited.add(c)
                        l3_ids.append(c)

            # Level 4
            l4_ids = []
            for p in l3_ids:
                for c in children_map.get(p, []):
                    if c not in visited:
                        visited.add(c)
                        l4_ids.append(c)

            # Level 5
            l5_ids = []
            for p in l4_ids:
                for c in children_map.get(p, []):
                    if c not in visited:
                        visited.add(c)
                        l5_ids.append(c)

            total_team = len(l1_ids) + len(l2_ids) + len(l3_ids) + len(l4_ids) + len(l5_ids)
            return {
                "level_1": len(l1_ids),
                "level_2": len(l2_ids),
                "level_3": len(l3_ids),
                "level_4": len(l4_ids),
                "level_5": len(l5_ids),
                "total_team": total_team
            }

    async def get_curator_for_level(self, user_id: int, target_level: int) -> int:
        """
        Finds the upline curator for a specific level upgrade.
        Level 1 -> 1st upline (direct referrer)
        Level 2 -> 2nd upline (referrer's referrer)
        Level 3 -> 3rd upline
        ...
        Level N -> N-th upline
        If upline chain breaks or reaches 0, falls back to ADMINS[0].
        """
        admin_default = ADMINS[0] if ADMINS else 0
        if target_level <= 0:
            target_level = 1

        curr_id = user_id
        last_valid_curator = admin_default

        for _ in range(target_level):
            user = await self.get_user(curr_id)
            if not user:
                break
            raw_ref_id = user.get("referrer_id", 0)
            if not raw_ref_id or raw_ref_id == 0:
                break

            ref_id = await self.get_effective_referrer_id(raw_ref_id)
            if not ref_id or ref_id == 0:
                break

            last_valid_curator = ref_id
            curr_id = ref_id

            if ref_id in ADMINS:
                return ref_id

        if curr_id and curr_id != user_id and curr_id != 0:
            return curr_id

        return last_valid_curator if last_valid_curator != user_id else admin_default

    async def get_user_tree(self, user_id: int, max_depth: int = 15) -> dict:
        """Returns deep multi-tier hierarchy structure for visual tree rendering (fast in-memory builder with alias resolution)."""
        try:
            rep_map = await self.get_replacement_map()
            async with aiosqlite.connect(self.db_path) as db_conn:
                db_conn.row_factory = aiosqlite.Row
                # Fetch all unbanned users in one single query
                cursor = await db_conn.execute("SELECT * FROM users WHERE is_banned IS NULL OR is_banned = 0 ORDER BY registered_at ASC")
                all_users = [dict(r) for r in await cursor.fetchall()]

            users_by_id: dict[int, dict] = {}
            children_map: dict[int, list[dict]] = {}

            for u in all_users:
                uid = u["user_id"]
                users_by_id[uid] = u
                raw_ref = u.get("referrer_id", 0)
                ref_id = int(raw_ref) if raw_ref and str(raw_ref).isdigit() else 0
                ref_id = rep_map.get(ref_id, ref_id)
                if ref_id not in children_map:
                    children_map[ref_id] = []
                children_map[ref_id].append(u)

            root_user = users_by_id.get(user_id)
            if not root_user:
                return {
                    "user_id": user_id,
                    "first_name": "Siz",
                    "last_name": "",
                    "username": "",
                    "current_level": 0,
                    "status": "🌱 Boshlang'ich",
                    "total_earned": 0,
                    "registered_at": "",
                    "children": []
                }

            visited = set()

            def _build_node(u_dict: dict, depth: int) -> dict:
                uid = u_dict.get("user_id", 0)
                visited.add(uid)
                children_nodes = []
                if depth < max_depth:
                    for ch in children_map.get(uid, []):
                        ch_id = ch.get("user_id", 0)
                        if ch_id not in visited:
                            children_nodes.append(_build_node(ch, depth + 1))

                return {
                    "user_id": uid,
                    "first_name": u_dict.get("first_name", ""),
                    "last_name": u_dict.get("last_name", ""),
                    "username": u_dict.get("username", ""),
                    "current_level": u_dict.get("current_level", 1),
                    "status": u_dict.get("status", "🌱 Boshlang'ich"),
                    "total_earned": u_dict.get("total_earned", 0.0),
                    "registered_at": u_dict.get("registered_at", ""),
                    "referrer_id": u_dict.get("referrer_id", 0),
                    "children": children_nodes
                }

            return _build_node(root_user, 0)
        except Exception as e:
            return {
                "user_id": user_id,
                "first_name": "Siz",
                "last_name": "",
                "username": "",
                "current_level": 0,
                "status": "🌱 Boshlang'ich",
                "total_earned": 0,
                "registered_at": "",
                "children": []
            }

    async def get_top_leaders(self, limit: int = 20):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            query = """
                SELECT u.user_id, u.first_name, u.last_name, u.username, u.status, u.current_level, u.total_earned,
                       COUNT(r.user_id) as direct_count
                FROM users u
                LEFT JOIN users r ON r.referrer_id = u.user_id AND r.is_banned = 0
                WHERE u.is_banned = 0
                GROUP BY u.user_id
                ORDER BY direct_count DESC, u.total_earned DESC
                LIMIT ?
            """
            cursor = await db.execute(query, (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def update_user_rank(self, user_id: int):
        if user_id in ADMINS:
            rank = "👑 Admin"
        else:
            count = await self.get_referral_count(user_id)
            if count >= 50:
                rank = "💎 VIP Diamond Lider"
            elif count >= 20:
                rank = "🥇 Oltin Hamkor"
            elif count >= 8:
                rank = "🥈 Kumush Hamkor"
            elif count >= 3:
                rank = "🥉 Bronza Hamkor"
            else:
                rank = "🌱 Boshlang'ich"

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE users SET status = ? WHERE user_id = ?", (rank, user_id))
            await db.commit()

    async def get_all_users(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM users ORDER BY registered_at DESC")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_filtered_user_ids(self, filter_type: str = "all") -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            if filter_type == "lvl1":
                cursor = await db.execute("SELECT user_id FROM users WHERE current_level = 1 AND is_banned = 0")
            elif filter_type == "lvl2_plus":
                cursor = await db.execute("SELECT user_id FROM users WHERE current_level >= 2 AND is_banned = 0")
            elif filter_type == "admins":
                cursor = await db.execute("SELECT user_id FROM users WHERE status LIKE '%Admin%'")
            elif filter_type == "inactive":
                cursor = await db.execute("SELECT user_id FROM users WHERE visits_count <= 1 AND is_banned = 0")
            else:
                cursor = await db.execute("SELECT user_id FROM users WHERE is_banned = 0")
            rows = await cursor.fetchall()
            return [r[0] for r in rows]

    async def get_level_settings(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM level_settings ORDER BY level ASC")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def update_level_price(self, level: int, price: float, name: str = None):
        async with aiosqlite.connect(self.db_path) as db:
            if name:
                await db.execute("UPDATE level_settings SET price = ?, name = ? WHERE level = ?", (price, name, level))
            else:
                await db.execute("UPDATE level_settings SET price = ? WHERE level = ?", (price, level))
            await db.commit()

    async def get_active_announcement(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM announcements WHERE is_active = 1 ORDER BY id DESC LIMIT 1")
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def set_active_announcement(self, title: str, text: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE announcements SET is_active = 0")
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute("INSERT INTO announcements (title, text, is_active, created_at) VALUES (?, ?, 1, ?)", (title, text, now))
            await db.commit()

    async def delete_announcements(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("UPDATE announcements SET is_active = 0")
            await db.commit()

    async def log_activity(self, user_id: int, action: str, details: str):
        try:
            async with aiosqlite.connect(self.db_path) as db:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                await db.execute("INSERT INTO activity_logs (user_id, action, details, created_at) VALUES (?, ?, ?, ?)", (user_id, action, details, now))
                await db.commit()
        except Exception:
            pass

    async def get_recent_logs(self, limit: int = 50):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def save_broadcast(self, text: str, photo_url: str, button_text: str, button_url: str, target_filter: str, sent_count: int, fail_count: int):
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                """
                INSERT INTO broadcast_history (text, photo_url, button_text, button_url, target_filter, sent_count, fail_count, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (text, photo_url, button_text, button_url, target_filter, sent_count, fail_count, now)
            )
            await db.commit()

    async def get_broadcast_history(self, limit: int = 20):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM broadcast_history ORDER BY id DESC LIMIT ?", (limit,))
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_total_users_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def add_payment_log(self, buyer_id: int, curator_id: int, level: int, amount: float):
        """Foydalanuvchi 'Я оплатил' bosganda pending to'lov yozadi."""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "INSERT INTO payment_logs (buyer_id, curator_id, level, amount, status, created_at) VALUES (?, ?, ?, ?, 'pending', ?)",
                (buyer_id, curator_id, level, amount, now)
            )
            await db.commit()

    async def confirm_payment_log(self, buyer_id: int, level: int):
        """Kurator tasdiqlanganda to'lovni 'confirmed' deb belgilaydi."""
        async with aiosqlite.connect(self.db_path) as db:
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                "UPDATE payment_logs SET status = 'confirmed', confirmed_at = ? WHERE buyer_id = ? AND level = ? AND status = 'pending'",
                (now, buyer_id, level)
            )
            await db.commit()

    async def get_all_payment_logs(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM payment_logs ORDER BY id DESC")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_all_activity_logs(self):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute("SELECT * FROM activity_logs ORDER BY id DESC LIMIT 500")
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    # ==================== MULTI-ACCOUNT & OTP VERIFICATION METHODS ====================

    async def find_user_by_query(self, query: str) -> dict:
        """
        Qidiruv: Telegram @username, user_id (raqamli ID), yoki telefon raqam orqali foydalanuvchini topadi.
        """
        clean = str(query).strip()
        if not clean:
            return None

        uname_query = clean.lstrip("@").lower()
        digits_only = "".join(ch for ch in clean if ch.isdigit())

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row

            # 1. ID raqami bo'yicha qidirish
            if digits_only and (clean.isdigit() or len(digits_only) <= 10):
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (int(digits_only),))
                row = await cursor.fetchone()
                if row:
                    return dict(row)

            # 2. @username bo'yicha qidirish
            if uname_query:
                cursor = await db.execute("SELECT * FROM users WHERE LOWER(username) = ?", (uname_query,))
                row = await cursor.fetchone()
                if row:
                    return dict(row)

            # 3. Telefon raqami bo'yicha qidirish
            if digits_only and len(digits_only) >= 7:
                cursor = await db.execute(
                    """
                    SELECT * FROM users 
                    WHERE phone != '' AND (
                        phone = ? 
                        OR phone LIKE ? 
                        OR REPLACE(REPLACE(REPLACE(phone, '+', ''), ' ', ''), '-', '') LIKE ?
                    )
                    """,
                    (clean, f"%{digits_only}%", f"%{digits_only}%")
                )
                row = await cursor.fetchone()
                if row:
                    return dict(row)

            # 4. Qo'shimcha tekshiruv
            if clean.isdigit():
                cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (int(clean),))
                row = await cursor.fetchone()
                if row:
                    return dict(row)

            return None

    async def create_link_otp(self, requester_id: int, target_id: int) -> str:
        """6 xonali bir martalik tasdiqlash kodi generatsiya qiladi (10 daqiqa yaroqli)."""
        code = str(random.randint(100000, 999999))
        now = datetime.now()
        expires = (now + timedelta(minutes=10)).strftime("%Y-%m-%d %H:%M:%S")
        now_str = now.strftime("%Y-%m-%d %H:%M:%S")

        async with aiosqlite.connect(self.db_path) as db:
            # Eski kutayotgan so'rovlarni bekor qilish
            await db.execute(
                "UPDATE account_link_otps SET status = 'cancelled' WHERE requester_id = ? AND target_id = ? AND status = 'pending'",
                (requester_id, target_id)
            )
            await db.execute(
                "INSERT INTO account_link_otps (requester_id, target_id, code, created_at, expires_at, status) VALUES (?, ?, ?, ?, ?, 'pending')",
                (requester_id, target_id, code, now_str, expires)
            )
            await db.commit()
        return code

    async def verify_link_otp(self, requester_id: int, target_id: int, code: str) -> bool:
        """Kodni yoki botdagi tasdiqlash holatini tekshiradi va akkauntlarni biriktiradi."""
        clean_code = str(code).strip()
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM account_link_otps 
                WHERE requester_id = ? AND target_id = ? 
                  AND (status = 'approved' OR (status = 'pending' AND code = ? AND expires_at >= ?))
                ORDER BY id DESC LIMIT 1
                """,
                (requester_id, target_id, clean_code, now_str)
            )
            row = await cursor.fetchone()
            if not row:
                return False

            otp_id = row["id"]
            await db.execute("UPDATE account_link_otps SET status = 'used' WHERE id = ?", (otp_id,))

            # Har ikki akkauntni o'zaro bog'lash (ikki tomonlama)
            await db.execute(
                "INSERT OR IGNORE INTO linked_accounts (owner_id, linked_id, created_at) VALUES (?, ?, ?)",
                (requester_id, target_id, now_str)
            )
            await db.execute(
                "INSERT OR IGNORE INTO linked_accounts (owner_id, linked_id, created_at) VALUES (?, ?, ?)",
                (target_id, requester_id, now_str)
            )
            await db.commit()
            await self.log_activity(requester_id, "LINK_ACCOUNT", f"Akkaunt biriktirildi: {target_id}")
            return True

    async def approve_link_request_by_target(self, target_id: int, requester_id: int) -> bool:
        """Target foydalanuvchi Telegram botdagi [✅ Tasdiqlash] tugmasini bosganda tasdiqlaydi."""
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT id FROM account_link_otps WHERE requester_id = ? AND target_id = ? AND status = 'pending' ORDER BY id DESC LIMIT 1",
                (requester_id, target_id)
            )
            row = await cursor.fetchone()
            if row:
                await db.execute("UPDATE account_link_otps SET status = 'approved' WHERE id = ?", (row["id"],))

            await db.execute(
                "INSERT OR IGNORE INTO linked_accounts (owner_id, linked_id, created_at) VALUES (?, ?, ?)",
                (requester_id, target_id, now_str)
            )
            await db.execute(
                "INSERT OR IGNORE INTO linked_accounts (owner_id, linked_id, created_at) VALUES (?, ?, ?)",
                (target_id, requester_id, now_str)
            )
            await db.commit()
            return True

    async def reject_link_request_by_target(self, target_id: int, requester_id: int) -> bool:
        """Target foydalanuvchi Telegram botdagi [❌ Rad etish] tugmasini bosganda bekor qiladi."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE account_link_otps SET status = 'rejected' WHERE requester_id = ? AND target_id = ? AND status = 'pending'",
                (requester_id, target_id)
            )
            await db.commit()
            return True

    async def get_linked_accounts_for_user(self, user_id: int) -> list:
        """Foydalanuvchiga biriktirilgan barcha tasdiqlangan akkauntlarni qaytaradi (almashtirilgan ID larni to'liq inobatga olgan holda)."""
        rep_map = await self.get_replacement_map()

        # All alias IDs for this user
        owner_ids = [user_id]
        for old_id, new_id in rep_map.items():
            if new_id == user_id and old_id not in owner_ids:
                owner_ids.append(old_id)
            if old_id == user_id and new_id not in owner_ids:
                owner_ids.append(new_id)

        placeholders = ",".join("?" for _ in owner_ids)
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                f"""
                SELECT la.linked_id, u.user_id, u.first_name, u.last_name, u.username, u.phone, u.current_level, u.balance, u.total_earned, u.status
                FROM linked_accounts la
                LEFT JOIN users u ON (u.user_id = la.linked_id)
                WHERE la.owner_id IN ({placeholders})
                ORDER BY la.id ASC
                """,
                owner_ids
            )
            rows = await cursor.fetchall()

            result = []
            seen_ids = set([user_id] + owner_ids)
            for r in rows:
                raw_linked_id = r["linked_id"]
                effective_id = rep_map.get(raw_linked_id, raw_linked_id)
                if effective_id in seen_ids:
                    continue
                seen_ids.add(effective_id)

                # Fetch fresh real-time user row
                u_row = await self.get_user(effective_id)
                if u_row:
                    result.append({
                        "user_id": u_row["user_id"],
                        "first_name": u_row.get("first_name", ""),
                        "last_name": u_row.get("last_name", ""),
                        "username": u_row.get("username", ""),
                        "phone": u_row.get("phone", ""),
                        "current_level": u_row.get("current_level", 1),
                        "balance": u_row.get("balance", 0.0),
                        "total_earned": u_row.get("total_earned", 0.0),
                        "status": u_row.get("status", "🌱 Boshlang'ich")
                    })
                elif r["user_id"]:
                    result.append({
                        "user_id": r["user_id"],
                        "first_name": r.get("first_name", ""),
                        "last_name": r.get("last_name", ""),
                        "username": r.get("username", ""),
                        "phone": r.get("phone", ""),
                        "current_level": r.get("current_level", 1),
                        "balance": r.get("balance", 0.0),
                        "total_earned": r.get("total_earned", 0.0),
                        "status": r.get("status", "🌱 Boshlang'ich")
                    })
            return result

    async def remove_linked_account(self, owner_id: int, target_id: int):
        """Akkauntlar o'rtasidagi bog'lanishni o'chiradi."""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "DELETE FROM linked_accounts WHERE (owner_id = ? AND linked_id = ?) OR (owner_id = ? AND linked_id = ?)",
                (owner_id, target_id, target_id, owner_id)
            )
            await db.commit()

db = Database()
