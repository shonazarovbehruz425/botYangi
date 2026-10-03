import os
import unicodedata
import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import CommandStart, CommandObject
from aiogram.types import Message, CallbackQuery, FSInputFile, InputMediaPhoto
from database import db
from keyboards import (
    get_register_keyboard,
    get_invalid_name_keyboard,
    get_main_menu_keyboard,
    get_back_to_menu_keyboard
)
from config import ADMINS

router = Router()

MAIN_MENU_CAPTION = (
    "«BUYUK HAYOTGA YO'L» — ham faol, ham passiv daromad olish uchun yuqori salohiyatga ega "
    "qulay dastur. Ko'plab daromad manbalari va moliyaviy vositalar kapitalingizni ko'paytirishga yordam beradi."
)

BANNER_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "main_banner.png")

INVALID_NAME_TEXT = (
    "⚠️ <b>Ismingizda xatolik aniqlandi!</b>\n\n"
    "Sizning Telegram profilingizdagi ismda <b>haqiqiy harflar</b> mavjud emas (ismingiz faqat nuqta, bo'sh joy, belgi yoki faqat emojilardan iborat).\n\n"
    "Bot tizimida ro'yxatdan o'tish uchun ismingizda kamida <b>harflar</b> (o'zbek, rus yoki lotin alifbosida) qatnashgan bo'lishi shart!\n\n"
    "📝 <b>Nima qilish kerak?</b>\n"
    "1. Telegram sozlamalaringizga (<i>Settings ➔ Edit Name / Изменить имя</i>) kiring.\n"
    "2. Ismingizni harflar bilan to'g'ri yozing (masalan: <i>Ali</i>, <i>Самандар</i> yoki <i>Shamsiddin</i>).\n"
    "3. So'ng quyidagi <b>«🔄 Ismimni to'g'irladim»</b> tugmasini bosing yoki botga qayta /start yuboring.\n\n"
    "Savollar yoki yordam uchun adminga murojaat qiling:\n"
    "👤 <b>Admin:</b> @samandar0855\n"
    "🆔 <b>Admin ID:</b> <code>6003608197</code>"
)


def has_valid_letters(first_name: str, last_name: str = "") -> bool:
    """
    Returns True if first_name or last_name contains at least one alphabetic letter
    in any alphabet/language (Latin, Cyrillic, Russian, Uzbek, etc.).
    """
    full = f"{first_name or ''} {last_name or ''}".strip()
    if not full:
        return False
    for char in full:
        if char.isalpha():
            return True
        cat = unicodedata.category(char)
        if cat.startswith("L"):
            return True
    return False


def validate_user_profile(user, first_name: str = None, last_name: str = None) -> tuple[bool, str]:
    """
    Checks if user meets requirements:
    Name must contain at least one real alphabetic letter.
    Returns (is_valid, error_message)
    """
    if user.id in ADMINS:
        return True, ""

    fn = first_name if first_name is not None else getattr(user, "first_name", "")
    ln = last_name if last_name is not None else getattr(user, "last_name", "")
    if not has_valid_letters(fn, ln):
        return False, INVALID_NAME_TEXT

    return True, ""


