import io
import math
import os
import qrcode
from aiogram import Router, F, Bot
from aiogram.types import CallbackQuery, Message, BufferedInputFile, FSInputFile
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from database import db
from config import ADMINS
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
    get_back_to_menu_keyboard,
    get_payment_request_keyboard,
    get_payment_sent_keyboard,
    get_curator_approval_keyboard
)

router = Router()

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
BANNER_MAIN = os.path.join(BASE_DIR, "assets", "main_banner.png")
BANNER_CABINET = os.path.join(BASE_DIR, "assets", "cabinet_banner.png")
BANNER_BALANCE = os.path.join(BASE_DIR, "assets", "balance_banner.png")
BANNER_MARKETING = os.path.join(BASE_DIR, "assets", "marketing_banner.png")
BANNER_ALL_LEVELS = os.path.join(BASE_DIR, "assets", "all_levels_banner.png")

LEVEL_PRICES = {
    1: 200000,
    2: 2700000,
    3: 35000000,
    4: 1377000000,
    5: 17100000000
}

LEVEL_LABELS = {
    1: "200 000 so'm (200 ming so'm)",
    2: "2 700 000 so'm (2 mln 700 ming so'm)",
    3: "35 000 000 so'm (35 mln so'm)",
    4: "1 377 000 000 so'm (1 mlrd 377 mln so'm)",
    5: "17 100 000 000 so'm (17 mlrd 100 mln so'm)"
}

LEVEL_REQUIRED_REFS = {
    1: 3,
    2: 9,
    3: 27,
    4: 81,
    5: 243
}

class WalletStates(StatesGroup):
    waiting_for_wallet_value = State()


# ==================== MARKETING SECTION (PAYMENT TO CURATOR) ====================

MARKETING_CAPTION = (
    "👑 <b>«BUYUK HAYOTGA INTIILISH» — MARKETING</b>\n\n"
    "⚪️ Dasturga kirish <b>200 000 so'm</b> turadi — bu 1-daraja uchun to'lov.\n"
    "⚪️ Siz ketma-ket 5 tagacha darajalarni faollashtirishingiz mumkin.\n"
    "⚪️ 100% shaffof va to'g'ridan-to'g'ri insondan-insonga daromad modeli!\n\n"
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
            reply_markup=keyboard,
            parse_mode="HTML"
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
    caption = "👑 <b>Barcha darajalar (1 - 5 Bosqichlar)</b>\nFaollashtirmoqchi bo'lgan darajangizni tanlang:"
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
            reply_markup=keyboard,
            parse_mode="HTML"
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
    cur_lvl = user_data.get("current_level", 0) if user_data else 0

    # Case 1: Already activated
    if level <= cur_lvl:
        caption = "✅ <b>Siz bu darajani allaqachon faollashtirgansiz</b>"
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
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            try:
                await callback.message.edit_caption(caption=caption, reply_markup=keyboard, parse_mode="HTML")
            except Exception:
                await callback.message.edit_text(text=caption, reply_markup=keyboard, parse_mode="HTML")
        return

    # Case 2: Skipped previous level
    if level > cur_lvl + 1:
        caption = f"🔒 <b>Avval oldingi {cur_lvl + 1}-darajani to'lang</b>"
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
                reply_markup=keyboard,
                parse_mode="HTML"
            )
        else:
            try:
                await callback.message.edit_caption(caption=caption, reply_markup=keyboard, parse_mode="HTML")
            except Exception:
                await callback.message.edit_text(text=caption, reply_markup=keyboard, parse_mode="HTML")
        return

    # Case 3: Payment details formatted exactly like screenshot
    curator_id = user_data.get("referrer_id", 0) if user_data else 0
    if not curator_id or curator_id == 0:
        curator_id = ADMINS[0] if ADMINS else user.id

    curator_data = await db.get_user(curator_id)

    # Always try Telegram API for fresh real info
    try:
        chat_obj = await bot.get_chat(curator_id)
        tg_info = {
            "first_name": chat_obj.first_name or "",
            "last_name": chat_obj.last_name or "",
            "username": chat_obj.username or ""
        }
        # Merge: use API for name/username, keep DB wallet fields
        merged = dict(curator_data) if curator_data else {}
        merged.update({k: v for k, v in tg_info.items() if v})
        curator_data = merged
    except Exception:
        if not curator_data:
            curator_data = {"first_name": f"ID: {curator_id}", "last_name": "", "username": ""}

    karta = curator_data.get("wallet_card") or "8600 **** **** **** (UzCard / Humo)"
    bep20 = curator_data.get("wallet_bep20") or "0x... (USDT BEP20)"
    trc20 = curator_data.get("wallet_trc20") or "T... (USDT TRC20)"
    payeer = curator_data.get("wallet_payeer") or "P... (PAYEER)"

    curator_username = curator_data.get("username", "")
    curator_tag = f"@{curator_username}" if curator_username else f"ID: {curator_id}"
    price_label = LEVEL_LABELS.get(level, f"{LEVEL_PRICES.get(level, 200000):,} so'm")

    caption = (
        f"Вам необходимо оплатить <b>{price_label}</b> на один из указаных кошельков:\n\n"
        f"💳 <b>KARTA BANKA (UzCard / Humo):</b>\n<code>{karta}</code>\n\n"
        f"💎 <b>USDT BEP20:</b>\n<code>{bep20}</code>\n\n"
        f"💎 <b>USDT TRC20:</b>\n<code>{trc20}</code>\n\n"
        f"🅿️ <b>PAYEER:</b>\n<code>{payeer}</code>\n\n"
        f"пользователю <b>{curator_tag}</b>\n"
        "После перевода нажмите кнопку <b>'я оплатил'</b> и свяжитесь с пользователем по кнопке <b>'Написать'</b>\n\n"
        "────────────────────\n"
        f"<i>(Siz ko'rsatilgan hamyonlardan biriga <b>{price_label}</b> to'lov qilishingiz kerak. "
        "O'tkazmani amalga oshirgandan so'ng 'Я оплатил' tugmasini bosing va 'Написать' tugmasi orqali foydalanuvchining lichkasiga yozing.)</i>"
    )

    keyboard = get_payment_request_keyboard(level, curator_id, curator_username, from_all=from_all)

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


