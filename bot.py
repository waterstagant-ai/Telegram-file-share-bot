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

# -------------------- REQUIRED ENV VARS --------------------
REQUIRED_VARS = {
    "API_ID": int,
    "API_HASH": str,
    "BOT_TOKEN": str,
    "DB_CHANNEL_ID": int,
    "FORCE_SUB_CHANNEL": int,
    "ADMIN_IDS": str,
}

missing = []
parsed = {}

for key, cast in REQUIRED_VARS.items():
    value = os.environ.get(key)
    if not value:
        missing.append(key)
    else:
        try:
            parsed[key] = cast(value) if cast != str else value
        except Exception:
            missing.append(key)

if missing:
    logging.error("❌ FATAL CONFIG ERROR")
    logging.error("Missing or invalid environment variables:")
    for v in missing:
        logging.error(f"  - {v}")
    logging.error("👉 Railway → Variables → Redeploy")
    sys.exit(1)

API_ID = parsed["API_ID"]
API_HASH = parsed["API_HASH"]
BOT_TOKEN = parsed["BOT_TOKEN"]
DB_CHANNEL_ID = parsed["DB_CHANNEL_ID"]
FORCE_SUB_CHANNEL = parsed["FORCE_SUB_CHANNEL"]
ADMIN_IDS = list(map(int, parsed["ADMIN_IDS"].split(",")))

# -------------------- CLIENT --------------------
app = Client(
    name="file_store_bot",
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


# -------------------- START COMMAND --------------------
@app.on_message(filters.private & filters.command("start"))
async def start_handler(client: Client, message: Message):
    user_id = message.from_user.id

    if not await is_subscribed(client, user_id):
        return await message.reply(
            "🔒 **Access Restricted**\n\n"
            "Please join the required channel to use this bot."
        )

    if len(message.command) == 1:
        return await message.reply(
            "👋 **Welcome**\n\n"
            "This is a secure file storage bot.\n"
            "Files can only be accessed via links."
        )

    file_msg_id = message.command[1]

    try:
        file_msg = await client.get_messages(DB_CHANNEL_ID, int(file_msg_id))
        await file_msg.copy(
            chat_id=message.chat.id,
            protect_content=True
        )
    except:
        await message.reply("❌ Invalid or expired file link.")


# -------------------- ADMIN FILE UPLOAD --------------------
@app.on_message(
    filters.private
    & ~filters.command()
    & (filters.document | filters.video | filters.photo | filters.audio)
)
async def admin_upload_handler(client: Client, message: Message):
    if not is_admin(message.from_user.id):
        return

    stored = await message.copy(
        chat_id=DB_CHANNEL_ID,
        protect_content=True
    )

    bot_username = (await client.get_me()).username
    link = f"https://t.me/{bot_username}?start={stored.id}"

    await message.reply(
        "✅ **File Stored Successfully**\n\n"
        f"🔗 **Permanent Link:**\n{link}"
    )


# -------------------- BLOCK NON-ADMIN MESSAGES --------------------
@app.on_message(filters.private)
async def block_everything_else(client: Client, message: Message):
    await message.reply("❌ You are not allowed to perform this action.")


# -------------------- RUN --------------------
if __name__ == "__main__":
    logging.info("🤖 Bot starting...")
    app.run()