async def send_main_menu(target, bot: Bot = None, user_id: int = None, **kwargs):
    """Sends or edits the main menu card with photo banner."""
    uid = None
    if isinstance(target, CallbackQuery):
        uid = target.from_user.id
    elif isinstance(target, Message):
        uid = target.from_user.id
    elif user_id:
        uid = user_id

    keyboard = get_main_menu_keyboard(user_id=uid)
    caption = f"👑 <b>BUYUK HAYOTGA YO'L</b>\n\n{MAIN_MENU_CAPTION}"
    photo = FSInputFile(BANNER_PATH) if os.path.exists(BANNER_PATH) else None

    if isinstance(target, CallbackQuery):
        try:
            if photo:
                await target.message.edit_media(
                    media=InputMediaPhoto(media=photo, caption=caption, parse_mode="HTML"),
                    reply_markup=keyboard
                )
            else:
                await target.message.edit_text(text=caption, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            if photo:
                await target.message.answer_photo(photo=photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
            else:
                await target.message.answer(text=caption, reply_markup=keyboard, parse_mode="HTML")
        try:
            await target.answer()
        except Exception:
            pass
    elif isinstance(target, Message):
        if photo:
            await target.answer_photo(photo=photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            await target.answer(text=caption, reply_markup=keyboard, parse_mode="HTML")
    elif isinstance(target, Bot) and (isinstance(bot, int) or isinstance(user_id, int)):
        chat_id = bot if isinstance(bot, int) else user_id
        if photo:
            await target.send_photo(chat_id=chat_id, photo=photo, caption=caption, reply_markup=keyboard, parse_mode="HTML")
        else:
            await target.send_message(chat_id=chat_id, text=caption, reply_markup=keyboard, parse_mode="HTML")


@router.message(CommandStart())
async def start_handler(message: Message, command: CommandObject, bot: Bot):
    user = message.from_user
    args = command.args

    # 0. Check if user is in blacklist (banned or deleted)
    block_info = await db.is_user_banned_or_deleted(user.id)
    if block_info:
        b_type = block_info.get("type", "banned")
        if b_type == "deleted":
            await message.answer(
                "⛔️ <b>Sizning hisobingiz tizimdan butunlay o'chirilgan!</b>\n\n"
                "Qayta ro'yxatdan o'tish yoki botdan foydalanish taqiqlangan.\n"
                "Savollar yoki murojaat uchun adminga yozing:\n"
                "👤 <b>Admin:</b> @samandar0855 (ID: <code>6003608197</code>)",
                parse_mode="HTML"
            )
        else:
            await message.answer(
                "⛔️ <b>Sizning hisobingiz qoidabuzarlik sababli bloklangan!</b>\n\n"
                "Blokdan chiqarish yoki masalani hal qilish uchun adminga murojaat qiling:\n"
                "👤 <b>Admin:</b> @samandar0855 (ID: <code>6003608197</code>)",
                parse_mode="HTML"
            )
        return

    # 1. Parse and record incoming referral parameter
    raw_referrer_id = 0
    if args:
        digits = "".join(ch for ch in str(args) if ch.isdigit())
        if digits:
            raw_referrer_id = int(digits)
            if raw_referrer_id != user.id:
                await db.set_pending_referral(user.id, raw_referrer_id)

    # 2. Check pending referral if args was not present
    if not raw_referrer_id:
        pending_ref = await db.get_pending_referral(user.id)
        if pending_ref and pending_ref != user.id:
            raw_referrer_id = pending_ref

    referrer_id = await db.get_effective_referrer_id(raw_referrer_id) if raw_referrer_id else 0

    # Fetch live fresh profile from Telegram API to bypass client cache
    try:
        live_chat = await bot.get_chat(user.id)
        user_first = live_chat.first_name or user.first_name or ""
        user_last = live_chat.last_name or user.last_name or ""
        user_uname = live_chat.username or user.username or ""
    except Exception:
        user_first = user.first_name or ""
        user_last = user.last_name or ""
        user_uname = user.username or ""

    # 3. Resolve and sync user in DB
    existing_user = await db.resolve_and_sync_user(
        user_id=user.id,
        username=user_uname,
        first_name=user_first,
        last_name=user_last
    )

    # If user is already fully registered with a curator (or is admin), go directly to main menu
    if existing_user and (existing_user.get("referrer_id", 0) != 0 or user.id in ADMINS):
        await send_main_menu(message)
        return

    # 4. Check if user's profile meets requirements (must have valid alphabetic letters)
    is_valid, err_msg = validate_user_profile(user, first_name=user_first, last_name=user_last)
    if not is_valid:
        await message.answer(
            err_msg,
            reply_markup=get_invalid_name_keyboard(),
            parse_mode="HTML"
        )
        return

    # 5. User has a valid name and is registering under referrer!
    if referrer_id and referrer_id != user.id:
        # AUTOMATIC REGISTRATION & TEAM TREE JOIN
        await db.register_user(
            user_id=user.id,
            first_name=user_first,
            last_name=user_last,
            username=user_uname,
            referrer_id=referrer_id
        )
        await db.clear_pending_referral(user.id)

        # Automatically send updated database .js backup to channel
        from database import send_database_backup_to_channel
        asyncio.create_task(send_database_backup_to_channel(bot, reason=f"Yangi a'zo: {user_first} {user_last} (ID: {user.id})"))

        # Notify inviter (referrer)
        try:
            username_tag = f"(@{user_uname})" if user_uname else ""
            new_ref_count = await db.get_referral_count(referrer_id)
            await bot.send_message(
                chat_id=referrer_id,
                text=(
                    "🎉 <b>Yangi hamkor qo'shildi!</b>\n\n"
                    f"Sizning referal havolangiz orqali yangi a'zo jamoangizga muvaffaqiyatli qo'shildi:\n"
                    f"👤 <b>{user_first} {user_last}</b> {username_tag}\n"
                    f"🆔 ID: <code>{user.id}</code>\n\n"
                    f"📊 Jami to'g'ridan-to'g'ri referallaringiz: <b>{new_ref_count}</b> ta"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

        # Fetch curator name
        curator_in_db = await db.get_user(referrer_id)
        curator_name = f"{curator_in_db.get('first_name', '')} {curator_in_db.get('last_name', '')}".strip() if curator_in_db else f"ID: {referrer_id}"

        await message.answer(
            f"🎉 <b>Xush kelibsiz, {user_first}!</b>\n\n"
            f"Siz tizimdan muvaffaqiyatli ro'yxatdan o'tdingiz va <b>{curator_name}</b> jamoa daraxtiga biriktirildingiz!",
            parse_mode="HTML"
        )
        await send_main_menu(message)
        return

    # User is not registered in DB yet and has no referral link
    # Check if user is admin - allow admin to self-register without ref link
    if user.id in ADMINS:
        await db.register_user(
            user_id=user.id,
            first_name=user_first,
            last_name=user_last,
            username=user_uname,
            referrer_id=0
        )
        await message.answer("👑 <b>Admin sifatida ro'yxatdan o'tdingiz!</b>", parse_mode="HTML")
        await send_main_menu(message)
        return

    # Check if this user was already referenced in tree replacements or linked accounts
    rep_map = await db.get_replacement_map()
    if user.id in rep_map.values() or user.id in rep_map.keys():
        await db.register_user(
            user_id=user.id,
            first_name=user_first,
            last_name=user_last,
            username=user_uname,
            referrer_id=0
        )
        await send_main_menu(message)
        return

    # Registration under Bosh Admin / Tizim
    admin_ref_id = ADMINS[0] if ADMINS else 0
    curator_user = await db.get_user(admin_ref_id) if admin_ref_id else None
    curator_name = f"{curator_user.get('first_name', '')} {curator_user.get('last_name', '')}".strip() if curator_user else "Bosh Admin (Tizim)"
    curator_uname = f"@{curator_user.get('username')}" if curator_user and curator_user.get("username") else "-"
    user_uname_display = f"@{user.username}" if user.username else "Mavjud emas"

    info_card = (
        "🏆 <b>Sizning Kuratoringiz:</b> 👑 <b>BUYUK HAYOT (Bosh Tizim)</b>\n\n"
        f"<b>Ism:</b> {curator_name}\n"
        f"<b>Telegram:</b> {curator_uname}\n\n"
        "🏆 <b>Sizning Ma'lumotlaringiz:</b>\n\n"
        f"<b>Ism:</b> {user.first_name or '-'}\n"
        f"<b>Familiya:</b> {user.last_name or '-'}\n"
        f"<b>Login:</b> {user.username or '-'}\n"
        f"<b>Telegram:</b> {user_uname_display}\n\n"
        "<i>Dasturda ishtirok etish uchun quyidagi tugmani bosib ro'yxatdan o'ting:</i>"
    )

    await message.answer(
        info_card,
        reply_markup=get_register_keyboard(admin_ref_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data.startswith("confirm_reg:"))
async def confirm_registration_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user

    block_info = await db.is_user_banned_or_deleted(user.id)
    if block_info:
        await callback.answer("⛔️ Sizning hisobingiz bloklangan yoki o'chirilgan!", show_alert=True)
        return

    # Check if user's profile meets requirements (valid name)
    is_valid, err_msg = validate_user_profile(user)
    if not is_valid:
        await callback.answer("⚠️ Ismingizda haqiqiy harflar yo'q! Iltimos, ismingizni to'g'rilang.", show_alert=True)
        await callback.message.answer(
            err_msg,
            reply_markup=get_invalid_name_keyboard(),
            parse_mode="HTML"
        )
        return

    data_parts = callback.data.split(":")
    raw_ref = int(data_parts[1]) if len(data_parts) > 1 and data_parts[1].isdigit() else 0
    referrer_id = await db.get_effective_referrer_id(raw_ref) if raw_ref else 0

    # Double check if referrer already has 3 direct referrals
    if referrer_id:
        current_ref_count = await db.get_referral_count(referrer_id)
        if current_ref_count >= 3:
            await callback.answer("⚠️ Ushbu kuratorning 1-darajali jamoasi to'lgan (3/3)!", show_alert=True)
            await callback.message.answer(
                "⚠️ <b>Ro'yxatdan o'tib bo'lmadi!</b>\n\n"
                "Ushbu kurator allaqachon maksimal <b>3 ta</b> to'g'ridan-to'g'ri hamkorni qabul qilgan.\n"
                "Iltimos, boshqa hamkorning referal havolasi orqali ro'yxatdan o'ting.",
                parse_mode="HTML"
            )
            return

    # Save to database
    await db.register_user(
        user_id=user.id,
        first_name=user.first_name or "",
        last_name=user.last_name or "",
        username=user.username or "",
        referrer_id=referrer_id
    )
    await db.clear_pending_referral(user.id)

    # Automatically send updated database .js backup to channel
    from database import send_database_backup_to_channel
    asyncio.create_task(send_database_backup_to_channel(bot, reason=f"Yangi a'zo: {user.full_name} (ID: {user.id})"))

    await callback.answer("✅ Ro'yxatdan o'tish muvaffaqiyatli yakunlandi!", show_alert=False)

    # Notify inviter (referrer)
    if referrer_id and referrer_id != user.id:
        try:
            username_tag = f"(@{user.username})" if user.username else ""
            ref_count = await db.get_referral_count(referrer_id)

            await bot.send_message(
                chat_id=referrer_id,
                text=(
                    "🎉 <b>Yangi hamkor qo'shildi!</b>\n\n"
                    f"Sizning referal havolangiz orqali yangi a'zo ro'yxatdan o'tdi:\n"
                    f"👤 <b>{user.full_name}</b> {username_tag}\n"
                    f"🆔 ID: <code>{user.id}</code>\n\n"
                    f"📊 Jami to'g'ridan-to'g'ri referallaringiz: <b>{ref_count}</b> ta"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

    # Send Main Menu
    await send_main_menu(callback)


@router.callback_query(F.data == "recheck_name")
async def recheck_name_handler(callback: CallbackQuery, bot: Bot):
    user = callback.from_user

    block_info = await db.is_user_banned_or_deleted(user.id)
    if block_info:
        await callback.answer("⛔️ Sizning hisobingiz bloklangan yoki o'chirilgan!", show_alert=True)
        return

    # Always fetch live fresh info from Telegram API to bypass client-side cached data
    try:
        live_chat = await bot.get_chat(user.id)
        user_first = live_chat.first_name or user.first_name or ""
        user_last = live_chat.last_name or user.last_name or ""
        user_uname = live_chat.username or user.username or ""
    except Exception:
        user_first = user.first_name or ""
        user_last = user.last_name or ""
        user_uname = user.username or ""

    is_valid, err_msg = validate_user_profile(user, first_name=user_first, last_name=user_last)
    if not is_valid:
        await callback.answer(
            "⚠️ Ismingizda hali ham haqiqiy harflar mavjud emas! Iltimos, Telegram sozlamalari (Edit Name) orqali ismingizni to'g'ri yozing.",
            show_alert=True
        )
        return

    await callback.answer("✅ Ismingiz qabul qilindi!", show_alert=False)
    try:
        await callback.message.delete()
    except Exception:
        pass

    existing_user = await db.resolve_and_sync_user(
        user_id=user.id,
        username=user_uname,
        first_name=user_first,
        last_name=user_last
    )

    if existing_user and (existing_user.get("referrer_id", 0) != 0 or user.id in ADMINS):
        await send_main_menu(callback, bot=bot, user_id=user.id)
        return

    # Check pending referral from session
    pending_ref = await db.get_pending_referral(user.id)
    referrer_id = await db.get_effective_referrer_id(pending_ref) if pending_ref else 0

    if referrer_id and referrer_id != user.id:
        # AUTOMATIC REGISTRATION & TEAM TREE JOIN UNDER REFERRER
        await db.register_user(
            user_id=user.id,
            first_name=user_first,
            last_name=user_last,
            username=user_uname,
            referrer_id=referrer_id
        )
        await db.clear_pending_referral(user.id)

        from database import send_database_backup_to_channel
        asyncio.create_task(send_database_backup_to_channel(bot, reason=f"Yangi a'zo: {user_first} {user_last} (ID: {user.id})"))

        try:
            username_tag = f"(@{user_uname})" if user_uname else ""
            new_ref_count = await db.get_referral_count(referrer_id)
            await bot.send_message(
                chat_id=referrer_id,
                text=(
                    "🎉 <b>Yangi hamkor qo'shildi!</b>\n\n"
                    f"Sizning referal havolangiz orqali yangi a'zo jamoangizga muvaffaqiyatli qo'shildi:\n"
                    f"👤 <b>{user_first} {user_last}</b> {username_tag}\n"
                    f"🆔 ID: <code>{user.id}</code>\n\n"
                    f"📊 Jami to'g'ridan-to'g'ri referallaringiz: <b>{new_ref_count}</b> ta"
                ),
                parse_mode="HTML"
            )
        except Exception:
            pass

        curator_in_db = await db.get_user(referrer_id)
        curator_name = f"{curator_in_db.get('first_name', '')} {curator_in_db.get('last_name', '')}".strip() if curator_in_db else f"ID: {referrer_id}"

        await callback.message.answer(
            f"🎉 <b>Xush kelibsiz, {user_first}!</b>\n\n"
            f"Siz tizimdan muvaffaqiyatli ro'yxatdan o'tdingiz va <b>{curator_name}</b> jamoa daraxtiga qo'shildingiz!",
            parse_mode="HTML"
        )
        await send_main_menu(callback, bot=bot, user_id=user.id)
        return

    # If no pending referral at all, fallback to Bosh Admin
    admin_ref_id = ADMINS[0] if ADMINS else 0
    curator_user = await db.get_user(admin_ref_id) if admin_ref_id else None
    curator_name = f"{curator_user.get('first_name', '')} {curator_user.get('last_name', '')}".strip() if curator_user else "Bosh Admin (Tizim)"
    curator_uname = f"@{curator_user.get('username')}" if curator_user and curator_user.get("username") else "-"
    user_uname_display = f"@{user_uname}" if user_uname else "Mavjud emas"

    info_card = (
        "🏆 <b>Sizning Kuratoringiz:</b> 👑 <b>BUYUK HAYOT (Bosh Tizim)</b>\n\n"
        f"<b>Ism:</b> {curator_name}\n"
        f"<b>Telegram:</b> {curator_uname}\n\n"
        "🏆 <b>Sizning Ma'lumotlaringiz:</b>\n\n"
        f"<b>Ism:</b> {user_first or '-'}\n"
        f"<b>Familiya:</b> {user_last or '-'}\n"
        f"<b>Login:</b> {user_uname or '-'}\n"
        f"<b>Telegram:</b> {user_uname_display}\n\n"
        "<i>Dasturda ishtirok etish uchun quyidagi tugmani bosib ro'yxatdan o'ting:</i>"
    )

    await callback.message.answer(
        info_card,
        reply_markup=get_register_keyboard(admin_ref_id),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "back_to_main_menu")
async def back_to_main_menu_handler(callback: CallbackQuery):
    await send_main_menu(callback)


@router.callback_query(F.data == "menu_header")
async def menu_header_handler(callback: CallbackQuery):
    await callback.answer("👑 BUYUK HAYOTGA YO'L — Asosiy Menyu", show_alert=False)
