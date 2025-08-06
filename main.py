from keep_alive import keep_alive

keep_alive()
import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (ApplicationBuilder, CommandHandler, MessageHandler,
                          CallbackQueryHandler, filters, ContextTypes)
from dotenv import load_dotenv
import yt_dlp
import re

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CHANNEL_USERNAME = "human_refer"  # টেলিগ্রাম চ্যানেল ইউজারনেম (ব্যাগ ছাড়া)

user_state = {}  # user_id: 'youtube' / 'tiktok' / 'facebook'


# প্রিমিয়াম মেনু (ভিডিও সোর্স আলাদা বোতাম)
def main_menu():
    keyboard = [
        [InlineKeyboardButton("▶️ YouTube Shorts", callback_data='youtube')],
        [InlineKeyboardButton("▶️ TikTok Shorts", callback_data='tiktok')],
        [InlineKeyboardButton("▶️ Facebook Shorts", callback_data='facebook')],
    ]
    return InlineKeyboardMarkup(keyboard)


# Back button
def back_button():
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton("🔙 Back to Menu", callback_data='back')]])


# চ্যানেলে ইউজার আছে কিনা চেক করার ফাংশন
async def is_user_joined_channel(context: ContextTypes.DEFAULT_TYPE,
                                 user_id: int) -> bool:
    try:
        member = await context.bot.get_chat_member(f"@{CHANNEL_USERNAME}",
                                                   user_id)
        if member.status in ['member', 'creator', 'administrator']:
            return True
        else:
            return False
    except Exception as e:
        print(f"Error checking channel membership: {e}")
        return False


# URL validation function platform-wise
def validate_url(url: str, platform: str) -> bool:
    url = url.lower()
    if platform == 'youtube':
        # ইউটিউব ডোমেইন চেক (youtube.com or youtu.be)
        return bool(
            re.search(r'(https?://)?(www\.)?(youtube\.com|youtu\.be)/', url))
    elif platform == 'tiktok':
        # টিকটক ডোমেইন চেক
        return bool(re.search(r'(https?://)?(www\.)?tiktok\.com/', url))
    elif platform == 'facebook':
        # ফেসবুক ডোমেইন চেক
        return bool(re.search(r'(https?://)?(www\.)?facebook\.com/', url))
    else:
        return False


