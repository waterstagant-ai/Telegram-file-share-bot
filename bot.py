import os
import logging
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

# -------------------------------
# Logging
# -------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# -------------------------------
# Environment Variables
# -------------------------------
API_ID = int(os.environ.get("API_ID"))
API_HASH = os.environ.get("API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN")

# Force join channel
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "-1003738214954"))

# Admin IDs (comma-separated)
ADMIN_IDS = [int(x) for x in os.environ.get("ADMIN_IDS", "").split() if x]

# Database channel for storing file IDs (if needed)
DB_CHANNEL_ID = int(os.environ.get("DB_CHANNEL_ID", "-1003738214954"))

# -------------------------------
# Initialize Bot
# -------------------------------
app = Client(
    "spicy_parlour_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN
)

# -------------------------------
# Start Command - Force Join
# -------------------------------
@app.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    try:
        # Check if user is in channel
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status != "kicked":
            await message.reply_text(
                "✅ You are already joined! You can now upload files."
            )
        else:
            raise Exception
    except:
        # User not in channel
        join_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔒 Join Channel", url="https://t.me/+K7hqRdOzClg1YTg1")]]
        )
        await message.reply_text(
            "🔒 Join the channel to use this bot.",
            reply_markup=join_button
        )

# -------------------------------
# Admin Command Example
# -------------------------------
@app.on_message(filters.private & filters.command("admin"))
async def admin_command(client, message):
    user_id = message.from_user.id
    if user_id not in ADMIN_IDS:
        await message.reply_text("❌ Action not allowed.")
        return
    await message.reply_text("✅ You are an admin!")

# -------------------------------
# File Upload Handler
# -------------------------------
@app.on_message(filters.private & (filters.document | filters.video | filters.photo | filters.audio))
async def handle_file(client, message):
    user_id = message.from_user.id
    # Force join check
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status == "kicked":
            raise Exception
    except:
        join_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔒 Join Channel", url="https://t.me/+K7hqRdOzClg1YTg1")]]
        )
        await message.reply_text(
            "🔒 You must join the channel to use the bot.",
            reply_markup=join_button
        )
        return

    # Forward file to DB channel
    sent_msg = await message.forward(chat_id=DB_CHANNEL_ID)

    # Generate shareable link
    file_id = sent_msg.message_id
    link = f"https://t.me/c/{str(DB_CHANNEL_ID)[4:]}/{file_id}"
    await message.reply_text(f"✅ File stored! Here is your shareable link:\n{link}")

# -------------------------------
# Run Bot
# -------------------------------
if __name__ == "__main__":
    logging.info("🤖 Bot started successfully")
    app.run()
