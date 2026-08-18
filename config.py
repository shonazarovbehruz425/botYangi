import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "YOUR_BOT_TOKEN_HERE")
ADMINS = [int(admin_id.strip()) for admin_id in os.getenv("ADMINS", "123456789").split(",") if admin_id.strip().isdigit()]
DB_NAME = os.getenv("DB_NAME", "concord_bot.db")
WEBAPP_PORT = int(os.getenv("PORT", os.getenv("WEBAPP_PORT", "8080")))
WEBAPP_URL = os.getenv("WEBAPP_URL", f"http://localhost:{WEBAPP_PORT}")
BACKUP_CHANNEL_ID = int(os.getenv("BACKUP_CHANNEL_ID", "-1003949169935"))

