import io
import math
import os
import qrcode
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from keyboards.inline import (
    get_main_menu_keyboard,
    get_marketing_menu_keyboard,
    get_all_levels_keyboard,
    get_level_back_keyboard,
    get_level_activate_keyboard,
    get_cabinet_menu_keyboard,
    get_account_keyboard,
    get_team_chat_keyboard,
    get_balance_keyboard,
    get_partners_keyboard,
    get_wallet_edit_keyboard,
    get_referrals_pagination_keyboard,
    get_back_to_menu_keyboard
)

router = Router()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BANNER_MAIN = os.path.join(BASE_DIR, "assets", "concord_banner.png")
BANNER_CABINET = os.path.join(BASE_DIR, "assets", "cabinet_banner.png")
BANNER_BALANCE = os.path.join(BASE_DIR, "assets", "balance_banner.png")
BANNER_MARKETING = os.path.join(BASE_DIR, "assets", "marketing_banner.png")
BANNER_ALL_LEVELS = os.path.join(BASE_DIR, "assets", "all_levels_banner.png")

LEVEL_PRICES = {
    1: 10,
    2: 20,
    3: 50,
    4: 100,
    5: 200,
    6: 500
}

class WalletStates(StatesGroup):
    waiting_for_wallet_value = State()


# ==================== MARKETING SECTION (4 SCREENSHOTS) ====================

MARKETING_CAPTION = (
    "MARKETING\n\n"
    "⚪️ Dasturga kirish atigi 10$ turadi — bu birinchi daraja uchun to'lov.\n"
    "⚪️ Siz birdaniga ketma-ket bir nechta darajalarni to'lashingiz mumkin.\n"
    "⚪️ Barcha narx tafsilotlari va model marketingda batafsil bayon etilgan.\n\n"
    "1-Darajani to'lash uchun pastdagi tugmani bosing 👇."
)

