import os
from dotenv import load_dotenv
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MINIAPP_URL = os.getenv("MINIAPP_URL")
PORT = int(os.environ.get("PORT", 10000))

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

def main():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    print("Bot is starting with webhook...")

    # Render automatically provides the service URL via RENDER_EXTERNAL_URL
    webhook_url = os.getenv("RENDER_EXTERNAL_URL")

    if webhook_url:
        print(f"Using webhook: {webhook_url}")
        application.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            url_path=BOT_TOKEN,          # secret path
            webhook_url=f"{webhook_url}/{BOT_TOKEN}"
        )
    else:
        print("No RENDER_EXTERNAL_URL found. Running polling (local only)...")
        application.run_polling()

if __name__ == "__main__":
    main()
