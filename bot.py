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

# -------------------- ENV VALIDATION --------------------
REQUIRED = ["API_ID", "API_HASH", "BOT_TOKEN", "DB_CHANNEL_ID", "FORCE_SUB_CHANNEL", "ADMIN_IDS"]
missing = [v for v in REQUIRED if not os.environ.get(v)]

if missing:
    logging.error("❌ Missing environment variables:")
    for v in missing:
        logging.error(f"- {v}")
    sys.exit(1)

API_ID = int(os.environ["API_ID"])
API_HASH = os.environ["API_HASH"]
BOT_TOKEN = os.environ["BOT_TOKEN"]
DB_CHANNEL_ID = int(os.environ["DB_CHANNEL_ID"])
FORCE_SUB_CHANNEL = int(os.environ["FORCE_SUB_CHANNEL"])
ADMIN_IDS = list(map(int, os.environ["ADMIN_IDS"].split(",")))

# -------------------- BOT --------------------
app = Client(
    "file_store_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------------------- HELPERS --------------------
def is_admin(user_id: int) -> bool:
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

# -------------------- /start --------------------
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_subscribed(client, user_id):
        return await message.reply(
            "🔒 **Join the channel to use this bot.**"
        )

    if len(message.command) == 1:
        return await message.reply(
            "📦 **Secure File Store Bot**\n\n"
            "• Files are accessed only via links\n"
            "• Forwarding & saving disabled\n"
            "• Admin-only uploads"
        )

    file_id = message.command[1]

    try:
        msg = await client.get_messages(DB_CHANNEL_ID, int(file_id))
        await msg.copy(
            message.chat.id,
            protect_content=True
        )
    except:
        await message.reply("❌ Invalid or expired link.")

# -------------------- ADMIN UPLOAD --------------------
@app.on_message(
    filters.private
    & (filters.document | filters.video | filters.photo | filters.audio)
)
async def admin_upload(client: Client, message: Message):
    # Ignore commands
    if message.text and message.text.startswith("/"):
        return

    if not is_admin(message.from_user.id):
        return await message.reply("❌ Only admins can upload files.")

    stored = await message.copy(
        DB_CHANNEL_ID,
        protect_content=True
    )

    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start={stored.id}"

    await message.reply(
        "✅ **File Stored Successfully**\n\n"
        f"🔗 **Permanent Link:**\n{link}"
    )

# -------------------- BLOCK EVERYTHING ELSE --------------------
@app.on_message(filters.private)
async def block_all(client: Client, message: Message):
    await message.reply("❌ Action not allowed.")

# -------------------- RUN --------------------
if __name__ == "__main__":
    logging.info("🤖 Bot started successfully")
    app.run()