@router.callback_query(F.data == "menu_marketing")
async def marketing_main_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    keyboard = get_marketing_menu_keyboard()

    if os.path.exists(BANNER_MARKETING):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(BANNER_MARKETING),
            caption=MARKETING_CAPTION,
            reply_markup=keyboard
        )
    else:
        try:
            await callback.message.edit_caption(
                caption=MARKETING_CAPTION,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.edit_text(
                text=MARKETING_CAPTION,
                reply_markup=keyboard,
                parse_mode="HTML"
            )


@router.callback_query(F.data == "mkt_all_levels")
async def marketing_all_levels_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    caption = "Barcha darajalar"
    keyboard = get_all_levels_keyboard()

    if os.path.exists(BANNER_ALL_LEVELS):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(BANNER_ALL_LEVELS),
            caption=caption,
            reply_markup=keyboard
        )
    else:
        try:
            await callback.message.edit_caption(
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.edit_text(
                text=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )


@router.callback_query(F.data.startswith("mkt_lvl:"))
async def marketing_level_click_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    parts = callback.data.split(":")
    level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    from_all = (len(parts) > 2 and parts[2] == "all")

    user = callback.from_user
    user_data = await db.get_user(user.id)
    cur_lvl = user_data.get("current_level", 1) if user_data else 1

    # Case 1: Already activated (Screenshot 2)
    if level <= cur_lvl:
        caption = "Siz bu darajani allaqachon faollashtirgansiz"
        keyboard = get_level_back_keyboard(from_all=from_all)
        if os.path.exists(BANNER_MARKETING):
            try:
                await callback.message.delete()
            except Exception:
                pass
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=FSInputFile(BANNER_MARKETING),
                caption=caption,
                reply_markup=keyboard
            )
        else:
            try:
                await callback.message.edit_caption(caption=caption, reply_markup=keyboard)
            except Exception:
                await callback.message.edit_text(text=caption, reply_markup=keyboard)
        return

    # Case 2: Skipped previous level (Screenshot 4)
    if level > cur_lvl + 1:
        caption = "Avval oldingi darajani to'lang"
        keyboard = get_level_back_keyboard(from_all=from_all)
        if os.path.exists(BANNER_MARKETING):
            try:
                await callback.message.delete()
            except Exception:
                pass
            await bot.send_photo(
                chat_id=callback.message.chat.id,
                photo=FSInputFile(BANNER_MARKETING),
                caption=caption,
                reply_markup=keyboard
            )
        else:
            try:
                await callback.message.edit_caption(caption=caption, reply_markup=keyboard)
            except Exception:
                await callback.message.edit_text(text=caption, reply_markup=keyboard)
        return

    # Case 3: Ready to activate next level
    price = LEVEL_PRICES.get(level, 10)
    caption = (
        f"💳 <b>{level}-Darajani faollashtirish</b>\n\n"
        f"💰 <b>Narxi:</b> {price}$\n\n"
        "To'lovni amalga oshirish va darajani ochish uchun quyidagi tugmani bosing:"
    )
    keyboard = get_level_activate_keyboard(level, price, from_all=from_all)
    if os.path.exists(BANNER_MARKETING):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(BANNER_MARKETING),
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        try:
            await callback.message.edit_caption(caption=caption, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            await callback.message.edit_text(text=caption, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("mkt_pay_level:"))
async def marketing_pay_level_handler(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

    await db.set_user_level(callback.from_user.id, level)
    await callback.answer(f"🎉 {level}-Daraja muvaffaqiyatli faollashtirildi!", show_alert=True)

    caption = f"✅ <b>{level}-Daraja muvaffaqiyatli faollashtirildi!</b>"
    keyboard = get_level_back_keyboard(from_all=True)

    if os.path.exists(BANNER_MARKETING):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(BANNER_MARKETING),
            caption=caption,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    else:
        try:
            await callback.message.edit_caption(caption=caption, reply_markup=keyboard, parse_mode="HTML")
        except Exception:
            await callback.message.edit_text(text=caption, reply_markup=keyboard, parse_mode="HTML")


# ==================== KABINET SECTION (4 SCREENSHOTS) ====================

@router.callback_query(F.data == "menu_cabinet")
async def cabinet_main_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    caption = "Mening kabinetim"
    keyboard = get_cabinet_menu_keyboard()

    if os.path.exists(BANNER_CABINET):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(BANNER_CABINET),
            caption=caption,
            reply_markup=keyboard
        )
    else:
        await callback.message.edit_text(
            text=f"🌌 <b>{caption}</b>",
            reply_markup=keyboard,
            parse_mode="HTML"
        )


@router.callback_query(F.data == "cabinet_header")
async def cabinet_header_handler(callback: CallbackQuery):
    await callback.answer("♦️ Shaxsiy Kabinet ♦️", show_alert=False)


# ==================== MENING HISOBIM ====================

@router.callback_query(F.data == "cab_account")
async def cab_account_handler(callback: CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id

    text = (
        f"⚪️ <b>Sizning ID:</b> {user_id};\n"
        "⚪️ <b>Biz bilan bog'lanish:</b>\n"
        "Qo'llab-quvvatlash: @ConcordSupport\n"
        "Loyiha chati: @concord_komanda\n"
        "Kelishuv: https://concord.link/agreement\n"
        "Etika va qoidalar: https://concord.link/rules\n"
        "Promomateriallar: https://concord.link/promo\n"
        "Bizning darajalar: https://concord.link/levels\n\n"
        "<b>Telegram</b>\n"
        "<b>Asosiy guruh</b>\n"
        "<b>CONCORD 🚀</b>\n"
        "CONCORD - yuqori daromad reytingiga ega dastur! 100% insondan insonga! Har qanday valyuta, turli xil hamyonlar!"
    )
    keyboard = get_account_keyboard()
    try:
        await callback.message.edit_caption(
            caption=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )
    except Exception:
        await callback.message.edit_text(
            text=text,
            reply_markup=keyboard,
            parse_mode="HTML"
        )


# ==================== JAMOA CHATI ====================

@router.callback_query(F.data == "cab_team_chat")
async def cab_team_chat_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    caption = "Jamoa chatiga havola\n@concord_komanda"
    keyboard = get_team_chat_keyboard()

    if os.path.exists(BANNER_CABINET):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(BANNER_CABINET),
            caption=caption,
            reply_markup=keyboard
        )
    else:
        try:
            await callback.message.edit_caption(
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.edit_text(
                text=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )


# ==================== MENING BALANSIM ====================

@router.callback_query(F.data == "cab_balance")
async def cab_balance_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    user = callback.from_user
    user_data = await db.get_user(user.id)
    total_earned = user_data.get("total_earned", 30.0) if user_data else 30.0

    caption = (
        f"Dasturdagi umumiy daromad: {int(total_earned) if total_earned == int(total_earned) else total_earned}$\n\n"
        "Hamyonni o'rnatish yoki tahrirlash uchun - tegishli tugmani bosing"
    )
    keyboard = get_balance_keyboard()

    if os.path.exists(BANNER_BALANCE):
        try:
            await callback.message.delete()
        except Exception:
            pass
        await bot.send_photo(
            chat_id=callback.message.chat.id,
            photo=FSInputFile(BANNER_BALANCE),
            caption=caption,
            reply_markup=keyboard
        )
    else:
        try:
            await callback.message.edit_caption(
                caption=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        except Exception:
            await callback.message.edit_text(
                text=caption,
                reply_markup=keyboard,
                parse_mode="HTML"
            )


@router.callback_query(F.data == "balance_header")
async def balance_header_handler(callback: CallbackQuery):
    await callback.answer("Mening balansim", show_alert=False)


# ==================== WALLET SELECTION & EDITING ====================

WALLET_NAMES = {
    "wallet_bep20": "USDT BEP20",
    "wallet_card": "KARTA BANKA (UzCard / Humo / Visa)",
    "wallet_trc20": "USDT TRC20",
    "wallet_payeer": "PAYEER"
}

@router.callback_query(F.data.startswith("wallet:"))
async def view_wallet_handler(callback: CallbackQuery):
    await callback.answer()
    wallet_key = callback.data.split(":")[1]
    wallet_name = WALLET_NAMES.get(wallet_key, wallet_key)

    user_data = await db.get_user(callback.from_user.id)
    current_val = user_data.get(wallet_key, "") if user_data else ""
    val_display = f"<code>{current_val}</code>" if current_val else "<i>Hali kiritilmagan</i>"

    text = (
        f"💳 <b>{wallet_name}</b>\n\n"
        f"📌 <b>Joriy hamyon:</b> {val_display}\n\n"
        "Hamyon raqamini o'zgartirish yoki yangi kiritish uchun pastdagi tugmani bosing:"
    )
    keyboard = get_wallet_edit_keyboard(wallet_key)
    try:
        await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data.startswith("setwallet:"))
async def set_wallet_prompt_handler(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    wallet_key = callback.data.split(":")[1]
    wallet_name = WALLET_NAMES.get(wallet_key, wallet_key)

    await state.update_data(editing_wallet_key=wallet_key)
    await state.set_state(WalletStates.waiting_for_wallet_value)

    await callback.message.answer(
        f"✍️ Iltimos, <b>{wallet_name}</b> hamyon manzilingiz yoki karta raqamingizni yuboring:\n\n"
        "<i>(Bekor qilish uchun /cancel deb yozing)</i>",
        parse_mode="HTML"
    )


@router.message(WalletStates.waiting_for_wallet_value)
async def save_wallet_value_handler(message: Message, state: FSMContext):
    if message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Hamyonni tahrirlash bekor qilindi.")
        return

    data = await state.get_data()
    wallet_key = data.get("editing_wallet_key")
    wallet_value = message.text.strip()

    if wallet_key:
        await db.update_wallet(message.from_user.id, wallet_key, wallet_value)
        wallet_name = WALLET_NAMES.get(wallet_key, wallet_key)
        await message.answer(
            f"✅ <b>{wallet_name}</b> muvaffaqiyatli saqlandi:\n<code>{wallet_value}</code>",
            parse_mode="HTML"
        )
    await state.clear()


@router.callback_query(F.data == "bal_history")
async def balance_history_handler(callback: CallbackQuery):
    await callback.answer()
    text = (
        "📜 <b>OPERATSIYALAR TARIXI</b>\n\n"
        "1. 📥 Dastlabki ro'yxatdan o'tish bonusi: <b>+30.00$</b>\n"
        "2. 🔄 Balans holati: <b>Faol</b>\n\n"
        "<i>Barcha yangi tushumlar va to'lovlar shu yerda aks etadi.</i>"
    )
    keyboard = get_balance_keyboard()
    try:
        await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "bal_archive")
async def balance_archive_handler(callback: CallbackQuery):
    await callback.answer()
    text = (
        "🗂 <b>DARAJALAR ARXIVI</b>\n\n"
        "🎯 <b>Joriy ochiq darajalar:</b> 1-bosqich (Asosiy)\n"
        "📊 <b>Yopilgan sikllar:</b> 0 ta\n"
        "💡 <i>Yangi darajalar yopilganda natijalar ushbu arxivda saqlanadi.</i>"
    )
    keyboard = get_balance_keyboard()
    try:
        await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")


# ==================== HAMKORLAR (PARTNERS) ====================

@router.callback_query(F.data == "cab_partners")
async def partners_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    user = callback.from_user
    bot_me = await bot.get_me()
    ref_count = await db.get_referral_count(user.id)
    multi_tier = await db.get_multi_tier_stats(user.id)
    ref_link = f"https://t.me/{bot_me.username}?start=ref_{user.id}"

    text = (
        "👥 <b>HAMKORLAR VA REFERAL TIZIMI</b>\n\n"
        f"🥇 <b>1-Daraja (To'g'ridan-to'g'ri):</b> <b>{ref_count}</b> ta hamkor\n"
        f"🥈 <b>2-Daraja (Bilvosita):</b> <b>{multi_tier['level_2']}</b> ta hamkor\n"
        f"🥉 <b>3-Daraja (Chuqur jamoa):</b> <b>{multi_tier['level_3']}</b> ta hamkor\n"
        "────────────────────\n"
        f"🌐 <b>JAMI JAMOA:</b> <b>{multi_tier['total_team']}</b> ta hamkor\n\n"
        f"🔗 <b>Sizning taklif havolangiz:</b>\n<code>{ref_link}</code>"
    )
    keyboard = get_partners_keyboard(bot_me.username, user.id)
    try:
        await callback.message.edit_caption(caption=text, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.edit_text(text=text, reply_markup=keyboard, parse_mode="HTML")


@router.callback_query(F.data == "cab_ref_link")
async def cab_ref_link_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer()
    user = callback.from_user
    bot_me = await bot.get_me()
    ref_link = f"https://t.me/{bot_me.username}?start=ref_{user.id}"

    text = (
        "🔗 <b>SIZNING SHAXSIY REFERAL HAVOLANGIZ:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        "📌 <i>Ushbu havolani nusxalab do'stlaringizga yuboring. Ular faqat sizning havolangiz orqali ro'yxatdan o'ta oladilar!</i>"
    )
    await callback.message.answer(text=text, parse_mode="HTML")


@router.callback_query(F.data == "cab_qr_code")
async def cab_qr_code_handler(callback: CallbackQuery, bot: Bot):
    await callback.answer("QR kod yaratilmoqda...", show_alert=False)
    user = callback.from_user
    bot_me = await bot.get_me()
    ref_link = f"https://t.me/{bot_me.username}?start=ref_{user.id}"

    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=10,
        border=3,
    )
    qr.add_data(ref_link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="#0b1b3d", back_color="white")

    img_byte_arr = io.BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()

    photo_file = BufferedInputFile(img_bytes, filename=f"concord_qr_{user.id}.png")
    caption = (
        "📲 <b>SIZNING SHAXSIY QR KODINGIZ</b>\n\n"
        f"👤 <b>Egasi:</b> {user.full_name}\n"
        f"🔗 <b>Havola:</b> <code>{ref_link}</code>\n\n"
        "💡 <i>Ushbu QR kodni skanerlash orqali hamkorlar to'g'ridan-to'g'ri sizning jamoangizga qo'shiladi.</i>"
    )
    await callback.message.answer_photo(photo=photo_file, caption=caption, parse_mode="HTML")


@router.callback_query(F.data == "cab_multi_tier")
async def cab_multi_tier_handler(callback: CallbackQuery):
    await callback.answer()
    user = callback.from_user
    stats = await db.get_multi_tier_stats(user.id)

    text = (
        "🌳 <b>3-DARAJALI JAMOA STRUKTURASI</b>\n\n"
        f"🥇 <b>1-Daraja (To'g'ridan-to'g'ri takliflar):</b> <b>{stats['level_1']}</b> ta hamkor\n"
        f"🥈 <b>2-Daraja (Bilvosita takliflar):</b> <b>{stats['level_2']}</b> ta hamkor\n"
        f"🥉 <b>3-Daraja (Chuqur jamoa):</b> <b>{stats['level_3']}</b> ta hamkor\n"
        "────────────────────\n"
        f"🌐 <b>JAMI JAMOA:</b> <b>{stats['total_team']}</b> ta hamkor"
    )
    await callback.message.answer(text=text, parse_mode="HTML")


@router.callback_query(F.data.startswith("cab_team_page:"))
async def cab_team_page_handler(callback: CallbackQuery):
    await callback.answer()
    user = callback.from_user
    parts = callback.data.split(":")
    page = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1

    per_page = 6
    total_refs = await db.get_referral_count(user.id)
    total_pages = max(1, math.ceil(total_refs / per_page))

    if page > total_pages:
        page = total_pages
    if page < 1:
        page = 1

    offset = (page - 1) * per_page
    referrals = await db.get_referrals(user.id, offset=offset, limit=per_page)

    if not referrals:
        await callback.message.answer(
            "👥 <b>Sizda hali to'g'ridan-to'g'ri taklif qilingan hamkorlar yo'q.</b>\n\n"
            "Referal havolangizni ulashing va jamoa shakllantiring!",
            parse_mode="HTML"
        )
        return

    text_lines = [
        f"👥 <b>SIZNING HAMKORLARINGIZ (Jami {total_refs} ta)</b>\n"
        f"<i>Sahifa {page}/{total_pages}:</i>\n"
    ]

    for idx, ref in enumerate(referrals, 1 + offset):
        name = f"{ref.get('first_name', '')} {ref.get('last_name', '')}".strip() or "Foydalanuvchi"
        uname = f"@{ref.get('username')}" if ref.get('username') else f"ID: {ref['user_id']}"
        status = ref.get("status", "🌱 Boshlang'ich")
        date = ref.get("registered_at", "")[:10]
        text_lines.append(f"{idx}. <b>{name}</b> ({uname})\n   └ Maqom: <i>{status}</i> | Sana: <i>{date}</i>")

    keyboard = get_referrals_pagination_keyboard(page, total_pages)
    await callback.message.answer(
        text="\n".join(text_lines),
        reply_markup=keyboard,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "noop")
async def noop_handler(callback: CallbackQuery):
    await callback.answer()
