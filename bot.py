import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes
from flask import Flask, request

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MINIAPP_URL = os.getenv("MINIAPP_URL")
PORT = int(os.environ.get("PORT", 10000))

# Flask app for webhook
flask_app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton(
            text="🎁 অ্যাড দেখে রিওয়ার্ড নাও",
            web_app=WebAppInfo(url=MINIAPP_URL)
        )]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "স্বাগতম!\n\n"
        "নিচের বাটনে ক্লিক করে Mini App ওপেন করো এবং অ্যাড দেখে রিওয়ার্ড নাও।",
        reply_markup=reply_markup
    )

# Telegram Application
application = Application.builder().token(BOT_TOKEN).build()
application.add_handler(CommandHandler("start", start))

@flask_app.route("/")
def home():
    return "Bot is running!"

@flask_app.route("/webhook", methods=["POST"])
async def webhook():
    update = Update.de_json(request.get_json(force=True), application.bot)
    await application.process_update(update)
    return "ok"

def main():
    # Set webhook (Render URL will be used)
    # You need to set WEBHOOK_URL environment variable or it will use polling as fallback
    webhook_url = os.getenv("WEBHOOK_URL")

    if webhook_url:
        print(f"Starting webhook on {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path="webhook",
            webhook_url=f"{webhook_url}/webhook"
        )
    else:
        print("No WEBHOOK_URL found, starting polling...")
        application.run_polling()

if __name__ == "__main__":
    main()
