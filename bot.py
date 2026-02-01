import logging
from datetime import datetime, timedelta
from pymongo import MongoClient
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

# -------------------- CONFIG --------------------
BOT_TOKEN = "7800121058:AAEr9FUy7wIjgXZSJ0snwfzlUQSJGXFEOIs"
MONGO_URI = "mongodb+srv://Faizalsheikh:arsh2k03@cluster0.ibd5h5x.mongodb.net/Faizalsheikh?retryWrites=true&w=majority"
CHANNEL_ID = -1003510118476
EXPIRY_HOURS = 3
# ------------------------------------------------

# -------------------- LOGGING -------------------
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)
# ------------------------------------------------

# ------------------ MONGO SETUP ----------------
try:
    mongo_client = MongoClient(MONGO_URI)
    db = mongo_client["Faizalsheikh"]
    users_collection = db["users"]
    logger.info("MongoDB connected successfully")
except Exception as e:
    logger.error(f"MongoDB connection error: {e}")
# ------------------------------------------------

# --------------- HELPER FUNCTIONS --------------
def add_or_update_user(user_id):
    """
    Adds a new user or updates expiry if exists
    """
    try:
        expiry_time = datetime.utcnow() + timedelta(hours=EXPIRY_HOURS)
        result = users_collection.update_one(
            {"user_id": user_id},
            {"$set": {"expiry": expiry_time}},
            upsert=True
        )
        if result.upserted_id:
            logger.info(f"New user added with user_id: {user_id}")
        else:
            logger.info(f"Existing user updated with user_id: {user_id}")
    except Exception as e:
        logger.error(f"Error in add_or_update_user: {e}")

async def is_user_in_channel(user_id, context: ContextTypes.DEFAULT_TYPE):
    """
    Checks if user is in the required channel
    """
    try:
        member = await context.bot.get_chat_member(CHANNEL_ID, user_id)
        if member.status in ["member", "administrator", "creator"]:
            return True
        return False
    except Exception as e:
        logger.warning(f"Channel check failed: {e}")
        return False
# ------------------------------------------------

# ---------------- COMMAND HANDLERS --------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    # Force join channel
    in_channel = await is_user_in_channel(user.id, context)
    if not in_channel:
        await update.message.reply_text(
            f"Hi {user.first_name}! You must join our channel to use this bot.\n"
            f"Join here: t.me/YourChannelUsername"
        )
        return

    # Add or update user
    add_or_update_user(user.id)

    await update.message.reply_text(
        f"Welcome {user.first_name}! You now have access for {EXPIRY_HOURS} hours."
    )
# ------------------------------------------------

# ------------------- MAIN -----------------------
def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    # Add command handlers
    app.add_handler(CommandHandler("start", start))

    logger.info("Bot started")
    app.run_polling()

if __name__ == "__main__":
    main()
# ------------------------------------------------
