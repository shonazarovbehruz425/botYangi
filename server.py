import os
import logging
import asyncio
from datetime import datetime
from aiohttp import web
from aiogram import Bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile, URLInputFile
from config import WEBAPP_PORT, ADMIN_PANEL_PASSWORD, BOT_TOKEN, BACKUP_CHANNEL_ID
from database.db import db
from database.backup import export_database_to_js_bytes

logger = logging.getLogger(__name__)

# Shared bot instance for server actions
_bot_instance: Bot = None

def set_bot_instance(bot: Bot):
    global _bot_instance
    _bot_instance = bot

async def start_webapp_server(bot: Bot = None):
    if bot:
        set_bot_instance(bot)

    app = web.Application()
    webapp_dir = os.path.join(os.path.dirname(__file__), "webapp")
    
    NO_CACHE_HEADERS = {
        "Cache-Control": "no-cache, no-store, must-revalidate, max-age=0",
        "Pragma": "no-cache",
        "Expires": "0"
    }

    # 1. Main Mini App Route
    async def index(request):
        return web.FileResponse(os.path.join(webapp_dir, "index.html"), headers=NO_CACHE_HEADERS)

    # 2. Admin Panel Route (/buyukhayotpanel)
    async def admin_panel(request):
        return web.FileResponse(os.path.join(webapp_dir, "admin.html"), headers=NO_CACHE_HEADERS)

    # 3. Live User Profile API for Mini App
    async def get_user_profile(request):
        try:
            user_id_param = request.query.get("user_id")
            if not user_id_param or not user_id_param.isdigit():
                return web.json_response({"success": False, "error": "user_id missing"}, status=400)

            uid = int(user_id_param)
            user = await db.get_user(uid)
            
            if not user:
                return web.json_response({
                    "success": True,
                    "registered": False,
                    "user": {
                        "user_id": uid,
                        "first_name": "Hamkor",
                        "last_name": "",
                        "username": "",
                        "current_level": 1,
                        "balance": 0.0,
                        "total_earned": 0.0,
                        "status": "🌱 Boshlang'ich",
                        "registered_at": "-",
                        "referrer_name": "Tizim",
                        "direct_referrals": 0,
                        "active_in_marketing": 0,
                        "team_total": 0,
                        "is_banned": 0,
                        "is_admin": (uid in ADMINS),
                        "multi_tier": {"level_1": 0, "level_2": 0, "level_3": 0, "total_team": 0},
                        "wallets": {"bep20": "", "card": "", "trc20": "", "payeer": ""}
                    }
                })

            # Fetch live stats
            try:
                ref_count = await db.get_referral_count(uid)
            except Exception:
                ref_count = 0
            try:
                team_stats = await db.get_multi_tier_stats(uid)
            except Exception:
                team_stats = {"level_1": 0, "level_2": 0, "level_3": 0, "total_team": 0}
            
            curator_text = "Bosh Admin (Tizim)"
            if user.get("referrer_id") and user["referrer_id"] != 0:
                try:
                    ref_obj = await db.get_user(user["referrer_id"])
                    if ref_obj:
                        c_name = f"{ref_obj.get('first_name', '')} {ref_obj.get('last_name', '')}".strip()
                        c_uname = f"@{ref_obj['username']}" if ref_obj.get("username") else ""
                        curator_text = f"{c_name} {c_uname}".strip()
                    else:
                        curator_text = f"ID: {user['referrer_id']}"
                except Exception:
                    curator_text = f"ID: {user['referrer_id']}"

            return web.json_response({
                "success": True,
                "registered": True,
                "user": {
                    "user_id": user["user_id"],
                    "first_name": user.get("first_name", "Hamkor"),
                    "last_name": user.get("last_name", ""),
                    "username": user.get("username", ""),
                    "current_level": user.get("current_level", 1),
                    "balance": user.get("balance", 0.0),
                    "total_earned": user.get("total_earned", 0.0),
                    "status": user.get("status", "🌱 Boshlang'ich"),
                    "registered_at": user.get("registered_at", "-")[:10] if user.get("registered_at") else "-",
                    "referrer_name": curator_text,
                    "direct_referrals": ref_count,
                    "active_in_marketing": max(0, ref_count * 2),
                    "team_total": team_stats.get("total_team", 0),
                    "is_banned": user.get("is_banned", 0),
                    "is_admin": (uid in ADMINS),
                    "multi_tier": team_stats,
                    "wallets": {
                        "bep20": user.get("wallet_bep20", ""),
                        "card": user.get("wallet_card", ""),
                        "trc20": user.get("wallet_trc20", ""),
                        "payeer": user.get("wallet_payeer", "")
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error in get_user_profile: {e}", exc_info=True)
            return web.json_response({"success": False, "error": str(e)}, status=500)

    # 3b. Live User Tree API for Mini App
    async def get_user_tree_api(request):
        try:
            user_id_param = request.query.get("user_id")
            if not user_id_param or not user_id_param.isdigit():
                return web.json_response({"success": False, "error": "user_id missing"}, status=400)
            uid = int(user_id_param)
            tree = await db.get_user_tree(uid)
            return web.json_response({"success": True, "tree": tree, "is_admin": (uid in ADMINS)})
        except Exception as e:
            logger.error(f"Error in get_user_tree_api: {e}", exc_info=True)
            return web.json_response({"success": False, "error": str(e)}, status=500)

    # 3c. User Tree Node Replace API
    async def user_tree_replace_api(request):
        try:
            data = await request.json()
            target_user_id = int(data.get("target_user_id", 0))
            new_identifier = str(data.get("new_identifier", "")).strip()
            requester_id = int(data.get("requester_id", 0))

            if not target_user_id or not new_identifier or not requester_id:
                return web.json_response({"success": False, "error": "Barcha maydonlar to'ldirilishi shart"}, status=400)

            if requester_id not in ADMINS:
                return web.json_response({"success": False, "error": "Faqatgina adminlar a'zolarni almashtira oladi"}, status=403)

            res = await db.replace_user_in_tree(target_user_id, new_identifier, requester_id)
            if res.get("success"):
                asyncio.create_task(db_backup_manager.backup_and_send(bot_instance))
            return web.json_response(res)
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    # 3d. User Tree Node Insert Between API
    async def user_tree_insert_api(request):
        try:
            data = await request.json()
            target_user_id = int(data.get("target_user_id", 0))
            new_identifier = str(data.get("new_identifier", "")).strip()
            requester_id = int(data.get("requester_id", 0))
            mode = str(data.get("mode", "above"))

            if not target_user_id or not new_identifier or not requester_id:
                return web.json_response({"success": False, "error": "Barcha maydonlar to'ldirilishi shart"}, status=400)

            if requester_id not in ADMINS:
                return web.json_response({"success": False, "error": "Faqatgina adminlar zanjir orasiga a'zo qo'sha oladi"}, status=403)

            res = await db.insert_user_in_between(target_user_id, new_identifier, requester_id, mode)
            if res.get("success"):
                asyncio.create_task(db_backup_manager.backup_and_send(bot_instance))
            return web.json_response(res)
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    # 4. Admin Auth API
    async def admin_auth(request):
        try:
            data = await request.json()
            entered_pass = data.get("password", "")
            if entered_pass == ADMIN_PANEL_PASSWORD:
                return web.json_response({"success": True})
            return web.json_response({"success": False, "error": "Noto'g'ri parol"}, status=401)
        except Exception:
            return web.json_response({"success": False}, status=400)

    # 5. Admin Users List API
    async def admin_get_users(request):
        users = await db.get_all_users()
        return web.json_response({"users": users})

    # 6. Admin User Update API
    async def admin_update_user(request):
        try:
            data = await request.json()
            user_id = int(data.get("user_id"))
            first_name = data.get("first_name", "")
            last_name = data.get("last_name", "")
            username = data.get("username", "").replace("@", "")
            level = int(data.get("current_level", 1))
            balance = float(data.get("balance", 0.0))
            total_earned = float(data.get("total_earned", 30.0))
            status = data.get("status", "🌱 Boshlang'ich")
            wallet_bep20 = data.get("wallet_bep20", "")
            wallet_card = data.get("wallet_card", "")
            wallet_trc20 = data.get("wallet_trc20", "")
            wallet_payeer = data.get("wallet_payeer", "")

            await db.update_user_full(
                user_id, first_name, last_name, username, level, balance, total_earned,
                status, wallet_bep20, wallet_card, wallet_trc20, wallet_payeer
            )
            return web.json_response({"success": True, "message": "Foydalanuvchi ma'lumotlari yangilandi"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    # 7. Admin Ban / Unban User API
    async def admin_ban_user(request):
        try:
            data = await request.json()
            user_id = int(data.get("user_id"))
            is_banned = int(data.get("is_banned", 0))
            await db.set_user_ban_status(user_id, is_banned)
            return web.json_response({"success": True, "is_banned": is_banned})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    # 8. Admin Change Referrer API
    async def admin_change_referrer(request):
        try:
            data = await request.json()
            user_id = int(data.get("user_id"))
            new_referrer_id = int(data.get("new_referrer_id", 0))
            
            if user_id == new_referrer_id:
                return web.json_response({"success": False, "error": "Foydalanuvchi o'ziga kurator bo'la olmaydi"}, status=400)

            await db.change_user_referrer(user_id, new_referrer_id)
            return web.json_response({"success": True, "message": "Kurator muvaffaqiyatli almashtirildi"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    # 8b. Admin Delete User API
    async def admin_delete_user(request):
        try:
            data = await request.json()
            user_id = int(data.get("user_id"))
            from config import ADMINS
            if user_id in ADMINS:
                return web.json_response({"success": False, "error": "Admin hisobini o'chirish mumkin emas!"}, status=403)
            await db.delete_user(user_id)

            if _bot_instance:
                from database.backup import send_database_backup_to_channel
                asyncio.create_task(send_database_backup_to_channel(_bot_instance, reason=f"Foydalanuvchi o'chirildi (ID: {user_id})"))

            return web.json_response({"success": True, "message": f"Foydalanuvchi {user_id} o'chirildi"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    # 9. Admin Visual Tree Graph API
    async def admin_get_tree(request):
        user_id_param = request.query.get("user_id")
        if not user_id_param or not user_id_param.isdigit():
            return web.json_response({"success": False, "error": "user_id kerak"}, status=400)
        tree = await db.get_user_tree(int(user_id_param))
        return web.json_response({"success": True, "tree": tree})

    # 10. Admin Leaderboard API
    async def admin_get_leaders(request):
        leaders = await db.get_top_leaders(30)
        return web.json_response({"success": True, "leaders": leaders})

    # 11. Admin Levels Settings API
    async def admin_get_levels(request):
        levels = await db.get_level_settings()
        return web.json_response({"success": True, "levels": levels})

    async def admin_update_level(request):
        try:
            data = await request.json()
            level = int(data.get("level"))
            price = float(data.get("price"))
            name = data.get("name")
            await db.update_level_price(level, price, name)
            return web.json_response({"success": True, "message": f"{level}-daraja narxi ${price} ga yangilandi"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    # 12. Admin Rich Targeted Broadcast API
    async def admin_send_broadcast(request):
        try:
            data = await request.json()
            text = data.get("text", "").strip()
            photo_url = data.get("photo_url", "").strip()
            button_text = data.get("button_text", "").strip()
            button_url = data.get("button_url", "").strip()
            filter_type = data.get("filter_type", "all")

            if not text:
                return web.json_response({"success": False, "error": "Xabar matni bo'sh bo'lishi mumkin emas"}, status=400)

            user_ids = await db.get_filtered_user_ids(filter_type)
            if not user_ids:
                return web.json_response({"success": False, "error": "Ushbu filter bo'yicha foydalanuvchilar topilmadi"}, status=400)

            # Build keyboard if button provided
            reply_markup = None
            if button_text and button_url:
                reply_markup = InlineKeyboardMarkup(inline_keyboard=[
                    [InlineKeyboardButton(text=button_text, url=button_url)]
                ])

            sent_count = 0
            fail_count = 0

            bot_to_use = _bot_instance or Bot(token=BOT_TOKEN)

            for uid in user_ids:
                try:
                    if photo_url and photo_url.startswith("http"):
                        await bot_to_use.send_photo(
                            chat_id=uid,
                            photo=photo_url,
                            caption=text,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                    else:
                        await bot_to_use.send_message(
                            chat_id=uid,
                            text=text,
                            reply_markup=reply_markup,
                            parse_mode="HTML"
                        )
                    sent_count += 1
                    await asyncio.sleep(0.04)  # Anti-flood rate limiting
                except Exception:
                    fail_count += 1

            if not _bot_instance:
                await bot_to_use.session.close()

            # Save history
            await db.save_broadcast(text, photo_url, button_text, button_url, filter_type, sent_count, fail_count)
            return web.json_response({
                "success": True,
                "total": len(user_ids),
                "sent": sent_count,
                "failed": fail_count
            })
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    # 13. Admin Broadcast History API
    async def admin_broadcast_history(request):
        history = await db.get_broadcast_history()
        return web.json_response({"success": True, "history": history})

    # 14. Mini App Announcement API
    async def admin_save_announcement(request):
        try:
            data = await request.json()
            title = data.get("title", "").strip()
            text = data.get("text", "").strip()
            if not text:
                await db.delete_announcements()
                return web.json_response({"success": True, "message": "E'lonlar o'chirildi"})
            await db.set_active_announcement(title, text)
            return web.json_response({"success": True, "message": "Mini App e'loni faollashtirildi"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=400)

    async def get_active_announcement(request):
        ann = await db.get_active_announcement()
        return web.json_response({"success": True, "announcement": ann})

    # 15. Auto-Post Official Stats Flyer to Channel API
    async def admin_post_to_channel(request):
        try:
            if not BACKUP_CHANNEL_ID:
                return web.json_response({"success": False, "error": "Kanal ID belgilanmagan"}, status=400)

            total_users = await db.get_total_users_count()
            top_leaders = await db.get_top_leaders(5)
            leaders_text = ""
            for idx, l in enumerate(top_leaders, 1):
                name = f"{l['first_name']} {l['last_name']}".strip() or "Hamkor"
                leaders_text += f"{idx}. 👑 <b>{name}</b> — {l['direct_count']} ta hamkor\n"

            now_str = datetime.now().strftime("%d.%m.%Y %H:%M")
            post_caption = (
                "👑 <b>«BUYUK HAYOTGA YO'L» — KUNLIK RASMIY HISOBOT</b>\n\n"
                f"📅 <b>Sana:</b> {now_str}\n"
                f"👥 <b>Jami a'zolar:</b> {total_users} nafar\n"
                f"⚡️ <b>Faol darajalar:</b> 1 - 6 Bosqichlar\n\n"
                "🏆 <b>ENG FAOL LIDERLAR REYTINGI:</b>\n"
                f"{leaders_text}\n"
                "✨ <i>Ният – Ишонч – Ҳаракат – Натижа!</i>\n\n"
                "🚀 <b>Botga kirish:</b> @Buyukhayot_bot"
            )

            bot_to_use = _bot_instance or Bot(token=BOT_TOKEN)
            banner_path = os.path.join(os.path.dirname(__file__), "assets", "main_banner.png")
            
            keyboard = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text="🚀 Botni ishga tushirish", url="https://t.me/Buyukhayot_bot")]
            ])

            if os.path.exists(banner_path):
                await bot_to_use.send_photo(
                    chat_id=BACKUP_CHANNEL_ID,
                    photo=FSInputFile(banner_path),
                    caption=post_caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )
            else:
                await bot_to_use.send_message(
                    chat_id=BACKUP_CHANNEL_ID,
                    text=post_caption,
                    reply_markup=keyboard,
                    parse_mode="HTML"
                )

            if not _bot_instance:
                await bot_to_use.session.close()

            return web.json_response({"success": True, "message": "Kanalga rasmiy post muvaffaqiyatli chop etildi!"})
        except Exception as e:
            return web.json_response({"success": False, "error": str(e)}, status=500)

    # 16. Audit Logs API
    async def admin_get_logs(request):
        logs = await db.get_recent_logs(50)
        return web.json_response({"success": True, "logs": logs})

    # 17. Admin Backup Download API
    async def admin_download_backup(request):
        js_bytes, filename, _ = await export_database_to_js_bytes()
        return web.Response(
            body=js_bytes,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/javascript; charset=utf-8"
            }
        )

    # 18. Admin Restore Database from Channel API
    async def admin_restore_channel(request):
        bot_to_use = _bot_instance or Bot(token=BOT_TOKEN)
        from database.backup import restore_database_from_channel
        count = await restore_database_from_channel(bot_to_use)
        if not _bot_instance:
            await bot_to_use.session.close()
        return web.json_response({"success": True, "count": count})

    # Register Routes
    app.router.add_get("/", index)
    app.router.add_get("/buyukhayotpanel", admin_panel)
    app.router.add_get("/api/user/profile", get_user_profile)
    app.router.add_get("/api/user/tree", get_user_tree_api)
    app.router.add_post("/api/user/tree/replace", user_tree_replace_api)
    app.router.add_post("/api/user/tree/insert", user_tree_insert_api)
    app.router.add_get("/api/announcements/active", get_active_announcement)

    # Admin APIs
    app.router.add_post("/api/admin/auth", admin_auth)
    app.router.add_get("/api/admin/users", admin_get_users)
    app.router.add_post("/api/admin/user/update", admin_update_user)
    app.router.add_post("/api/admin/user/ban", admin_ban_user)
    app.router.add_post("/api/admin/user/delete", admin_delete_user)
    app.router.add_post("/api/admin/user/referrer", admin_change_referrer)
    app.router.add_get("/api/admin/user/tree", admin_get_tree)
    app.router.add_get("/api/admin/leaders", admin_get_leaders)
    app.router.add_get("/api/admin/levels", admin_get_levels)
    app.router.add_post("/api/admin/levels/update", admin_update_level)
    app.router.add_post("/api/admin/broadcast", admin_send_broadcast)
    app.router.add_get("/api/admin/broadcast/history", admin_broadcast_history)
    app.router.add_post("/api/admin/announcement", admin_save_announcement)
    app.router.add_post("/api/admin/channel/post", admin_post_to_channel)
    app.router.add_get("/api/admin/logs", admin_get_logs)
    app.router.add_get("/api/admin/backup/download", admin_download_backup)
    app.router.add_post("/api/admin/backup/restore_channel", admin_restore_channel)

    # Static assets
    app.router.add_static("/", webapp_dir, show_index=True)

    runner = web.AppRunner(app)
    await runner.setup()

    # Try binding on configured port or fallback
    ports_to_try = [WEBAPP_PORT, 8085, 8090, 5000, 3000, 0]
    seen = set()
    ports_to_try = [p for p in ports_to_try if not (p in seen or seen.add(p))]

    site = None
    active_port = None

    for port in ports_to_try:
        try:
            site = web.TCPSite(runner, "0.0.0.0", port)
            await site.start()
            if port == 0 and site._server and site._server.sockets:
                active_port = site._server.sockets[0].getsockname()[1]
            else:
                active_port = port
            logger.info(f"🌐 Mini App & Admin Panel ishga tushdi: http://localhost:{active_port}")
            logger.info(f"👑 Admin Panel manzili: http://localhost:{active_port}/buyukhayotpanel")
            break
        except OSError:
            continue

    return runner
