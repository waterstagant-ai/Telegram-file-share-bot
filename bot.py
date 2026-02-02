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

# ===================== ENV VALIDATION =====================

REQUIRED_VARS = [
    "API_ID",
    "API_HASH",
    "BOT_TOKEN",
    "DB_CHANNEL_ID",
    "FORCE_SUB_CHANNEL",
    "ADMIN_IDS"
]

missing = [v for v in REQUIRED_VARS if not os.environ.get(v)]
if missing:
    print("❌ FATAL CONFIG ERROR")
    print("Missing environment variables:")
    for v in missing:
        print(f"  - {v}")
    print("\n👉 Fix this in Railway → Variables → Redeploy")
    sys.exit(1)

# ===================== CONFIG =====================

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_CHANNEL_ID = int(os.environ["DB_CHANNEL_ID"])
FORCE_SUB_CHANNEL = int(os.environ["FORCE_SUB_CHANNEL"])
ADMIN_IDS = list(map(int, os.environ["ADMIN_IDS"].split(",")))

# ===================== BOT =====================

app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
    in_memory=True
)

# ===================== HELPERS =====================

def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def force_sub_check(client, user_id: int) -> bool:
    try:
        await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return True
    except UserNotParticipant:
        return False


def build_share_link(message_id: int) -> str:
    return f"https://t.me/{BOT_USERNAME}?start=file_{message_id}"

# ===================== STARTUP =====================

@app.on_start()
async def startup(client):
    global BOT_USERNAME
    me = await client.get_me()
    BOT_USERNAME = me.username

    print("✅ Bot started successfully")
    print(f"🤖 Username: @{BOT_USERNAME}")
    print(f"📦 DB Channel: {DB_CHANNEL_ID}")
    print(f"👮 Admins: {ADMIN_IDS}")

    # Admin-only command menu
    commands = [BotCommand("start", "Start the bot")]

    for admin_id in ADMIN_IDS:
        await client.set_bot_commands(
            commands=commands,
            scope=BotCommandScopeChat(chat_id=admin_id)
        )

    # Hide commands for non-admins
    await client.set_bot_commands(
        commands=[],
        scope=BotCommandScopeDefault()
    )

# ===================== START COMMAND =====================

@app.on_message(filters.command("start") & filters.private)
async def start_handler(client, message):
    user_id = message.from_user.id

    if not await force_sub_check(client, user_id):
        await message.reply(
            "🔒 You must join the channel to access files.",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Join Channel", url=f"https://t.me/c/{str(FORCE_SUB_CHANNEL)[4:]}")]]
            )
        )
        return

    if len(message.command) == 1:
        await message.reply("👋 Send a file link to access content.")
        return

    if not message.command[1].startswith("file_"):
        return

    msg_id = int(message.command[1].split("_")[1])

    try:
        await client.copy_message(
            chat_id=user_id,
            from_chat_id=DB_CHANNEL_ID,
            message_id=msg_id,
            protect_content=True
        )
    except Exception:
        await message.reply("❌ File not found or removed.")

# ===================== FILE UPLOAD (ADMIN ONLY) =====================

@app.on_message(filters.private & filters.media)
async def upload_handler(client, message):
    if not is_admin(message.from_user.id):
        return

    sent = await message.copy(
        chat_id=DB_CHANNEL_ID,
        protect_content=True
    )

    link = build_share_link(sent.id)

    await message.reply(
        f"✅ File stored successfully\n\n🔗 Shareable link:\n{link}",
        disable_web_page_preview=True
    )

# ===================== ERROR HANDLER =====================

@app.on_error()
async def error_handler(_, error):
    print("❌ Runtime error:")
    traceback.print_exc()

# ===================== RUN =====================

if __name__ == "__main__":
    try:
        app.run()
    except Exception:
        print("🔥 Fatal crash:")
        traceback.print_exc()
        sys.exit(1)
