import json
import logging
from datetime import datetime
from aiogram import Bot
from aiogram.types import BufferedInputFile
from config import BACKUP_CHANNEL_ID
from database.db import db

logger = logging.getLogger(__name__)

async def export_database_to_js_bytes() -> tuple[bytes, str, int]:
    """Exports all database tables to a formatted .js file content."""
    users = await db.get_all_users()
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    timestamp_filename = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"database_backup_{timestamp_filename}.js"

    # Build multi-tier structures and full database dict
    db_export = {
        "project": "CONCORD / BUYUK HAYOTGA YO'L",
        "exported_at": now_str,
        "total_users": len(users),
        "users": users
    }

    # Format as JavaScript file
    js_content = (
        f"// ==========================================\n"
        f"// CONCORD DATABASE BACKUP\n"
        f"// Exported at: {now_str}\n"
        f"// Total Users: {len(users)}\n"
        f"// Channel ID: {BACKUP_CHANNEL_ID}\n"
        f"// ==========================================\n\n"
        f"const CONCORD_DATABASE = {json.dumps(db_export, indent=2, ensure_ascii=False)};\n\n"
        f"// CommonJS & ES Module Export Support\n"
        f"if (typeof module !== 'undefined' && module.exports) {{\n"
        f"  module.exports = CONCORD_DATABASE;\n"
        f"}}\n"
        f"if (typeof window !== 'undefined') {{\n"
        f"  window.CONCORD_DATABASE = CONCORD_DATABASE;\n"
        f"}}\n"
    )

    return js_content.encode("utf-8"), filename, len(users)


async def send_database_backup_to_channel(bot: Bot, reason: str = "Avtomatik zaxiralash") -> bool:
    """Exports database as .js and sends to the configured channel."""
    if not BACKUP_CHANNEL_ID:
        return False

    try:
        js_bytes, filename, count = await export_database_to_js_bytes()
        document = BufferedInputFile(js_bytes, filename=filename)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        caption = (
            f"📦 <b>DATABASE BACKUP (.js)</b>\n\n"
            f"🎯 <b>Sabab:</b> {reason}\n"
            f"📅 <b>Vaqt:</b> {now_str}\n"
            f"👥 <b>Jami foydalanuvchilar:</b> {count} ta\n"
            f"📁 <b>Fayl:</b> <code>{filename}</code>"
        )

        await bot.send_document(
            chat_id=BACKUP_CHANNEL_ID,
            document=document,
            caption=caption,
            parse_mode="HTML"
        )
        logger.info(f"✅ Ma'lumotlar bazasi {filename} kanalga ({BACKUP_CHANNEL_ID}) muvaffaqiyatli yuborildi.")
        return True
    except Exception as e:
        logger.error(f"❌ Kanalga backup yuborishda xatolik: {e}")
        return False
