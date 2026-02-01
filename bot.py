import os
import logging
from datetime import datetime, timedelta
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)
from pymongo import MongoClient

# -------- CONFIG --------
BOT_TOKEN = "YOUR_BOT_TOKEN"
MONGO_URL = "YOUR_MONGO_URL"
ADMIN_ID = 123456789  # <-- your Telegram ID
CHANNEL_ID = "@YourChannelUsername"
USER_TIMER_HOURS = 3

# -------- LOGGING --------
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)

# -------- DATABASE --------
client = MongoClient(MONGO_URL)
db = client["telegram_bot"]
users_collection = db["users"]

# -------- HELPERS --------
def is_user_allowed(user_id):
    """Check if user is within allowed time limit."""
    if user_id == ADMIN_ID:
        return True
    user = users_collection.find_one({"user_id": user_id})
    if not user:
        return False
    if datetime.utcnow() < user["expiry"]:
        return True
    return False

def add_or_update_user(user_id):
    """Add new user or refresh expiry."""
    expiry_time = datetime.utcnow() + timedelta(hours=USER_TIMER_HOURS)
    users_collection.update_one(
        {"user_id": user_id},
        {"$set": {"expiry": expiry_time}},
        upsert=True
    )

async def check_channel_membership(update: Update, user_id, context: ContextTypes.DEFAULT_TYPE):
    """Force user to join channel before using bot."""
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
    except:
        pass
    await update.message.reply_text(
        f"⚠️ You must join the channel {CHANNEL_ID} to use this bot."
    )
    return False

# -------- HANDLERS --------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_channel_membership(update, user.id, context):
        return
    add_or_update_user(user.id)
    await update.message.reply_text("Welcome! Send me a file to get a permanent shareable link.")

async def start_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await start(update, context)

async def handle_files(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not await check_channel_membership(update, user.id, context):
        return
    if not is_user_allowed(user.id):
        await update.message.reply_text("⏳ Your 3-hour access has expired. Send /start again to refresh.")
        return

    file = None
    file_type = None

    if update.message.document:
        file = update.message.document
        file_type = "Document"
    elif update.message.video:
        file = update.message.video
        file_type = "Video"
    elif update.message.audio:
        file = update.message.audio
        file_type = "Audio"
    elif update.message.photo:
        file = update.message.photo[-1]  # highest resolution
        file_type = "Photo"

    if file:
        file_link = await file.get_file()
        await update.message.reply_text(f"✅ {file_type} link:\n{file_link.file_path}")
    else:
        await update.message.reply_text("❌ Unsupported file type.")

# -------- MAIN --------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Command handlers
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Regex(r"^/start "), start_link))

    # File handlers
    app.add_handler(MessageHandler(filters.DOCUMENT, handle_files))
    app.add_handler(MessageHandler(filters.VIDEO, handle_files))
    app.add_handler(MessageHandler(filters.AUDIO, handle_files))
    app.add_handler(MessageHandler(filters.PHOTO, handle_files))

    print("🤖 Bot is running...")
    app.run_polling()

# -------- RUN --------
if __name__ == "__main__":
    main()
