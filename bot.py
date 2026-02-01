print("🚀 Bot file loaded")
import os
from pyrogram import Client, filters
from pymongo import MongoClient

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME")

mongo = MongoClient(MONGO_URL)
db = mongo["FileBot"]
files = db["files"]

app = Client(
    "FileBot",
    bot_token=BOT_TOKEN,
    api_id=API_ID,
    api_hash=API_HASH
)

# ─── START COMMAND ─────────────────────────────────

@app.on_message(filters.command("start") & filters.private)
async def start(client, msg):
    user_id = msg.from_user.id

    # Force join channel
    try:
        member = await client.get_chat_member(CHANNEL_ID, user_id)
        if member.status == "left":
            raise
    except:
        return await msg.reply(
            "🔒 You must join our channel to use this bot.\n\n"
            "After joining, come back and press /start"
        )

    # Normal /start
    if len(msg.command) == 1:
        if user_id == ADMIN_ID:
            await msg.reply("👑 Admin mode active.\nSend me a file.")
        else:
            await msg.reply("✅ Access granted.\nSend /start link to get files.")
        return

    # /start FILECODE
    code = msg.command[1]
    file = files.find_one({"code": code})

    if not file:
        return await msg.reply("❌ Invalid or deleted link.")

    await msg.reply_document(
        file["file_id"],
        protect_content=True
    )

# ─── FILE UPLOAD (ADMIN ONLY) ──────────────────────

@app.on_message(filters.document & filters.private)
async def upload(client, msg):
    if msg.from_user.id != ADMIN_ID:
        return await msg.reply("❌ You are not allowed to upload files.")

    code = msg.document.file_unique_id

    files.update_one(
        {"code": code},
        {"$set": {"file_id": msg.document.file_id}},
        upsert=True
    )

    link = f"https://t.me/{BOT_USERNAME}?start={code}"

    await msg.reply(
        "📁 File uploaded successfully!\n\n"
        f"🔗 Permanent Link:\n{link}"
    )

print("Bot is running...")
print("🤖 Bot starting...")
app.run()
