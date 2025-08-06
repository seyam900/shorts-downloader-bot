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

def main_menu():
    keyboard = [
        [InlineKeyboardButton(platforms["yt"], callback_data="yt")],
        [InlineKeyboardButton(platforms["fb"], callback_data="fb")],
        [InlineKeyboardButton(platforms["tt"], callback_data="tt")]
    ]
    return InlineKeyboardMarkup(keyboard)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "🚫 *Oops! You need to join our premium channel first!*\n\n"
                f"👉 [Join @{CHANNEL_USERNAME}](https://t.me/{CHANNEL_USERNAME})\n\n"
                "Then come back here and send /start again.",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]]
                )
            )
            return
    except Exception as e:
        logger.error(f"Channel check error: {e}")
        await update.message.reply_text("⚠️ Sorry, couldn’t verify your membership. Please try again later.")
        return

    welcome_text = (
        "🌟 *Welcome to* *Shorts Downloader Premium!* 🌟\n\n"
        "🎉 Download your favorite Shorts videos instantly from:\n\n"
        "▶️ YouTube Shorts\n▶️ TikTok Shorts\n▶️ Facebook Shorts\n\n"
        "✨ Just select a platform below and send your Shorts link.\n"
        "🔒 *Exclusive for @SL_TooL_HuB channel members only.*"
    )
    await update.message.reply_text(
        welcome_text,
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


async def platform_selected(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    platform = query.data
    context.user_data["platform"] = platform
    await query.message.reply_text(
        f"📥 *Send me the link of your {platforms[platform]} video now!*",
        parse_mode="Markdown"
    )


async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    try:
        chat_member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}", user.id)
        if chat_member.status not in ["member", "administrator", "creator"]:
            await update.message.reply_text(
                "🚫 *You left the channel or not joined yet.*\n"
                f"👉 Please join [@{CHANNEL_USERNAME}](https://t.me/{CHANNEL_USERNAME}) first!",
                parse_mode="Markdown",
                reply_markup=InlineKeyboardMarkup(
                    [[InlineKeyboardButton("🔗 Join Channel", url=f"https://t.me/{CHANNEL_USERNAME}")]]
                )
            )
            return
    except Exception as e:
        logger.error(f"Channel check error: {e}")
        await update.message.reply_text("⚠️ Couldn't verify your membership. Try again later.")
        return

    url = update.message.text.strip()
    platform = context.user_data.get("platform")
    if not platform or platform not in platforms:
        await update.message.reply_text(
            "⚠️ Please select a platform first using /start and choose from menu."
        )
        return

    # Basic validation
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
        # Create downloads folder if needed
        if not os.path.exists("downloads"):
            os.makedirs("downloads")

        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'format': 'best[ext=mp4]',
            'quiet': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_path = ydl.prepare_filename(info)

        with open(file_path, 'rb') as video:
            await update.message.reply_video(
                video=video,
                caption=f"✅ *Downloaded:* {info.get('title', 'Shorts Video')}\n\n"
                        "Thank you for using our premium bot! 💎"
                ,parse_mode="Markdown"
            )
        os.remove(file_path)

        # Show menu again for next download
        await update.message.reply_text(
            "🔄 *Want to download another Shorts?* Choose platform below:",
            parse_mode="Markdown",
            reply_markup=main_menu()
        )
        context.user_data.pop("platform", None)

    except Exception as e:
        logger.error(f"Error downloading: {e}")
        await update.message.reply_text(
            "❌ Failed to download video. Please check your link and try again."
        )


if __name__ == "__main__":
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(platform_selected))
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), download_video))

    print("🤖 Bot is running...")
    app.run_polling()

