#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
HGB Welcome Bot — Entry point.
"""
import os
import sys
os.environ["PYTHONUNBUFFERED"] = "1"
os.environ["PYTHONIOENCODING"] = "utf-8"

if sys.platform == "win32":
    sys.stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", buffering=1)
    sys.stderr = open(sys.stderr.fileno(), mode="w", encoding="utf-8", buffering=1)
else:
    try:
        sys.stdout.reconfigure(encoding="utf-8", line_buffering=True)
        sys.stderr.reconfigure(encoding="utf-8", line_buffering=True)
    except Exception:
        pass

print("bot.py đang khởi động...", flush=True)

import discord
import asyncio
import traceback
from discord.ext import commands
from dotenv import load_dotenv

import database
import welcome as welcome_module

load_dotenv()

intents = discord.Intents.default()
intents.message_content = True
intents.members = True          # BẮT BUỘC cho welcome/goodbye

bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)


@bot.event
async def on_ready():
    print("=" * 50)
    print(f"✅ Logged in as: {bot.user.name} (ID: {bot.user.id})")
    print(f"🌐 Guilds: {len(bot.guilds)}")
    print("=" * 50)

    await database.get_db()
    print("💾 Database ready.")

    # Setup module 1 lần duy nhất
    if not getattr(bot, "_modules_loaded", False):
        welcome_module.setup_welcome(bot)
        bot._modules_loaded = True

    try:
        synced = await bot.tree.sync()
        print(f"🔄 Synced {len(synced)} slash commands.")
    except Exception as e:
        print(f"❌ Sync error: {e}")

    await bot.change_presence(
        activity=discord.Activity(
            type=discord.ActivityType.watching,
            name="👋 Welcome & Goodbye | /help"
        )
    )


async def main_runner():
    token = os.getenv("DISCORD_BOT_TOKEN")
    if not token:
        print("❌ LỖI: Chưa cấu hình DISCORD_BOT_TOKEN trong file .env")
        return

    retry_delay = 30
    while True:
        # Reset HTTP session nếu cần (tránh "Session is closed")
        try:
            if getattr(bot, "http", None) is not None:
                if getattr(bot.http, "_session", None) is not None:
                    if not bot.http._session.closed:
                        await bot.http._session.close()
                bot.http._session = None
                bot.http._global_over = asyncio.Event()
                bot.http._global_over.set()
        except Exception:
            pass

        try:
            await bot.start(token)
        except discord.errors.HTTPException as e:
            if e.status == 429:
                retry_delay = 120
                print(f"⚠️ Rate limited. Nghỉ {retry_delay}s...")
            else:
                print(f"❌ HTTP error ({e.status}): {e}. Nghỉ {retry_delay}s...")
                traceback.print_exc()
        except Exception as e:
            print(f"❌ Bot error: {type(e).__name__}: {e}. Nghỉ {retry_delay}s...")
            traceback.print_exc()

        try:
            await bot.close()
        except Exception:
            pass

        await database.close_db()
        await asyncio.sleep(retry_delay)
        print("🔄 Đang thử kết nối lại Discord...")


if __name__ == "__main__":
    try:
        asyncio.run(main_runner())
    except KeyboardInterrupt:
        print("\n👋 Bot dừng bởi người dùng.")
    except Exception as e:
        print(f"💥 CRASH: {type(e).__name__}: {e}")
        traceback.print_exc()
        sys.exit(1)