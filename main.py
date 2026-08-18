import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from config import BOT_TOKEN
from database import db
from handlers import setup_routers

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

async def main():
    if not BOT_TOKEN or BOT_TOKEN == "YOUR_BOT_TOKEN_HERE":
        logger.error("❌ BOT_TOKEN belgilanmagan! Iltimos, .env faylida BOT_TOKEN ni kiriting.")
        print("\n" + "="*60)
        print("DIQQAT: .env fayliga Telegram BotFather'dan olingan bot tokeningizni yozing!")
        print("Masalan: BOT_TOKEN=1234567890:ABCdefGhIJKlmNoPQRsTUVwxyZ")
        print("="*60 + "\n")
        return

    # Initialize Database
    await db.init_db()
    logger.info("✅ Ma'lumotlar bazasi ishga tushirildi.")

    # Initialize Bot and Dispatcher
    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # Setup Routers
    setup_routers(dp)

    # Start WebApp Static Server
    from server import start_webapp_server
    webapp_runner = await start_webapp_server()

    logger.info("🚀 Bot ishga tushmoqda...")
    try:
        # Delete webhook before polling
        await bot.delete_webhook(drop_pending_updates=True)
        bot_user = await bot.get_me()
        logger.info(f"🤖 Bot muvaffaqiyatli ishga tushdi: @{bot_user.username}")

        # Configure Menu Button ("Open" / "Mini App")
        from config import WEBAPP_URL
        from aiogram.types import MenuButtonWebApp, WebAppInfo, MenuButtonDefault
        if WEBAPP_URL and WEBAPP_URL.startswith("https://"):
            try:
                await bot.set_chat_menu_button(
                    menu_button=MenuButtonWebApp(
                        text="Open",
                        web_app=WebAppInfo(url=WEBAPP_URL)
                    )
                )
                logger.info(f"✅ Telegram 'Open' menyu tugmasi muvaffaqiyatli o'rnatildi: {WEBAPP_URL}")
            except Exception as btn_err:
                logger.warning(f"Menyu tugmasini o'rnatishda ogohlantirish: {btn_err}")

        # Initial backup & periodic backup background loop
        from database import send_database_backup_to_channel

        async def periodic_backup():
            await asyncio.sleep(5)  # Initial backup 5 seconds after startup
            await send_database_backup_to_channel(bot, reason="Bot ishga tushirildi (Start)")
            while True:
                await asyncio.sleep(3600 * 2)  # Every 2 hours
                await send_database_backup_to_channel(bot, reason="Rejali avtomat zaxiralash (2 soatlik)")

        asyncio.create_task(periodic_backup())

        await dp.start_polling(bot)
    except Exception as e:
        logger.error(f"Xatolik yuz berdi: {e}")
    finally:
        await webapp_runner.cleanup()
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot to'xtatildi.")
