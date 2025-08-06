from keep_alive import keep_alive

keep_alive()
import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler, filters,
    ContextTypes, CallbackQueryHandler
)
import yt_dlp

BOT_TOKEN = os.environ.get("BOT_TOKEN") or "YOUR_BOT_TOKEN"
CHANNEL_USERNAME = "SL_TooL_HuB"  # without @

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

platforms = {
    "yt": "YouTube Shorts 🎬",
    "fb": "Facebook Shorts 📘",
    "tt": "TikTok Shorts 🎵"
}

# ✅ Make downloads folder if missing
if not os.path.exists("downloads"):
    os.makedirs("downloads")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "🚫 Join our channel to use this bot!",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Join", url=f"https://t.me/{CHANNEL_USERNAME}")]]
                )
            )
            return
    except Exception as e:
        logger.error(f"Channel check error: {e}")
        await update.message.reply_text("⚠️ Could not verify channel membership.")
        return

    keyboard = [
        [InlineKeyboardButton(platforms["yt"], callback_data="yt")],
        [InlineKeyboardButton(platforms["fb"], callback_data="fb")],
        [InlineKeyboardButton(platforms["tt"], callback_data="tt")]
    ]
    await update.message.reply_text(
        "🎉 Welcome! Choose a platform to download Shorts video:",
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
    try:
        chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "🚫 Join our channel first!",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Join", url=f"https://t.me/{CHANNEL_USERNAME}")]]
                )
            )
            return
    except:
        await update.message.reply_text("⚠️ Error verifying channel membership.")
        return

    url = update.message.text.strip()
    platform = context.user_data.get("platform")
    if not platform or platform not in platforms:
        await update.message.reply_text("⚠️ Please select a platform first using /start.")
        return

    # Basic link validation
    if platform == "yt" and "youtu" not in url:
        await update.message.reply_text("❌ Please send a valid YouTube Shorts link.")
        return
    if platform == "fb" and "facebook" not in url:
        await update.message.reply_text("❌ Please send a valid Facebook Shorts link.")
        return
    if platform == "tt" and "tiktok" not in url:
        await update.message.reply_text("❌ Please send a valid TikTok Shorts link.")
        return

    await update.message.reply_text("⏳ Downloading... Please wait...")

    try:
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'best[ext=mp4]',
            'quiet': True,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        with open(file_path, 'rb') as f:
            await update.message.reply_video(
                video=f,
                caption="✅ Downloaded successfully!\nThanks for using our bot 💎"
            )
        os.remove(file_path)

    except Exception as e:
        logger.error(f"Error downloading: {e}")
        await update.message.reply_text("❌ Could not download the video. Please try again.")

if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(platform_selected))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    print("Bot running...")
    app.run_polling()
