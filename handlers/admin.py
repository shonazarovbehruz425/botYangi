import asyncio
from aiogram import Router, F, Bot
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from config import ADMINS, BACKUP_CHANNEL_ID
from database import db
from keyboards import get_admin_keyboard, get_back_to_menu_keyboard

router = Router()

class AdminStates(StatesGroup):
    waiting_for_broadcast_message = State()


@router.message(Command("backup"))
async def admin_manual_backup(message: Message, bot: Bot):
    if message.from_user.id not in ADMINS:
        return
    status_msg = await message.answer("⏳ Ma'lumotlar bazasi zaxira nusxasi tayyorlanmoqda va kanalga yuborilmoqda...")
    from database import send_database_backup_to_channel
    success = await send_database_backup_to_channel(bot, reason="Admin tomonidan qo'lda chaqirildi (/backup)")
    if success:
        await status_msg.edit_text("✅ <b>Database .js fayli kanalga muvaffaqiyatli yuborildi va qadaldi!</b>", parse_mode="HTML")
    else:
        await status_msg.edit_text("❌ <b>Xatolik yuz berdi.</b> Bot kanalga admin ekanligini tekshiring.")


@router.message(Command("restore"))
async def admin_manual_restore(message: Message, bot: Bot):
    if message.from_user.id not in ADMINS:
        return
    status_msg = await message.answer("⏳ Kanaldan oxirgi zaxira nusxasi yuklanmoqda va bazaga tiklanmoqda...")
    from database.backup import restore_database_from_channel
    count = await restore_database_from_channel(bot)
    if count > 0:
        await status_msg.edit_text(f"✅ <b>Baza muvaffaqiyatli tiklandi!</b>\n👥 Jami tiklangan a'zolar: <b>{count}</b> ta", parse_mode="HTML")
    else:
        await status_msg.edit_text("⚠️ <b>Tiklash amalga oshmadi.</b> Kanaldagi oxirgi qadalgan .js zaxira faylini tekshiring.")


@router.message(Command("admin"))
async def admin_panel_handler(message: Message):
    if message.from_user.id not in ADMINS:
        await message.answer("⛔️ Sizda admin huquqlari mavjud emas.")
        return

    total_users = await db.get_total_users_count()
    text = (
        "👑 <b>ADMIN BOSHQARUV PANELI</b>\n\n"
        f"👥 <b>Jami foydalanuvchilar:</b> {total_users} ta\n"
        f"📢 <b>Backup kanali:</b> <code>{BACKUP_CHANNEL_ID}</code>\n\n"
        "Quyidagi bo'limlardan birini tanlang:"
    )
    await message.answer(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_stats")
async def admin_stats_handler(callback: CallbackQuery):
    if callback.from_user.id not in ADMINS:
        await callback.answer("⛔️ Ruxsat berilmagan", show_alert=True)
        return

    total = await db.get_total_users_count()
    all_users = await db.get_all_users()

    # Find top referrers
    ref_counts = {}
    for u in all_users:
        ref_id = u.get("referrer_id")
        if ref_id and ref_id != 0:
            ref_counts[ref_id] = ref_counts.get(ref_id, 0) + 1

    sorted_refs = sorted(ref_counts.items(), key=lambda x: x[1], reverse=True)[:5]
    top_text = ""
    for idx, (uid, count) in enumerate(sorted_refs, 1):
        top_text += f"{idx}. ID: <code>{uid}</code> — <b>{count}</b> ta taklif\n"

    if not top_text:
        top_text = "Hozircha ma'lumot yo'q\n"

    text = (
        "📊 <b>BOT STATISTIKASI</b>\n\n"
        f"👥 Jami ro'yxatdan o'tganlar: <b>{total}</b> ta\n\n"
        f"🏆 <b>Top taklif qiluvchilar:</b>\n{top_text}"
    )
    await callback.message.edit_text(
        text=text,
        reply_markup=get_admin_keyboard(),
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_ref")
async def admin_ref_handler(callback: CallbackQuery, bot: Bot):
    if callback.from_user.id not in ADMINS:
        await callback.answer("⛔️ Ruxsat berilmagan", show_alert=True)
        return

    bot_me = await bot.get_me()
    admin_id = callback.from_user.id
    ref_link = f"https://t.me/{bot_me.username}?start=ref_{admin_id}"

    text = (
        "🔗 <b>ADMINNING BOSHLANG'ICH (ROOT) REFERAL HAVOLASI:</b>\n\n"
        f"<code>{ref_link}</code>\n\n"
        "💡 <i>Ushbu havolani dastlabki asosiy yetakchilarga yuborishingiz mumkin.</i>"
    )
    await callback.message.answer(
        text=text,
        parse_mode="HTML"
    )


@router.callback_query(F.data == "admin_broadcast")
async def start_broadcast(callback: CallbackQuery, state: FSMContext):
    if callback.from_user.id not in ADMINS:
        await callback.answer("⛔️ Ruxsat berilmagan", show_alert=True)
        return

    await state.set_state(AdminStates.waiting_for_broadcast_message)
    await callback.message.answer(
        "✍️ <b>Barcha foydalanuvchilarga yuboriladigan xabarni (matn, rasm yoki video) kiriting:</b>\n\n"
        "<i>(Bekor qilish uchun /cancel deb yozing)</i>",
        parse_mode="HTML"
    )
    await callback.answer()


@router.message(AdminStates.waiting_for_broadcast_message)
async def process_broadcast(message: Message, state: FSMContext, bot: Bot):
    if message.text and message.text == "/cancel":
        await state.clear()
        await message.answer("❌ Xabar yuborish bekor qilindi.")
        return

    await state.clear()
    users = await db.get_all_users()
    total_users = len(users)

    status_msg = await message.answer(f"⏳ Xabar yuborilmoqda... (0/{total_users})")
    
    sent_count = 0
    blocked_count = 0

    for user in users:
        try:
            await message.copy_to(chat_id=user["user_id"])
            sent_count += 1
            await asyncio.sleep(0.05)  # To avoid flood limits
        except Exception:
            blocked_count += 1

    await status_msg.edit_text(
        f"✅ <b>Xabar yuborish yakunlandi!</b>\n\n"
        f"📨 Yuborildi: <b>{sent_count}</b> ta\n"
        f"🚫 Yetib bormadi (bloklagan): <b>{blocked_count}</b> ta",
        parse_mode="HTML"
    )
