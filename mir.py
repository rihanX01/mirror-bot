import os
import aiohttp
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters

BOT_TOKEN = os.getenv("BOT_TOKEN")
GOFILE_API = os.getenv("GOFILE_API")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("📤 Send any file and I will generate a FAST mirror link!")

async def upload_stream_to_gofile(file_url, file_name):
    server = requests.get("https://api.gofile.io/servers").json()["data"]["servers"][0]["name"]
    upload_url = f"https://{server}.gofile.io/uploadFile"

    async with aiohttp.ClientSession() as session:
        async with session.get(file_url) as resp:
            stream = resp.content

            data = aiohttp.FormData()
            data.add_field("token", GOFILE_API)
            data.add_field("file", stream, filename=file_name)

            async with session.post(upload_url, data=data) as up:
                result = await up.json()

                return (
                    result["data"]["downloadPage"],
                    result["data"]["directLink"]
                )

async def handle_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = await update.message.reply_text("⏳ Processing...")

    file = update.message.document or update.message.effective_attachment
    file_name = file.file_name
    file_size = round(file.file_size / (1024 * 1024), 2)

    telegram_file = await context.bot.get_file(file.file_id)
    file_url = telegram_file.file_path

    download_page, direct_link = await upload_stream_to_gofile(file_url, file_name)

    keyboard = [
        [
            InlineKeyboardButton("📥 DOWNLOAD", url=direct_link),
            InlineKeyboardButton("▶ STREAM", url=download_page),
        ]
    ]

    markup = InlineKeyboardMarkup(keyboard)

    text = (
        f"🔥 *Mirror Generated!*\n\n"
        f"> *Name:* `{file_name}`\n"
        f"> *Size:* `{file_size} MB`\n\n"
        f"📥 Fast Download\n"
        f"▶ Stream Online\n"
    )

    await msg.edit_text(text, reply_markup=markup, parse_mode="Markdown")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_file))
    app.run_polling()
