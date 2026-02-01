import os
import uuid
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient

print("🚀 Bot file loaded")

# ─── ENV VARIABLES ────────────────────────────────

BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MONGO_URL = os.getenv("MONGO_URL")
CHANNEL_ID = int(os.getenv("CHANNEL_ID"))
ADMIN_ID = int(os.getenv("ADMIN_ID"))
BOT_USERNAME = os.getenv("BOT_USERNAME").replace("@", "")

CHANNEL_INVITE_LINK = "https://t.me/+CLfnma8b2jM0YWQ1"

# ─── DATABASE ─────────────────────────────────────

mongo = MongoClient(MONGO_URL)
db = mongo["FileBot"]
files = db["files"]

# ─── BOT ──────────────────────────────────────────

app = Client(
    "FileBot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

pending_files = {}

# ─── START COMMAND ────────────────────────────────

@app.on_message(filters.command("start") & filters.private)
async def start(client, msg):
    user_id = msg.from_user.id
    file_code = msg.command[1] if len(msg.command) > 1 else None

    # ADMIN BYPASS
    if user_id == ADMIN_ID and not file_code:
        return await msg.reply("👑 Admin mode active.\nSend me a file.")

    if file_code:
        pending_files[user_id] = file_code

    # FORCE JOIN CHECK
    try:
        member = await client.get_chat_member(CHANNEL_ID, user_id)
        if member.status == "left":
            raise
    except:
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔔 Join Channel", url=CHANNEL_INVITE_LINK)],
            [InlineKeyboardButton("✅ I Joined", callback_data="check_join")]
        ])
        return await msg.reply(
            "🔒 You must join our channel to access this file.\n\n"
            "Join first, then tap **I Joined**.",
            reply_markup=buttons
        )

    # SEND FILE DIRECTLY IF ALREADY JOINED
    if file_code:
        file = files.find_one({"code": file_code})
        if not file:
            return await msg.reply("❌ Invalid or deleted link.")

        return await msg.reply_document(
            file["file_id"],
            protect_content=True
        )

    await msg.reply("✅ Access granted.")

# ─── JOIN CHECK CALLBACK ──────────────────────────

@app.on_callback_query(filters.regex("^check_join$"))
async def check_join_callback(client, callback):
    user_id = callback.from_user.id

    try:
        member = await client.get_chat_member(CHANNEL_ID, user_id)
        if member.status == "left":
            raise
    except:
        return await callback.answer(
            "❌ You haven't joined yet!",
            show_alert=True
        )

    code = pending_files.pop(user_id, None)

    if not code:
        return await callback.message.edit_text(
            "✅ Membership verified.\nNo pending file."
        )

    file = files.find_one({"code": code})
    if not file:
        return await callback.message.edit_text(
            "❌ File not found or deleted."
        )

    await callback.message.delete()
    await callback.message.reply_document(
        file["file_id"],
        protect_content=True
    )

# ─── ADMIN FILE UPLOAD ────────────────────────────

@app.on_message(filters.document & filters.private)
async def upload(client, msg):
    if msg.from_user.id != ADMIN_ID:
        return await msg.reply("❌ Only admin can upload files.")

    code = uuid.uuid4().hex[:10]

    files.insert_one({
        "code": code,
        "file_id": msg.document.file_id
    })

    link = f"https://t.me/{BOT_USERNAME}?start={code}"

    await msg.reply(
        "📁 File uploaded successfully!\n\n"
        f"🔗 Permanent Link:\n{link}"
    )

print("🤖 Bot starting...")
app.run()
