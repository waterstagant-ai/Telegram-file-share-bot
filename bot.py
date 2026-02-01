import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from pymongo import MongoClient

# ---------------- CONFIG ---------------- #
BOT_TOKEN = "7800121058:AAEr9FUy7wIjgXZSJ0snwfzlUQSJGXFEOIs"
MONGO_URL = "mongodb+srv://Faizalsheikh:Faizalsheikh@cluster0.ibd5h5x.mongodb.net/Faizalsheikh?retryWrites=true&w=majority"
ADMIN_IDS = [7450686441]  # Add your Telegram user ID(s)
CHANNEL_ID = -1003510118476  # Your channel ID
# ---------------------------------------- #

# Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# MongoDB
client = MongoClient(MONGO_URL)
db = client.get_database()
users_col = db["users"]
files_col = db["files"]
logger.info("MongoDB connected successfully")

# ---------------- HELPERS ---------------- #
async def check_channel_member(user_id):
    """Check if user has joined the required channel."""
    try:
        member = await application.bot.get_chat_member(CHANNEL_ID, user_id)
        return member.status != 'left'
    except Exception as e:
        logger.error(f"Error checking channel member: {e}")
        return False

def add_or_update_user(user_id):
    """Add new user or update existing in DB."""
    if users_col.find_one({"user_id": user_id}):
        users_col.update_one({"user_id": user_id}, {"$set": {"user_id": user_id}})
        logger.info(f"Existing user updated with user_id: {user_id}")
    else:
        users_col.insert_one({"user_id": user_id})
        logger.info(f"New user added with user_id: {user_id}")

def generate_shareable_link(file_id):
    """Generate permanent shareable link for a file."""
    # In real scenario, you can integrate a file hosting URL here
    return f"https://t.me/your_channel/{file_id}"

# ---------------- COMMAND HANDLERS ---------------- #
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_or_update_user(user_id)

    if user_id not in ADMIN_IDS and not await check_channel_member(user_id):
        await update.message.reply_text(
            f"❌ You must join the channel first: @SpicyParlour"
        )
        return

    await update.message.reply_text(
        "✅ Welcome! Send me any file, and I will give you a permanent shareable link."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "/start - Start the bot\n"
        "/help - Show this help message\n"
        "Send a file to get a permanent shareable link."
    )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in ADMIN_IDS and not await check_channel_member(user_id):
        await update.message.reply_text(
            f"❌ You must join the channel first: @SpicyParlour"
        )
        return

    file = update.message.document or update.message.video or update.message.audio or update.message.photo[-1]
    file_id = file.file_id
    shareable_link = generate_shareable_link(file_id)

    # Store file info in DB
    files_col.insert_one({
        "user_id": user_id,
        "file_id": file_id,
        "file_name": getattr(file, 'file_name', 'photo_or_media')
    })

    await update.message.reply_text(
        f"✅ Your file link:\n{shareable_link}",
        disable_web_page_preview=True
    )

# ---------------- MAIN ---------------- #
application = ApplicationBuilder().token(BOT_TOKEN).build()

# Handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(CommandHandler("help", help_command))
application.add_handler(MessageHandler(filters.Document.ALL | filters.PHOTO | filters.VIDEO | filters.AUDIO, handle_file))

# Run the bot
logger.info("Bot started")
application.run_polling()
