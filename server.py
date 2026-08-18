import os
import logging
from aiohttp import web
from config import WEBAPP_PORT

logger = logging.getLogger(__name__)

async def start_webapp_server():
    app = web.Application()
    webapp_dir = os.path.join(os.path.dirname(__file__), "webapp")
    
    # Serve index.html at root
    async def index(request):
        return web.FileResponse(os.path.join(webapp_dir, "index.html"))

    app.router.add_get("/", index)
    app.router.add_static("/", webapp_dir, show_index=True)

    runner = web.AppRunner(app)
    await runner.setup()

    # Try binding on configured port or find an available port
    ports_to_try = [WEBAPP_PORT, 8085, 8090, 5000, 3000, 0]
    # Remove duplicates preserving order
    seen = set()
    ports_to_try = [p for p in ports_to_try if not (p in seen or seen.add(p))]

    site = None
    active_port = None

    for port in ports_to_try:
        try:
            site = web.TCPSite(runner, "0.0.0.0", port)
            await site.start()
            # If port 0 was passed, get allocated port
            if port == 0 and site._server and site._server.sockets:
                active_port = site._server.sockets[0].getsockname()[1]
            else:
                active_port = port
            logger.info(f"🌐 Mini App Web server muvaffaqiyatli ishga tushdi: http://localhost:{active_port}")
            break
        except OSError:
            continue

    if not site:
        logger.warning("⚠️ Mini App veb-serveri uchun bo'sh port topilmadi. Bot veb-serversiz davom etadi.")

    return runner
