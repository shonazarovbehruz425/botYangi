import os
import logging
import json
from aiohttp import web
from config import WEBAPP_PORT, ADMIN_PANEL_PASSWORD
from database.db import db
from database.backup import export_database_to_js_bytes

logger = logging.getLogger(__name__)

async def start_webapp_server():
    app = web.Application()
    webapp_dir = os.path.join(os.path.dirname(__file__), "webapp")
    
    # 1. Main Mini App Route
    async def index(request):
        return web.FileResponse(os.path.join(webapp_dir, "index.html"))

    # 2. Admin Panel Route (/buyukhayotpanel)
    async def admin_panel(request):
        return web.FileResponse(os.path.join(webapp_dir, "admin.html"))

    # 3. Live User Profile API for Mini App
    async def get_user_profile(request):
        user_id_param = request.query.get("user_id")
        if not user_id_param or not user_id_param.isdigit():
            return web.json_response({"success": False, "error": "user_id missing"}, status=400)

        uid = int(user_id_param)
        user = await db.get_user(uid)
        
        if not user:
            # Return fresh default for unverified guest
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
                    "total_earned": 30.0,
                    "status": "🌱 Boshlang'ich",
                    "registered_at": "-",
                    "referrer_name": "Tizim",
                    "direct_referrals": 0,
                    "active_in_marketing": 0,
                    "team_total": 0,
                    "multi_tier": {"level_1": 0, "level_2": 0, "level_3": 0, "total_team": 0},
                    "wallets": {"bep20": "", "card": "", "trc20": "", "payeer": ""}
                }
            })

        # Fetch live stats
        ref_count = await db.get_referral_count(uid)
        team_stats = await db.get_multi_tier_stats(uid)
        
        # Curator name
        curator_text = "Bosh Admin (Tizim)"
        if user.get("referrer_id") and user["referrer_id"] != 0:
            ref_obj = await db.get_user(user["referrer_id"])
            if ref_obj:
                c_name = f"{ref_obj.get('first_name', '')} {ref_obj.get('last_name', '')}".strip()
                c_uname = f"@{ref_obj['username']}" if ref_obj.get("username") else ""
                curator_text = f"{c_name} {c_uname}".strip()
            else:
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
                "total_earned": user.get("total_earned", 30.0),
                "status": user.get("status", "🌱 Boshlang'ich"),
                "registered_at": user.get("registered_at", "-")[:10] if user.get("registered_at") else "-",
                "referrer_name": curator_text,
                "direct_referrals": ref_count,
                "active_in_marketing": max(0, ref_count * 2),
                "team_total": team_stats["total_team"],
                "multi_tier": team_stats,
                "wallets": {
                    "bep20": user.get("wallet_bep20", ""),
                    "card": user.get("wallet_card", ""),
                    "trc20": user.get("wallet_trc20", ""),
                    "payeer": user.get("wallet_payeer", "")
                }
            }
        })

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

    # 6. Admin Backup Download API
    async def admin_download_backup(request):
        js_bytes, filename, _ = await export_database_to_js_bytes()
        return web.Response(
            body=js_bytes,
            headers={
                "Content-Disposition": f'attachment; filename="{filename}"',
                "Content-Type": "application/javascript; charset=utf-8"
            }
        )

    app.router.add_get("/", index)
    app.router.add_get("/buyukhayotpanel", admin_panel)
    app.router.add_get("/api/user/profile", get_user_profile)
    app.router.add_post("/api/admin/auth", admin_auth)
    app.router.add_get("/api/admin/users", admin_get_users)
    app.router.add_get("/api/admin/backup/download", admin_download_backup)

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
