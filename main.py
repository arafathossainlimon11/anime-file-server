import asyncio
import os

# Create event loop before importing Pyrogram
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

from aiohttp import web
from pyrogram import Client

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0"))

bot = Client("file_proxy_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

routes = web.RouteTableDef()

@routes.get("/")
async def home(request):
    return web.Response(text="Anime File Proxy Server is Running!")

@routes.get("/download/{message_id}")
async def download_file(request):
    try:
        msg_id = int(request.match_info['message_id'])
        msg = await bot.get_messages(CHANNEL_ID, msg_id)
        if not msg or not msg.media:
            return web.Response(text="File not found!", status=404)

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
        return web.Response(text=f"Error: {str(e)}", status=500)

app = web.Application()
app.add_routes(routes)

async def start_services():
    await bot.start()
    runner = web.AppRunner(app)
    await runner.setup()
    port = int(os.environ.get("PORT", 8080))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()

if __name__ == "__main__":
    loop.run_until_complete(start_services())
    loop.run_forever()
