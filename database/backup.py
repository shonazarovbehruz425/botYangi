import re
import json
import logging
import aiosqlite
from io import BytesIO
from datetime import datetime
from aiogram import Bot
from aiogram.types import BufferedInputFile
from config import BACKUP_CHANNEL_ID
from database.db import db

logger = logging.getLogger(__name__)


def extract_json_from_js(js_content: str) -> dict:
    """Parses JSON content embedded in the .js backup file."""
    match = re.search(r'const\s+BUYUK_HAYOT_DATABASE\s*=\s*(\{.*?\});\s*(?://|if|$)', js_content, re.DOTALL)
    if match:
        json_str = match.group(1)
        return json.loads(json_str)

    first_brace = js_content.find('{')
    last_brace = js_content.rfind('}')
    if first_brace != -1 and last_brace != -1:
        json_str = js_content[first_brace:last_brace+1]
        return json.loads(json_str)

    raise ValueError("Zaxira faylidan JSON ma'lumotlarini o'qib bo'lmadi")


async def restore_users_from_dict(db_dict: dict) -> int:
    """Inserts or updates all tables from a backup dictionary into SQLite."""
    users = db_dict.get("users", [])
    payment_logs = db_dict.get("payment_logs", [])
    activity_logs = db_dict.get("activity_logs", [])

    restored_users = 0

    async with aiosqlite.connect(db.db_path) as conn:
        # Restore users
        for u in users:
            await conn.execute(
                """
                INSERT INTO users (
                    user_id, first_name, last_name, username, referrer_id,
                    balance, total_earned, status, current_level,
                    wallet_bep20, wallet_card, wallet_trc20, wallet_payeer,
                    registered_at, is_active, is_banned, visits_count, last_active
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    first_name = excluded.first_name,
                    last_name = excluded.last_name,
                    username = excluded.username,
                    referrer_id = excluded.referrer_id,
                    balance = excluded.balance,
                    total_earned = excluded.total_earned,
                    status = excluded.status,
                    current_level = excluded.current_level,
                    wallet_bep20 = excluded.wallet_bep20,
                    wallet_card = excluded.wallet_card,
                    wallet_trc20 = excluded.wallet_trc20,
                    wallet_payeer = excluded.wallet_payeer,
                    registered_at = excluded.registered_at,
                    is_active = excluded.is_active,
                    is_banned = excluded.is_banned,
                    visits_count = excluded.visits_count,
                    last_active = excluded.last_active
                """,
                (
                    u.get("user_id"),
                    u.get("first_name", ""),
                    u.get("last_name", ""),
                    u.get("username", ""),
                    u.get("referrer_id", 0),
                    u.get("balance", 0.0),
                    u.get("total_earned", 0.0),
                    u.get("status", "🌱 Boshlang'ich"),
                    u.get("current_level", 0),
                    u.get("wallet_bep20", ""),
                    u.get("wallet_card", ""),
                    u.get("wallet_trc20", ""),
                    u.get("wallet_payeer", ""),
                    u.get("registered_at", ""),
                    u.get("is_active", 1),
                    u.get("is_banned", 0),
                    u.get("visits_count", 1),
                    u.get("last_active", "")
                )
            )
            restored_users += 1

        # Restore payment_logs (INSERT OR IGNORE to avoid duplicates)
        for p in payment_logs:
            try:
                await conn.execute(
                    """
                    INSERT OR IGNORE INTO payment_logs
                    (id, buyer_id, curator_id, level, amount, status, created_at, confirmed_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        p.get("id"),
                        p.get("buyer_id"),
                        p.get("curator_id"),
                        p.get("level"),
                        p.get("amount", 0),
                        p.get("status", "pending"),
                        p.get("created_at", ""),
                        p.get("confirmed_at", "")
                    )
                )
            except Exception:
                pass

        # Restore activity_logs (INSERT OR IGNORE to avoid duplicates)
        for a in activity_logs:
            try:
                await conn.execute(
                    """
                    INSERT OR IGNORE INTO activity_logs
                    (id, user_id, action, details, created_at)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (
                        a.get("id"),
                        a.get("user_id"),
                        a.get("action", ""),
                        a.get("details", ""),
                        a.get("created_at", "")
                    )
                )
            except Exception:
                pass

        await conn.commit()

    return restored_users


