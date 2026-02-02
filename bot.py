import os
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

# =====================
# Environment Variables
# =====================
API_ID = int(os.environ.get("API_ID", "12345"))
API_HASH = os.environ.get("API_HASH", "YOUR_API_HASH")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "YOUR_BOT_TOKEN")
FORCE_SUB_CHANNEL = int(os.environ.get("FORCE_SUB_CHANNEL", "-1003738214954"))
ADMIN_IDS = list(map(int, os.environ.get("ADMIN_IDS", "").split()))  # Your Telegram ID(s)

# =====================
# Initialize Bot
# =====================
app = Client(
    "file_storage_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

# =====================
# Command Buttons (type bar)
# =====================
COMMAND_BUTTONS = ReplyKeyboardMarkup(
    [
        [KeyboardButton("/start"), KeyboardButton("/admin"), KeyboardButton("/help")]
    ],
    resize_keyboard=True,
)

# =====================
# Start Command - Force Join
# =====================
@app.on_message(filters.private & filters.command("start"))
async def start(client, message):
    user_id = message.from_user.id
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status in ["member", "creator", "administrator"]:
            await message.reply_text(
                "✅ Welcome! You can now upload your files.",
                reply_markup=COMMAND_BUTTONS
            )
        else:
            raise Exception
    except:
        join_button = InlineKeyboardMarkup(
            [[InlineKeyboardButton("🔒 Join Channel", url="https://t.me/+K7hqRdOzClg1YTg1")]]
        )
        await message.reply_text(
            "🔒 You must join the channel to use this bot.",
            reply_markup=join_button
        )

# =====================
# Admin Command
# =====================
@app.on_message(filters.private & filters.command("admin"))
async def admin_panel(client, message):
    user_id = message.from_user.id
    if user_id in ADMIN_IDS:
        await message.reply_text(
            "🛠 Welcome, Admin!\nYou can manage the bot from here."
        )
    else:
        await message.reply_text(
            "❌ Action not allowed."
        )

# =====================
# Help Command
# =====================
@app.on_message(filters.private & filters.command("help"))
async def help_cmd(client, message):
    await message.reply_text(
        "📌 *Commands Available:*\n"
        "/start - Start bot\n"
        "/admin - Admin panel\n"
        "/help - Show commands\n\n"
        "📂 Upload any file, photo, video, or audio to get a shareable Telegram link.",
        parse_mode="Markdown",
        reply_markup=COMMAND_BUTTONS
    )

# =====================
# File Upload Handler
# =====================
@app.on_message(filters.private & (filters.document | filters.video | filters.photo | filters.audio))
async def handle_file(client, message):
    user_id = message.from_user.id

    # Force join check
    try:
        member = await client.get_chat_member(FORCE_SUB_CHANNEL, user_id)
        if member.status not in ["member", "creator", "administrator"]:
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

    # File accepted, create a shareable Telegram link
    file_id = None
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name
    elif message.video:
        file_id = message.video.file_id
        file_name = message.video.file_name
    elif message.audio:
        file_id = message.audio.file_id
        file_name = message.audio.file_name
    elif message.photo:
        file_id = message.photo.file_id
        file_name = "Photo"

    if file_id:
        shareable_link = f"https://t.me/{(await client.get_me()).username}?start={file_id}"
        await message.reply_text(
            f"✅ File received: {file_name}\n"
            f"🔗 Shareable link: {shareable_link}",
            reply_markup=COMMAND_BUTTONS
        )

# =====================
# Run the Bot
# =====================
print("🤖 Bot started successfully")
app.run()