@router.callback_query(F.data.startswith("mkt_paid:"))
async def marketing_paid_click_handler(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    level = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 1
    curator_id = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 0

    user = callback.from_user
    user_uname = f"@{user.username}" if user.username else f"ID: {user.id}"
    price_label = LEVEL_LABELS.get(level, f"{LEVEL_PRICES.get(level, 200000):,} so'm")

    # Fetch curator info for button
    curator_data = await db.get_user(curator_id)
    curator_username = curator_data.get("username", "") if curator_data else ""

    await callback.answer("✅ Запрос отправлен!", show_alert=False)

    caption = (
        "Запрос отправлен, при необходимости свяжитесь с пользователем в том же разделе\n\n"
        "<i>(So'rov yuborildi, zarurat bo'lsa 'Написать' tugmasi orqali kuratoringiz bilan bog'laning)</i>"
    )
    keyboard = get_payment_sent_keyboard(curator_id, curator_username)

    try:
        await callback.message.edit_caption(caption=caption, reply_markup=keyboard, parse_mode="HTML")
    except Exception:
        await callback.message.edit_text(text=caption, reply_markup=keyboard, parse_mode="HTML")

    # Notify curator
    if curator_id and curator_id != user.id:
        try:
            curator_notify_text = (
                "🔔 <b>YANGI TO'LOV BILDIRISHNOMASI!</b>\n\n"
                f"👤 <b>Foydalanuvchi:</b> {user.full_name} ({user_uname})\n"
                f"🆔 <b>ID:</b> <code>{user.id}</code>\n"
                f"⚡️ <b>Daraja:</b> {level}-Bosqich\n"
                f"💰 <b>Summa:</b> {price_label}\n\n"
                "Foydalanuvchi sizning hamyoningizga to'lov o'tkazganini bildirdi. "
                "Hamyoningizga pul tushganini tekshirib, darajani tasdiqlang 👇"
            )
            approval_keyboard = get_curator_approval_keyboard(user.id, level)
            await bot.send_message(
                chat_id=curator_id,
                text=curator_notify_text,
                reply_markup=approval_keyboard,
                parse_mode="HTML"
            )
        except Exception:
            pass


@router.callback_query(F.data.startswith("approve_lvl:"))
async def approve_level_handler(callback: CallbackQuery, bot: Bot):
    parts = callback.data.split(":")
    buyer_id = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else 0
    level = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1

    await db.set_user_level(buyer_id, level)
    
    price_val = LEVEL_PRICES.get(level, 200000)
    await db.add_user_earnings(callback.from_user.id, price_val)

    await callback.answer(f"✅ {level}-Daraja muvaffaqiyatli tasdiqlandi!", show_alert=True)
    try:
        await callback.message.edit_text(
            f"✅ <b>To'lov tasdiqlandi!</b>\nFoydalanuvchiga (ID: <code>{buyer_id}</code>) <b>{level}-Bosqich</b> berildi.",
            parse_mode="HTML"
        )
    except Exception:
        pass

    # Notify buyer
    try:
        await bot.send_message(
            chat_id=buyer_id,
            text=(
                f"🎉 <b>TABRIKLAYMIZ!</b>\n\n"
                f"Sizning <b>{level}-Bosqich</b> uchun to'lovingiz kuratoringiz tomonidan tasdiqlandi!\n"
                f"Yangi darajangiz: <b>{level}-Daraja</b> ✅"
            ),
            parse_mode="HTML"
        )
    except Exception:
        pass


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
        "Rasmiy bot: @Buyukhayot_bot\n"
        "Loyiha chati: @Buyukhayot_bot\n"
        "Qo'llab-quvvatlash: @Buyukhayot_bot\n\n"
        "<b>Telegram</b>\n"
        "<b>Asosiy guruh</b>\n"
        "<b>👑 BUYUK HAYOTGA YO'L</b>\n"
        "BUYUK HAYOTGA YO'L — yuqori daromad reytingiga ega dastur! 100% insondan insonga! Har qanday valyuta, turli xil hamyonlar!"
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
    caption = "👑 Jamoa chati va rasmiy bot:\n@Buyukhayot_bot"
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
    total_earned = user_data.get("total_earned", 0.0) if user_data else 0.0

    caption = (
        f"Dasturdagi umumiy daromad: {int(total_earned):,} so'm\n\n"
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
        "1. 📥 Dastlabki hisob: <b>0 so'm</b>\n"
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
    ref_link = f"https://t.me/{bot_me.username}?start=ref_{user.id}"

    text = (
        "👥 <b>HAMKORLAR VA REFERAL TIZIMI</b>\n\n"
        f"👤 <b>Sizning hamkorlaringiz:</b> <b>{ref_count}</b> ta\n\n"
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

    photo_file = BufferedInputFile(img_bytes, filename=f"buyukhayot_qr_{user.id}.png")
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