async def export_database_to_js_bytes() -> tuple:
    """Exports ALL database tables to a formatted .js file with full referral tree."""
    users = await db.get_all_users()
    payment_logs = await db.get_all_payment_logs()
    activity_logs = await db.get_all_activity_logs()

    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"database_backup_{timestamp_filename}.js"

    # Build referral tree: {curator_id: [list of referrals]}
    referral_tree = {}
    for u in users:
        ref_id = u.get("referrer_id", 0)
        if ref_id:
            if ref_id not in referral_tree:
                referral_tree[ref_id] = []
            referral_tree[ref_id].append({
                "user_id": u["user_id"],
                "full_name": f"{u.get('first_name','')} {u.get('last_name','')}".strip(),
                "username": u.get("username", ""),
                "level": u.get("current_level", 0),
                "registered_at": u.get("registered_at", "")
            })

    # Build full database export
    db_export = {
        "project": "BUYUK HAYOTGA YO'L",
        "exported_at": now_str,
        "total_users": len(users),
        "total_payments": len(payment_logs),
        "total_activity_logs": len(activity_logs),
        "users": users,
        "payment_logs": payment_logs,
        "activity_logs": activity_logs,
        "referral_tree": referral_tree
    }

    js_content = (
        f"// ==========================================\n"
        f"// BUYUK HAYOTGA YO'L DATABASE BACKUP\n"
        f"// Exported at: {now_str}\n"
        f"// Total Users: {len(users)}\n"
        f"// Total Payments: {len(payment_logs)}\n"
        f"// Total Activity Logs: {len(activity_logs)}\n"
        f"// Channel ID: {BACKUP_CHANNEL_ID}\n"
        f"// ==========================================\n\n"
        f"const BUYUK_HAYOT_DATABASE = {json.dumps(db_export, indent=2, ensure_ascii=False)};\n\n"
        f"// CommonJS & ES Module Export Support\n"
        f"if (typeof module !== 'undefined' && module.exports) {{\n"
        f"  module.exports = BUYUK_HAYOT_DATABASE;\n"
        f"}}\n"
        f"if (typeof window !== 'undefined') {{\n"
        f"  window.BUYUK_HAYOT_DATABASE = BUYUK_HAYOT_DATABASE;\n"
        f"}}\n"
    )

    return js_content.encode("utf-8"), filename, len(users)


async def send_database_backup_to_channel(bot: Bot, reason: str = "Avtomatik zaxiralash") -> bool:
    """Exports full database as .js, sends to the channel, and PINS it for persistent recovery."""
    if not BACKUP_CHANNEL_ID:
        return False

    try:
        js_bytes, filename, count = await export_database_to_js_bytes()
        document = BufferedInputFile(js_bytes, filename=filename)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Get payment count
        payments = await db.get_all_payment_logs()
        confirmed = sum(1 for p in payments if p.get("status") == "confirmed")

        caption = (
            f"📦 <b>DATABASE BACKUP (.js)</b>\n\n"
            f"🎯 <b>Sabab:</b> {reason}\n"
            f"📅 <b>Vaqt:</b> {now_str}\n"
            f"👥 <b>Jami foydalanuvchilar:</b> {count} ta\n"
            f"💳 <b>Jami to'lovlar:</b> {len(payments)} ta (✅ {confirmed} tasdiqlangan)\n"
            f"📁 <b>Fayl:</b> <code>{filename}</code>"
        )

        sent_msg = await bot.send_document(
            chat_id=BACKUP_CHANNEL_ID,
            document=document,
            caption=caption,
            parse_mode="HTML"
        )

        # Pin the message so bot can always find latest backup on restart
        try:
            await bot.pin_chat_message(
                chat_id=BACKUP_CHANNEL_ID,
                message_id=sent_msg.message_id,
                disable_notification=True
            )
        except Exception as pin_err:
            logger.warning(f"Zaxira faylini qadashda ogohlantirish: {pin_err}")

        logger.info(f"✅ To'liq database {filename} kanalga yuborildi va qadaldi.")
        return True
    except Exception as e:
        logger.error(f"❌ Kanalga backup yuborishda xatolik: {e}")
        return False


async def restore_database_from_channel(bot: Bot) -> int:
    """Restores the latest database backup from the pinned message in BACKUP_CHANNEL_ID."""
    if not BACKUP_CHANNEL_ID:
        return 0

    try:
        chat = await bot.get_chat(chat_id=BACKUP_CHANNEL_ID)
        pinned = chat.pinned_message
        if not pinned or not pinned.document:
            logger.warning("ℹ️ Kanaldan qadalgan (pinned) zaxira fayli topilmadi (baza hali yaratilmagan).")
            return 0

        doc = pinned.document
        logger.info(f"📥 Kanaldan oxirgi zaxira fayli yuklanmoqda: {doc.file_name}")

        file_obj = await bot.get_file(doc.file_id)
        downloaded = await bot.download_file(file_obj.file_path)

        if isinstance(downloaded, BytesIO):
            js_text = downloaded.getvalue().decode("utf-8")
        else:
            js_text = downloaded.read().decode("utf-8")

        db_dict = extract_json_from_js(js_text)
        count = await restore_users_from_dict(db_dict)
        logger.info(f"✅ Ma'lumotlar bazasi kanaldan muvaffaqiyatli tiklandi: {count} ta foydalanuvchi!")
        return count
    except Exception as e:
        logger.error(f"❌ Kanaldan bazani tiklashda xatolik: {e}")
        return 0
