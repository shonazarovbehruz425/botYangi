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

    # 3. Admin Auth API
    async def admin_auth(request):
        try:
            data = await request.json()
            entered_pass = data.get("password", "")
            if entered_pass == ADMIN_PANEL_PASSWORD:
                return web.json_response({"success": True})
            return web.json_response({"success": False, "error": "Noto'g'ri parol"}, status=401)
        except Exception:
            return web.json_response({"success": False}, status=400)

    # 4. Admin Users List API
    async def admin_get_users(request):
        users = await db.get_all_users()
        return web.json_response({"users": users})

    # 5. Admin Backup Download API
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
