import os
import uuid
from telegram import Update
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ContextTypes,
)
from pymongo import MongoClient

# ====== CONFIG ======
BOT_TOKEN = os.getenv("BOT_TOKEN")
MONGO_URL = os.getenv("MONGO_URL")

CHANNEL_LINK = "https://t.me/+CLfnma8b2jM0YWQ1"   # your channel invite
CHANNEL_ID = -1003510118476                     # your channel ID
BASE_LINK = "https://t.me/SpicyParlourCool_bot?start="  # change bot username

# ====================

mongo = MongoClient(MONGO_URL)
db = mongo["filebot"]
files_col = db["files"]


async def is_joined(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        member = await context.bot.get_chat_member(
            CHANNEL_ID, update.effective_user.id
        )
        return member.status in ["member", "administrator", "creator"]
    except:
        return False


async def force_join(update: Update):
    await update.message.reply_text(
        "🚫 **You must join our channel to access files**\n\n"
        f"👉 Join here: {CHANNEL_LINK}\n\n"
        "After joining, **open the file link again**.",
        disable_web_page_preview=True
    )


async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not await is_joined(update, context):
        await force_join(update)
        return

    msg = update.message
    file_id = (
        msg.document.file_id if msg.document else
        msg.video.file_id if msg.video else
        msg.audio.file_id if msg.audio else
        msg.photo[-1].file_id
    )

    unique_id = str(uuid.uuid4())[:8]

    files_col.insert_one({
        "_id": unique_id,
        "file_id": file_id
    })

    link = BASE_LINK + unique_id

    await msg.reply_text(
        "✅ **File stored successfully!**\n\n"
        "🔗 **Permanent Link:**\n"
        f"{link}\n\n"
        "⚠️ File cannot be downloaded inside bot.",
        disable_web_page_preview=True
    )


async def start_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        return

    if not await is_joined(update, context):
        await force_join(update)
        return

    file_code = context.args[0]
    data = files_col.find_one({"_id": file_code})

    if not data:
        await update.message.reply_text("❌ File not found.")
        return

    await context.bot.send_document(
        chat_id=update.effective_user.id,
        document=data["file_id"]
    )


def main():
    app = Application.builder().token(BOT_TOKEN).build()

    app.add_handler(MessageHandler(filters.Document.ALL, handle_files))
    app.add_handler(MessageHandler(filters.Video.ALL, handle_files))
    app.add_handler(MessageHandler(filters.Audio.ALL, handle_files))
    app.add_handler(MessageHandler(filters.Photo.ALL, handle_files))

    app.add_handler(MessageHandler(filters.Regex("^/start "), start_link))

    print("🤖 Bot is running...")
    app.run_polling()


if __name__ == "__main__":
    main()
