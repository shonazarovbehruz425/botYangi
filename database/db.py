import aiosqlite
import os
from datetime import datetime
from config import DB_NAME, ADMINS

class Database:
    def __init__(self, db_path: str = DB_NAME):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    first_name TEXT,
                    last_name TEXT,
                    username TEXT,
                    referrer_id INTEGER,
                    balance REAL DEFAULT 0.0,
                    total_earned REAL DEFAULT 30.0,
                    status TEXT DEFAULT 'Boshlang''ich',
                    current_level INTEGER DEFAULT 1,
                    wallet_bep20 TEXT DEFAULT '',
                    wallet_card TEXT DEFAULT '',
                    wallet_trc20 TEXT DEFAULT '',
                    wallet_payeer TEXT DEFAULT '',
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active INTEGER DEFAULT 1
                )
            """)
            await db.commit()

            # Ensure columns exist if table was already created earlier
            columns_to_add = [
                ("wallet_bep20", "TEXT DEFAULT ''"),
                ("wallet_card", "TEXT DEFAULT ''"),
                ("wallet_trc20", "TEXT DEFAULT ''"),
                ("wallet_payeer", "TEXT DEFAULT ''"),
                ("total_earned", "REAL DEFAULT 30.0"),
                ("current_level", "INTEGER DEFAULT 1"),
            ]
            for col_name, col_def in columns_to_add:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                    await db.commit()
                except Exception:
                    pass

            # Ensure admins are auto-registered if not exists as root users
            for admin_id in ADMINS:
                cursor = await db.execute("SELECT user_id FROM users WHERE user_id = ?", (admin_id,))
                user = await cursor.fetchone()
                if not user:
                    await db.execute(
                        """
                        INSERT OR IGNORE INTO users 
                        (user_id, first_name, last_name, username, referrer_id, status, current_level) 
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                        """,
                        (admin_id, "Admin", "Buyuk Hayot", "admin", 0, "👑 Asoschi (Admin)", 6)
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
            default_level = 6 if user_id in ADMINS else 1
            await db.execute(
                """
                INSERT INTO users (user_id, first_name, last_name, username, referrer_id, status, current_level, registered_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    username = excluded.username,
                    referrer_id = excluded.referrer_id
                """,
                (user_id, first_name, last_name, username, referrer_id, status, default_level, now)
            )
            await db.commit()
            await self.update_user_rank(user_id)
            if referrer_id:
                await self.update_user_rank(referrer_id)

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
            cursor = await db.execute("SELECT COUNT(*) FROM users WHERE referrer_id = ?", (user_id,))
            row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_multi_tier_stats(self, user_id: int) -> dict:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT user_id FROM users WHERE referrer_id = ?", (user_id,))
            l1_ids = [row[0] for row in await cursor.fetchall()]
            
            l2_ids = []
            if l1_ids:
                placeholders = ",".join("?" for _ in l1_ids)
                cursor = await db.execute(f"SELECT user_id FROM users WHERE referrer_id IN ({placeholders})", l1_ids)
                l2_ids = [row[0] for row in await cursor.fetchall()]

            l3_ids = []
            if l2_ids:
                placeholders = ",".join("?" for _ in l2_ids)
                cursor = await db.execute(f"SELECT user_id FROM users WHERE referrer_id IN ({placeholders})", l2_ids)
                l3_ids = [row[0] for row in await cursor.fetchall()]

            total_team = len(l1_ids) + len(l2_ids) + len(l3_ids)
            return {
                "level_1": len(l1_ids),
                "level_2": len(l2_ids),
                "level_3": len(l3_ids),
                "total_team": total_team
            }

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

    async def get_total_users_count(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            return row[0] if row else 0

db = Database()
