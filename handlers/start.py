import os
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile
from database import db
from keyboards import (
    get_register_keyboard,
    get_main_menu_keyboard,
    get_back_to_menu_keyboard
)
from config import ADMINS

router = Router()

MAIN_MENU_CAPTION = (
    "CONCORD — ham faol, ham passiv daromad olish uchun yuqori salohiyatga ega "
    "qulay dastur. Ko'plab daromad manbalari va moliyaviy vositalar "
    "kapitalingizni ko'paytirishga yordam beradi."
)

BANNER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "concord_banner.png")


async def send_main_menu(bot: Bot, chat_id: int, message_id_to_edit: int = None):
    """Sends or edits the main menu message with banner and buttons."""
    keyboard = get_main_menu_keyboard()
    
    if os.path.exists(BANNER_PATH):
        photo = FSInputFile(BANNER_PATH)
        if message_id_to_edit:
            try:
                await bot.delete_message(chat_id=chat_id, message_id=message_id_to_edit)
            except Exception:
                pass
        await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=MAIN_MENU_CAPTION,
            reply_markup=keyboard
        )
    else:
        if message_id_to_edit:
            try:
                await bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id_to_edit,
                    text=f"🌌 <b>CONCORD</b>\n\n{MAIN_MENU_CAPTION}",
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
                return
            except Exception:
                pass
        await bot.send_message(
            chat_id=chat_id,
            text=f"🌌 <b>CONCORD</b>\n\n{MAIN_MENU_CAPTION}",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    args = command.args
    existing_user = await db.get_user(user.id)

    # If user is already registered, take them straight to the main menu
    if existing_user:
        await send_main_menu(bot, message.chat.id)
        return

    # User is not registered. Check if referral parameter is provided
    if not args:
        # Check if user is admin - allow admin to self-register without ref link
        if user.id in ADMINS:
            await db.register_user(
                user_id=user.id,
                first_name=user.first_name or "",
                last_name=user.last_name or "",
                username=user.username or "",
                referrer_id=0
            )
            await message.answer("👑 <b>Admin sifatida ro'yxatdan o'tdingiz!</b>", parse_mode="HTML")
            await send_main_menu(bot, message.chat.id)
            return

        # Regular user without referral link -> strictly deny access as requested
        await message.answer(
            "⚠️ <b>Botda ro'yxatdan o'tish faqat taklif qiluvchining referal havolasi orqali mumkin.</b>",
            parse_mode="HTML"
        )
        return

    # Parse referral argument (supports 'ref_12345' or '12345')
    ref_str = args.replace("ref_", "").strip()
    if not ref_str.isdigit():
        await message.answer(
            "⚠️ <b>Noto'g'ri referal havola!</b>\nIltimos, taklif qiluvchingiz yuborgan to'g'ri havoladan kiring.",
            parse_mode="HTML"
        )
        return

    referrer_id = int(ref_str)

    # Check if user tries to refer themselves
    if referrer_id == user.id:
        await message.answer(
            "⚠️ <b>Siz o'z referal havolangiz orqali ro'yxatdan o'ta olmaysiz!</b>",
            parse_mode="HTML"
        )
        return

    # Check if referrer exists in DB or is in admin list
    referrer_in_db = await db.get_user(referrer_id)
    referrer_info = None

    if referrer_in_db:
        referrer_info = {
            "first_name": referrer_in_db.get("first_name") or "-",
            "last_name": referrer_in_db.get("last_name") or "-",
            "username": referrer_in_db.get("username") or "-"
        }
    else:
        # Try fetching info directly from Telegram API
        try:
            chat = await bot.get_chat(referrer_id)
            referrer_info = {
                "first_name": chat.first_name or "-",
                "last_name": chat.last_name or "-",
                "username": chat.username or "-"
            }
        except Exception:
            if referrer_id in ADMINS:
                referrer_info = {
                    "first_name": "Admin",
                    "last_name": "Concord",
                    "username": "concord_admin"
                }

    if not referrer_info:
        await message.answer(
            "⚠️ <b>Taklif qiluvchi topilmadi yoki havola eskirgan.</b>\n"
            "Iltimos, to'g'ri referal havoladan foydalaning.",
            parse_mode="HTML"
        )
        return

    # Format Curator (Inviter) & User info card in Uzbek (matching reference/Screenshot_5.png)
    curator_username_display = f"@{referrer_info['username']}" if referrer_info['username'] != "-" else "Mavjud emas"
    user_username_display = f"@{user.username}" if user.username else "Mavjud emas"

    info_card = (
        "🏆 <b>Sizning Kuratoringiz.</b>\n\n"
        f"<b>Ism:</b> {referrer_info['first_name']}\n"
        f"<b>Familiya:</b> {referrer_info['last_name']}\n"
        f"<b>Login:</b> {referrer_info['username']}\n"
        f"<b>Telegram:</b> {curator_username_display}\n\n"
        "🏆 <b>Sizning Ma'lumotlaringiz.</b>\n\n"
        f"<b>Ism:</b> {user.first_name or '-'}\n"
        f"<b>Familiya:</b> {user.last_name or '-'}\n"
        f"<b>Login:</b> {user.username or '-'}\n"
        f"<b>Telegram:</b> {user_username_display}"
    )

    await message.answer(
        info_card,
        reply_markup=get_register_keyboard(referrer_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_reg:"))
async def confirm_registration_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user
    data_parts = callback.data.split(":")
    referrer_id = int(data_parts[1]) if len(data_parts) > 1 and data_parts[1].isdigit() else 0

    # Save to database
    await db.register_user(
        user_id=user.id,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        username=user.username or "",
        referrer_id=referrer_id
    )

    await callback.answer("✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!", show_alert=False)

    # Notify inviter (referrer)
    if referrer_id and referrer_id != user.id:
        try:
            username_tag = f"(@{user.username})" if user.username else ""
            await bot.send_message(
                chat_id=referrer_id,
                text=(
                    "🎉 <b>Yangi hamkor!</b>\n\n"
                    f"Sizning referal havolangiz orqali yangi a'zo ro'yxatdan o'tdi:\n"
                    f"👤 <b>{user.full_name}</b> {username_tag}\n"
                    f"🆔 ID: <code>{user.id}</code>"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Send Main Menu
    await send_main_menu(bot, callback.message.chat.id, message_id_to_edit=callback.message.message_id)


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    await send_main_menu(bot, callback.message.chat.id, message_id_to_edit=callback.message.message_id)


@router.callback_query(F.data == "menu_header")
async def menu_header_handler(callback: CallbackQuery):
    await callback.answer("♦️ CONCORD — Asosiy Menyu ♦️", show_alert=False)
