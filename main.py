import asyncio
import os
from urllib.parse import quote
from aiohttp import web
from pyrogram import Client

# Credentials from Environment Variables (Secure)
API_ID = int(os.environ.get("API_ID", "30783696").strip())
API_HASH = os.environ.get("API_HASH", "5af98d47141b1b40a64c248aba36def2").strip()
BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1004208629055").strip())

bot = Client(
    "file_proxy_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

routes = web.RouteTableDef()

@routes.get("/")
async def home(request):
    if bot.is_connected:
        return web.Response(text="Anime File Proxy Server is Live & Telegram Bot Connected Successfully!")
    return web.Response(text="Server is Running! Connecting to Telegram Bot...")

@routes.get("/download/{message_id}")
async def download_file(request):
    if not bot.is_connected:
        return web.Response(text="Bot is connecting to Telegram, please wait a few seconds and refresh!", status=503)
        
    try:
        msg_id = int(request.match_info['message_id'])
        msg = await bot.get_messages(CHANNEL_ID, msg_id)

        if not msg or not msg.media:
            return web.Response(text="File not found in Telegram Channel!", status=404)

        media = getattr(msg, msg.media.value, None)
        file_size = getattr(media, "file_size", 0)
        file_name = getattr(media, "file_name", f"anime_{msg_id}.mp4")
        safe_file_name = quote(file_name)

        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename="{safe_file_name}"',
                'Content-Length': str(file_size)
            }
        )
        await response.prepare(request)

        async for chunk in bot.stream_media(msg):
            await response.write(chunk)

        return response
    except Exception as e:
        return web.Response(text=f"Error streaming file: {str(e)}", status=500)

async def start_bot(app):
    try:
        await bot.start()
        print(">>> Telegram Bot Connected Successfully! <<<")
    except Exception as e:
        print(f">>> Telegram Bot Error: {e} <<<")

async def stop_bot(app):
    if bot.is_connected:
        await bot.stop()

app = web.Application()
app.add_routes(routes)
app.on_startup.append(start_bot)
app.on_cleanup.append(stop_bot)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
