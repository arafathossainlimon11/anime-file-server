import asyncio
import os
from aiohttp import web
from pyrogram import Client

# Your Official Telegram API Credentials
API_ID = 30783696
API_HASH = "5af98d47141b1b40a64c248aba36def2"

BOT_TOKEN = os.environ.get("BOT_TOKEN", "").strip()
CHANNEL_ID = int(os.environ.get("CHANNEL_ID", "0").strip() or "0")

routes = web.RouteTableDef()
bot = None


@routes.get("/")
async def home(request):
  return web.Response(
      text="Anime File Proxy Server is Running & Connected Successfully!"
  )


@routes.get("/download/{message_id}")
async def download_file(request):
  try:
    msg_id = int(request.match_info["message_id"])
    msg = await bot.get_messages(CHANNEL_ID, msg_id)

    if not msg or not msg.media:
      return web.Response(text="File not found in Telegram Channel!", status=404)

    media = getattr(msg, msg.media.value, None)
    file_size = getattr(media, "file_size", 0)
    file_name = getattr(media, "file_name", f"anime_{msg_id}.mp4")

    response = web.StreamResponse(
        status=200,
        headers={
            "Content-Type": "application/octet-stream",
            "Content-Disposition": f'attachment; filename="{file_name}"',
            "Content-Length": str(file_size),
        },
    )
    await response.prepare(request)

    async for chunk in bot.stream_media(msg):
      await response.write(chunk)

    return response
  except Exception as e:
    return web.Response(text=f"Error: {str(e)}", status=500)


async def main():
  global bot

  print("Starting Telegram Bot...")
  bot = Client(
      "file_proxy_bot",
      api_id=API_ID,
      api_hash=API_HASH,
      bot_token=BOT_TOKEN,
      in_memory=True,
  )
  await bot.start()
  print(">>> Telegram Bot Connected Successfully! <<<")

  app = web.Application()
  app.add_routes(routes)

  runner = web.AppRunner(app)
  await runner.setup()
  port = int(os.environ.get("PORT", 8080))
  site = web.TCPSite(runner, "0.0.0.0", port)
  await site.start()
  print(f"Server is live on port {port}")

  await asyncio.Event().wait()


if __name__ == "__main__":
  asyncio.run(main())
