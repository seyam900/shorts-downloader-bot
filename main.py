import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)
import yt_dlp
import requests

BOT_TOKEN = "YOUR_BOT_TOKEN_HERE"
CHANNEL_USERNAME = "SL_TooL_HuB"  # Without @

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

platforms = {
    "yt": "YouTube Shorts 🎬",
    "fb": "Facebook Shorts 📘",
    "tt": "TikTok Shorts 🎵"
}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
    if chat_member.status not in ["member", "administrator", "creator"]:
        await update.message.reply_text(
            "🚫 To use this bot, please join our channel first!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]])
        )
        return

    keyboard = [
        [InlineKeyboardButton(platforms["yt"], callback_data="yt")],
        [InlineKeyboardButton(platforms["fb"], callback_data="fb")],
        [InlineKeyboardButton(platforms["tt"], callback_data="tt")]
    ]
    await update.message.reply_text(
        "🎉 Welcome! Select a platform to download Shorts video:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data
    context.user_data["platform"] = platform
    await query.message.reply_text(f"✅ Now send the {platforms[platform]} link:")

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
    if chat_member.status not in ["member", "administrator", "creator"]:
        await update.message.reply_text(
            "🚫 Please join our channel to use this bot!",
            reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]])
        )
        return

    url = update.message.text.strip()
    platform = context.user_data.get("platform")
    if not platform or platform not in ["yt", "fb", "tt"]:
        await update.message.reply_text("⚠️ Please select a platform first by sending /start")
        return

    if platform == "yt" and "youtu" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube Shorts link.")
        return
    if platform == "fb" and "facebook" not in url:
        await update.message.reply_text("❌ Please send a valid Facebook Shorts link.")
        return
    if platform == "tt" and "tiktok" not in url:
        await update.message.reply_text("❌ Please send a valid TikTok Shorts link.")
        return

    await update.message.reply_text("⏳ Downloading your video... Please wait!")

    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'best[ext=mp4]',
            'quiet': True
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)
            with open(file_path, 'rb') as video:
                await update.message.reply_video(video=video, caption="✅ Video downloaded successfully!\nThanks for using our premium bot 💎")
            os.remove(file_path)
    except Exception as e:
        logger.error(f"Download failed: {e}")
        await update.message.reply_text("❌ Failed to download video. Please check the link and try again.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(platform_selected))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))
    print("Bot is running...")
    app.run_polling()
