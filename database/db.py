import os
import aiosqlite
from datetime import datetime
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

            # Ensure columns exist if table was created previously
            try:
                await db.execute("ALTER TABLE users ADD COLUMN is_banned INTEGER DEFAULT 0")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE users ADD COLUMN visits_count INTEGER DEFAULT 1")
            except Exception:
                pass
            try:
                await db.execute("ALTER TABLE users ADD COLUMN last_active TEXT DEFAULT ''")
            except Exception:
                pass

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
                (1, 200000, "1-Daraja (200 ming so'm)"),
                (2, 2700000, "2-Daraja (2 mln 700 ming so'm)"),
                (3, 35000000, "3-Daraja (35 mln so'm)"),
                (4, 1377000000, "4-Daraja (1 mlrd 377 mln so'm)"),
                (5, 17100000000, "5-Daraja (17 mlrd 100 mln so'm)"),
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
                    referrer_id = excluded.referrer_id,
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

    async def find_or_create_user_by_identifier(self, identifier: str) -> dict:
        """Finds user by user_id or @username, or registers placeholder if valid numeric ID."""
        clean_id = identifier.strip().lstrip("@")
        if not clean_id:
            return None

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

            # 2. Try finding by username
            cursor = await db.execute("SELECT * FROM users WHERE LOWER(username) = LOWER(?)", (clean_id,))
            row = await cursor.fetchone()
            if row:
                return dict(row)

            # 3. If username not found, generate a pseudo user_id based on hash or random ID to register them
            pseudo_id = 900000000 + abs(hash(clean_id)) % 99999999
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            await db.execute(
                """
                INSERT OR IGNORE INTO users (user_id, first_name, last_name, username, referrer_id, current_level, registered_at)
                VALUES (?, ?, ?, ?, 0, 1, ?)
                """,
                (pseudo_id, clean_id, "", clean_id, now_str)
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

    async def replace_user_in_tree(self, target_user_id: int, new_user_identifier: str, requester_id: int) -> dict:
        """Replaces target_user with new_user in the referral tree."""
        new_user = await self.find_or_create_user_by_identifier(new_user_identifier)
        if not new_user:
            return {"success": False, "error": "Yangi foydalanuvchi topilmadi yoki kiritilmadi"}

        new_user_id = new_user["user_id"]
        if new_user_id == target_user_id:
            return {"success": False, "error": "Ayni bir xil foydalanuvchini almashtirib bo'lmaydi"}

        target_user = await self.get_user(target_user_id)
        if not target_user:
            return {"success": False, "error": "Almashtiriluvchi foydalanuvchi topilmadi"}

        # Check authorization (is requester admin or ancestor)
        is_auth = (requester_id in ADMINS) or await self.is_user_in_subtree(requester_id, target_user_id)
        if not is_auth:
            return {"success": False, "error": "Siz ushbu a'zoni almashtirish huquqiga ega emassiz"}

        parent_id = target_user.get("referrer_id", 0)

        async with aiosqlite.connect(self.db_path) as db:
            # 1. Set new_user's referrer to target's parent
            await db.execute("UPDATE users SET referrer_id = ? WHERE user_id = ?", (parent_id, new_user_id))

            # 2. Reassign target's children to new_user
            await db.execute("UPDATE users SET referrer_id = ? WHERE referrer_id = ? AND user_id != ?", (new_user_id, target_user_id, new_user_id))

            # 3. Detach target_user
            await db.execute("UPDATE users SET referrer_id = 0 WHERE user_id = ?", (target_user_id,))
            await db.commit()

        if parent_id:
            await self.update_user_rank(parent_id)
        await self.update_user_rank(new_user_id)

        await self.log_activity(requester_id, "TREE_REPLACE_USER", f"Foydalanuvchi {target_user_id} o'rniga {new_user_id} (@{new_user.get('username', '')}) almashtirildi")
        return {"success": True, "message": f"Foydalanuvchi muvaffaqiyatli almashtirildi: {new_user.get('first_name', '')} (ID: {new_user_id})", "new_user": new_user}

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

        is_auth = (requester_id in ADMINS) or await self.is_user_in_subtree(requester_id, target_user_id)
        if not is_auth:
            return {"success": False, "error": "Siz ushbu zanjirga a'zo qo'shish huquqiga ega emassiz"}

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
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                """
                SELECT * FROM users 
                WHERE referrer_id = ? 
                ORDER BY registered_at DESC 
                LIMIT ? OFFSET ?
                """, 
                (user_id, limit, offset)
            )
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]

    async def get_referral_count(self, user_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ? AND is_banned = 0", (user_id,))
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_multi_tier_stats(self, user_id: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM users WHERE referrer_id = ? AND is_banned = 0", (user_id,))
            l1_ids = [row[0] for row in await cursor.fetchall()]
            
            l2_ids = []
            if l1_ids:
                placeholders = ",".join("?" for _ in l1_ids)
                cursor = await db.execute(f"SELECT user_id FROM users WHERE referrer_id IN ({placeholders}) AND is_banned = 0", l1_ids)
                l2_ids = [row[0] for row in await cursor.fetchall()]

            l3_ids = []
            if l2_ids:
                placeholders = ",".join("?" for _ in l2_ids)
                cursor = await db.execute(f"SELECT user_id FROM users WHERE referrer_id IN ({placeholders}) AND is_banned = 0", l2_ids)
                l3_ids = [row[0] for row in await cursor.fetchall()]

            total_team = len(l1_ids) + len(l2_ids) + len(l3_ids)
            return {
                "level_1": len(l1_ids),
                "level_2": len(l2_ids),
                "level_3": len(l3_ids),
                "total_team": total_team
            }

    async def get_user_tree(self, user_id: int, max_depth: int = 5) -> dict:
        """Returns deep multi-tier hierarchy structure for visual tree rendering."""
        user = await self.get_user(user_id)
        if not user:
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

        async with aiosqlite.connect(self.db_path) as db_conn:
            db_conn.row_factory = aiosqlite.Row

            async def _fetch_children(parent_id: int, depth: int) -> list:
                if depth > max_depth:
                    return []
                cursor = await db_conn.execute(
                    "SELECT user_id, first_name, last_name, username, current_level, status, total_earned, registered_at FROM users WHERE referrer_id = ? AND is_banned = 0 ORDER BY registered_at ASC",
                    (parent_id,)
                )
                rows = [dict(r) for r in await cursor.fetchall()]
                for row in rows:
                    row["children"] = await _fetch_children(row["user_id"], depth + 1)
                return rows

            children = await _fetch_children(user_id, 1)

            return {
                "user_id": user["user_id"],
                "first_name": user.get("first_name", ""),
                "last_name": user.get("last_name", ""),
                "username": user.get("username", ""),
                "current_level": user.get("current_level", 0),
                "status": user.get("status", "🌱 Boshlang'ich"),
                "total_earned": user.get("total_earned", 0),
                "registered_at": user.get("registered_at", ""),
                "children": children
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

db = Database()