# /start কমান্ড হ্যান্ডলার
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    joined = await is_user_joined_channel(context, user_id)
    if not joined:
        await update.message.reply_text(
            f"❗️ প্রথমে আমাদের চ্যানেল [@{CHANNEL_USERNAME}](https://t.me/{CHANNEL_USERNAME}) এ জয়েন করুন।\n"
            "যোগদানের পর /start আবার চালান।",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        return

    welcome_text = (
        "✨ *Welcome to Premium Shorts Downloader Bot!*\n\n"
        "🔻 নিচের বাটন থেকে Shorts এর সোর্স সিলেক্ট করুন:\n\n"
        "▶️ YouTube Shorts\n▶️ TikTok Shorts\n▶️ Facebook Shorts\n\n"
        "🔒 বটটি শুধুমাত্র তখনই কাজ করবে যখন আপনি আমাদের চ্যানেলে জয়েন থাকবেন।")
    await update.message.reply_text(welcome_text,
                                    reply_markup=main_menu(),
                                    parse_mode="Markdown")


# বাটন হ্যান্ডলার
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    user_id = query.from_user.id

    joined = await is_user_joined_channel(context, user_id)
    if not joined:
        await query.answer()
        await query.edit_message_text(
            f"❗️ আপনি আমাদের চ্যানেল [@{CHANNEL_USERNAME}](https://t.me/{CHANNEL_USERNAME}) থেকে বেরিয়ে গেছেন বা জয়েন করেননি।\n"
            "অতএব, বট ব্যবহার করার অনুমতি নেই।\n"
            "অনুগ্রহ করে আবার জয়েন করুন।",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        return

    await query.answer()

    if query.data in ['youtube', 'tiktok', 'facebook']:
        user_state[user_id] = query.data
        await query.edit_message_text(
            f"📽️ *Send the {query.data.capitalize()} Shorts video link now.*\n\n"
            "উদাহরণ: https://www.example.com/your-shorts-link",
            parse_mode="Markdown",
            reply_markup=back_button())
    elif query.data == 'back':
        user_state.pop(user_id, None)
        await query.edit_message_text(
            "🔙 *Back to main menu.*\n\nনিচের অপশন থেকে সিলেক্ট করুন:",
            parse_mode="Markdown",
            reply_markup=main_menu())


# ভিডিও ডাউনলোড ফাংশন (yt-dlp)
def download_video(url: str):
    ydl_opts = {
        'format': 'best',
        'outtmpl': 'video.%(ext)s',
        'quiet': True,
        'nocheckcertificate': True,
        'ignoreerrors': True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info = ydl.extract_info(url, download=True)
        filename = ydl.prepare_filename(info)
        return filename, info


# ইউজার মেসেজ হ্যান্ডলিং (ভিডিও লিংক প্রোসেস)
async def handle_link(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()
    choice = user_state.get(user_id)

    joined = await is_user_joined_channel(context, user_id)
    if not joined:
        await update.message.reply_text(
            f"❗️ আপনি আমাদের চ্যানেল [@{CHANNEL_USERNAME}](https://t.me/{CHANNEL_USERNAME}) থেকে বেরিয়ে গেছেন বা জয়েন করেননি।\n"
            "অতএব, বট ব্যবহার করতে পারবেন না।\n"
            "অনুগ্রহ করে আবার জয়েন করুন।",
            parse_mode="Markdown",
            disable_web_page_preview=True,
        )
        return

    if choice not in ['youtube', 'tiktok', 'facebook']:
        await update.message.reply_text(
            "❗ প্রথমে নিচের মেনু থেকে Shorts এর সোর্স সিলেক্ট করুন।",
            reply_markup=main_menu(),
            parse_mode="Markdown")
        return

    # Validate URL based on selected platform
    if not validate_url(text, choice):
        await update.message.reply_text(
            f"⚠️ দয়া করে *শুধুমাত্র {choice.capitalize()} Shorts এর সঠিক URL পাঠান।*",
            parse_mode="Markdown")
        return

    await update.message.reply_text("⏳ *Downloading Shorts, please wait...*",
                                    parse_mode="Markdown")

    try:
        filepath, info = download_video(text)
        max_size = 50 * 1024 * 1024  # 50MB Telegram limit

        if not filepath or not os.path.exists(filepath):
            raise Exception("Downloaded file not found.")

        file_size = os.path.getsize(filepath)
        if file_size > max_size:
            # বড় ভিডিও হলে ডাউনলোড লিংক পাঠাও
            await update.message.reply_text(
                f"⚠️ Shorts ভিডিওটি বড় (>{max_size//1024//1024}MB)। Telegram-এ সরাসরি পাঠানো সম্ভব নয়।\n"
                f"আপনি ভিডিওটি নিচের লিংক থেকে ডাউনলোড করতে পারেন:\n\n{info.get('webpage_url')}",
                parse_mode="Markdown")
            os.remove(filepath)
            return

        await update.message.reply_video(video=open(filepath, 'rb'),
                                         caption=info.get(
                                             'title', 'Shorts Video'))
        os.remove(filepath)

    except Exception as e:
        print(f"Download error: {e}")
        await update.message.reply_text(
            "❌ *Download failed!*\n"
            "সম্ভবত লিংকটি সঠিক নয় অথবা Shorts ভিডিও ডাউনলোডে সমস্যা হয়েছে। আবার চেষ্টা করুন।",
            parse_mode="Markdown")

    # শেষে মেনু দেখাও এবং ইউজারের স্টেট ক্লিয়ার করো
    await update.message.reply_text(
        "🎬 *আরো Shorts ডাউনলোড করতে নিচের মেনু থেকে সোর্স বেছে নিন:*",
        reply_markup=main_menu(),
        parse_mode="Markdown")
    user_state.pop(user_id, None)


if __name__ == '__main__':
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(
        MessageHandler(filters.TEXT & ~filters.COMMAND, handle_link))

    print("🚀 Bot is running...")
    app.run_polling()