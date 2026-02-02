import os
import sys
import traceback
from datetime import datetime

from pyrogram import Client, filters
from pyrogram.errors import UserNotParticipant
from pyrogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    BotCommand,
    BotCommandScopeChat,
    BotCommandScopeDefault
)

# ─── ENV VARIABLES ─────────────────────
REQUIRED_VARS = [
    "API_ID",
    "API_HASH",
    "BOT_TOKEN",
    "ADMIN_ID",
    "DB_CHANNEL",
    "FORCE_CHANNEL",
    "LOG_CHANNEL"
]

missing = [v for v in REQUIRED_VARS if not os.getenv(v)]
if missing:
    print(f"❌ Missing ENV variables: {', '.join(missing)}")
    sys.exit(1)

API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = int(os.getenv("ADMIN_ID"))
DB_CHANNEL = int(os.getenv("DB_CHANNEL"))
FORCE_CHANNEL = int(os.getenv("FORCE_CHANNEL"))
LOG_CHANNEL = int(os.getenv("LOG_CHANNEL"))

app = Client(
    "secure_file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

ALBUM_CACHE = {}
USERS = set()

# ─── SAFE LOGGER ───────────────────────
async def safe_log(text: str):
    try:
        await app.send_message(LOG_CHANNEL, text)
    except:
        pass

# ─── FORCE JOIN CHECK ──────────────────
async def check_join(client, user_id):
    if user_id == ADMIN_ID:
        return True
    try:
        await client.get_chat_member(FORCE_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False
    except:
        return False

# ─── ACCESS LOGGER ─────────────────────
async def log_access(user, file_id):
    text = (
        "📥 FILE ACCESS LOG\n\n"
        f"👤 User: {user.first_name} ({user.id})\n"
        f"📦 File ID: {file_id}\n"
        f"🕒 Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')} UTC"
    )
    await safe_log(text)

# ─── ADMIN COMMAND MENU ────────────────
async def setup_commands(client):
    # Clear commands for everyone
    await client.set_bot_commands(
        commands=[],
        scope=BotCommandScopeDefault()
    )

    # Admin-only commands
    await client.set_bot_commands(
        commands=[
            BotCommand("admin", "Admin panel"),
            BotCommand("stats", "Bot statistics")
        ],
        scope=BotCommandScopeChat(chat_id=ADMIN_ID)
    )

# ─── START COMMAND ─────────────────────
@app.on_message(filters.command("start"))
async def start(client, message):
    USERS.add(message.from_user.id)

    if not await check_join(client, message.from_user.id):
        await message.reply(
            "🔒 You must join our channel to use this bot.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("📢 Join Channel", url="https://t.me/+r7j8QFkHrPAzNDU1")]]
            )
        )
        return

    if len(message.command) == 1:
        await message.reply(
            "👋 Welcome\n\n"
            "Use the shared link to access files.\n"
            "Forwarding is restricted."
        )
        return

    try:
        msg_id = int(message.command[1])
        msg = await client.get_messages(DB_CHANNEL, msg_id)

        if msg.media_group_id:
            media = await client.get_media_group(DB_CHANNEL, msg.id)
            for m in media:
                await client.copy_message(
                    message.chat.id,
                    DB_CHANNEL,
                    m.id,
                    protect_content=True
                )
            await log_access(message.from_user, f"Album:{msg_id}")
        else:
            await client.copy_message(
                message.chat.id,
                DB_CHANNEL,
                msg.id,
                protect_content=True
            )
            await log_access(message.from_user, msg_id)

    except Exception:
        await message.reply("❌ Invalid or removed link.")

# ─── ADMIN: SINGLE FILE ────────────────
@app.on_message(
    filters.private &
    filters.media &
    filters.user(ADMIN_ID) &
    ~filters.media_group
)
async def save_single(client, message):
    sent = await message.copy(DB_CHANNEL)
    link = f"https://t.me/{client.me.username}?start={sent.id}"
    await message.reply(f"✅ File stored\n\n🔗 {link}")

# ─── ADMIN: ALBUM ──────────────────────
@app.on_message(
    filters.private &
    filters.media_group &
    filters.user(ADMIN_ID)
)
async def save_album(client, message):
    gid = message.media_group_id
    ALBUM_CACHE.setdefault(gid, [])

    sent = await message.copy(DB_CHANNEL)
    ALBUM_CACHE[gid].append(sent.id)

    if len(ALBUM_CACHE[gid]) == message.media_group_count:
        first_id = ALBUM_CACHE[gid][0]
        link = f"https://t.me/{client.me.username}?start={first_id}"
        await message.reply(f"✅ Album stored\n\n🔗 {link}")
        del ALBUM_CACHE[gid]

# ─── BLOCK USER UPLOADS ─────────────────
@app.on_message(filters.private & filters.media)
async def block_users(_, message):
    if message.from_user.id != ADMIN_ID:
        await message.reply("🚫 Only admin can upload files.")

# ─── ADMIN COMMANDS ────────────────────
@app.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_panel(_, message):
    await message.reply("👑 Admin Panel\n\n/stats – Bot statistics")

@app.on_message(filters.command("stats") & filters.user(ADMIN_ID))
async def stats(_, message):
    await message.reply(f"📊 Bot Stats\n\n👥 Users: {len(USERS)}")

# ─── GLOBAL ERROR HANDLER ───────────────
@app.on_error()
async def error_handler(_, error):
    tb = "".join(traceback.format_exception(None, error, error.__traceback__))
    await safe_log(f"❌ BOT ERROR\n\n{tb[:3500]}")

# ─── RUN ───────────────────────────────
async def main():
    await app.start()
    await setup_commands(app)
    await safe_log("✅ Bot started / restarted successfully")
    await app.idle()

app.run(main)
