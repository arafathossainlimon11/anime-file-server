import os
from aiohttp import web
from pyrogram import Client

# Official Telegram Desktop Credentials (Always Working for Bots)
API_ID = 2040
API_HASH = "b18441a1ed609ea10b776a12d1b0a728"

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0").strip() or "0")

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
    status = "Connected" if bot.is_connected else "Connecting..."
    return web.Response(text=f"Anime File Proxy Server is Running! Bot Status: {status}")

@routes.get("/download/{message_id}")
async def download_file(request):
    if not bot.is_connected:
        return web.Response(text="Bot is connecting to Telegram, please try again in a few seconds!", status=503)
        
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
        return web.Response(text=f"Error streaming file: {str(e)}", status=500)

async def start_bot(app):
    try:
        await bot.start()
        print(">>> Telegram Bot Started Successfully <<<")
    except Exception as e:
        print(f">>> Error starting bot: {e} <<<")

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
