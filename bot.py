import os
import sys
import logging
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.enums import ChatMemberStatus

# -------------------- LOGGING --------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------- ENV VARIABLES --------------------
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
    logging.error("❌ FATAL CONFIG ERROR")
    logging.error("Missing environment variables:")
    for v in missing:
        logging.error(f"  - {v}")
    logging.error("👉 Fix this in Railway → Variables → Redeploy")
    sys.exit(1)

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]

DB_CHANNEL_ID = int(os.environ["DB_CHANNEL_ID"])          # Private channel
FORCE_SUB_CHANNEL = int(os.environ["FORCE_SUB_CHANNEL"])  # Public/Private channel
ADMIN_IDS = list(map(int, os.environ["ADMIN_IDS"].split()))

# -------------------- BOT CLIENT --------------------
app = Client(
    name="file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------------------- HELPERS --------------------
async def is_admin(user_id: int) -> bool:
    return user_id in ADMIN_IDS


async def is_subscribed(client: Client, user_id: int) -> bool:
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        return member.status in (
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.ADMINISTRATOR,
            ChatMemberStatus.OWNER,
        )
    except:
        return False


# -------------------- START --------------------
@app.on_message(filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_subscribed(client, user_id):
        return await message.reply(
            "🔒 **Access Restricted**\n\n"
            "You must join our channel to use this bot."
        )

    if len(message.command) == 1:
        await message.reply(
            "👋 **Welcome**\n\n"
            "This is a secure file store bot.\n"
            "You can only access files via special links."
        )
        return

    # /start <file_id>
    file_id = message.command[1]

    try:
        msg = await client.get_messages(DB_CHANNEL_ID, int(file_id))
        await msg.copy(
            chat_id=message.chat.id,
            protect_content=True
        )
    except:
        await message.reply("❌ Invalid or expired link.")


# -------------------- ADMIN FILE UPLOAD --------------------
@app.on_message(filters.private & ~filters.command & (filters.document | filters.video | filters.photo | filters.audio))
async def admin_upload(client: Client, message: Message):
    if not await is_admin(message.from_user.id):
        return

    stored = await message.copy(
        chat_id=DB_CHANNEL_ID,
        protect_content=True
    )

    link = f"https://t.me/{client.me.username}?start={stored.id}"

    await message.reply(
        f"✅ **File Stored Successfully**\n\n"
        f"🔗 **Permanent Link:**\n{link}"
    )


# -------------------- BLOCK EVERYTHING ELSE --------------------
@app.on_message(filters.private)
async def block_others(client: Client, message: Message):
    await message.reply("❌ You are not allowed to do this.")


# -------------------- RUN --------------------
if __name__ == "__main__":
    logging.info("🤖 Starting bot...")
    app.run()
