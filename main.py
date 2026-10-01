import asyncio
import os
from aiohttp import web
from pyrogram import Client

# Official Telegram Android App Credentials (Always Working for All Bots)
API_ID = 6
API_HASH = "eb6e06552671a5513d2a34241d99d316"

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8878615893:AAHpmwUINy3Cv8v6dpTE2h7m5tIEUUxdB80").strip()
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "-1004208629055").strip())

routes = web.RouteTableDef()
bot = None
bot_connected = False
bot_error_message = None

@routes.get("/")
async def home(request):
    if bot_connected:
        return web.Response(text="Anime File Proxy Server is Live & Telegram Bot Connected Successfully!")
    elif bot_error_message:
        return web.Response(text=f"Server is Running, but Telegram Bot Error: {bot_error_message}")
    else:
        return web.Response(text="Server is Running. Connecting to Telegram Bot...")

@routes.get("/download/{message_id}")
async def download_file(request):
    if not bot_connected:
        err = bot_error_message or "Connecting..."
        return web.Response(text=f"Bot not connected yet. Details: {err}", status=503)
        
    try:
        msg_id = int(request.match_info['message_id'])
        msg = await bot.get_messages(CHANNEL_ID, msg_id)

        if not msg or not msg.media:
            return web.Response(text="File not found in Telegram Channel!", status=404)

        media = getattr(msg, msg.media.value, None)
        file_size = getattr(media, "file_size", 0)
        file_name = getattr(media, "file_name", f"anime_{msg_id}.mp4")

        response = web.StreamResponse(
            status=200,
            headers={
                'Content-Type': 'application/octet-stream',
                'Content-Disposition': f'attachment; filename="{file_name}"',
                'Content-Length': str(file_size)
            }
        )
        await response.prepare(request)

        async for chunk in bot.stream_media(msg):
            await response.write(chunk)

        return response
    except Exception as e:
        return web.Response(text=f"Error downloading file: {str(e)}", status=500)

async def start_telegram_bot(app):
    global bot, bot_connected, bot_error_message
    try:
        bot = Client(
            "file_proxy_bot",
            api_id=API_ID,
            api_hash=API_HASH,
            bot_token=BOT_TOKEN,
            in_memory=True
        )
        await bot.start()
        bot_connected = True
        print(">>> Telegram Bot Connected Successfully! <<<")
    except Exception as e:
        bot_connected = False
        bot_error_message = str(e)
        print(f">>> Telegram Bot Error: {e} <<<")

async def cleanup_bot(app):
    if bot and bot.is_connected:
        await bot.stop()

async def start_bg_task(app):
    asyncio.create_task(start_telegram_bot(app))

app = web.Application()
app.add_routes(routes)
app.on_startup.append(start_bg_task)
app.on_cleanup.append(cleanup_bot)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8080))
    web.run_app(app, host="0.0.0.0", port=port)
