# ©️ LISA-KOREA | @LISA_FAN_LK | NT_BOT_CHANNEL | LISA-KOREA/YouTube-Video-Download-Bot
# [⚠️ Do not change this repo link ⚠️] :- https://github.com/LISA-KOREA/YouTube-Video-Download-Bot

import os
import logging
import yt_dlp
from pyrofork import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, Message
from Youtube.config import Config
from Youtube.forcesub import handle_force_subscribe

youtube_dl_username = None
youtube_dl_password = None


# 📊 Progress bar helper
async def progress_bar(current, total, message: Message, stage: str):
    percent = int(current * 100 / total)
    bar = "■" * int(percent / 10) + "□" * (10 - int(percent / 10))
    try:
        await message.edit_text(
            f"{stage}...\n\n[{bar}] {percent}%\n\n{current // (1024 * 1024)} MB / {total // (1024 * 1024)} MB"
        )
    except Exception:
        pass


# 🔗 Handle YouTube Link
@Client.on_message(filters.regex(r'^(http(s)?:\/\/)?((w){3}\.)?youtu(\.be|be)?(\.com)?\/.+'))
async def process_youtube_link(client, message):
    if Config.CHANNEL:
        fsub = await handle_force_subscribe(client, message)
        if fsub == 400:
            return

    youtube_link = message.text.strip()

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Best Quality", callback_data=f"download|best|{youtube_link}")],
        [InlineKeyboardButton("1080p", callback_data=f"download|1080p|{youtube_link}")],
        [InlineKeyboardButton("2K", callback_data=f"download|2k|{youtube_link}")],
        [InlineKeyboardButton("4K", callback_data=f"download|4k|{youtube_link}")],
        [InlineKeyboardButton("Medium Quality", callback_data=f"download|medium|{youtube_link}")],
        [InlineKeyboardButton("Low Quality", callback_data=f"download|low|{youtube_link}")]
    ])

    await message.reply_text("📥 **Choose Video Quality**", reply_markup=keyboard)


# 📥 Handle Download Callback
@Client.on_callback_query(filters.regex(r'^download\|'))
async def handle_download_button(client, callback_query):
    quality, youtube_link = callback_query.data.split('|')[1:]

    # 🎥 Quality mapping
    quality_format = {
        'best': 'best',
        '1080p': 'bestvideo[height<=1080]+bestaudio/best[height<=1080]',
        '2k': 'bestvideo[height<=1440]+bestaudio/best[height<=1440]',
        '4k': 'bestvideo[height<=2160]+bestaudio/best[height<=2160]',
        'medium': 'best[height<=480]',
        'low': 'best[height<=360]'
    }.get(quality, 'best')

    status_msg = await callback_query.message.edit_text("⬇️ **Starting download...**")

    try:
        ydl_opts = {
            'format': quality_format,
            'outtmpl': 'downloaded_video_%(id)s.%(ext)s',
            'merge_output_format': 'mp4',
            'cookiefile': 'cookies.txt',
            'progress_hooks': [
                lambda d: asyncio.get_event_loop().create_task(
                    progress_bar(
                        d.get("downloaded_bytes", 0),
                        d.get("total_bytes", 1),
                        status_msg,
                        "⬇️ Downloading"
                    )
                ) if d['status'] == 'downloading' else None
            ]
        }

        if Config.HTTP_PROXY:
            ydl_opts['proxy'] = Config.HTTP_PROXY
        if youtube_dl_username:
            ydl_opts['username'] = youtube_dl_username
        if youtube_dl_password:
            ydl_opts['password'] = youtube_dl_password

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(youtube_link, download=False)
            video_id = info_dict.get('id')
            title = info_dict.get('title')
            duration = info_dict.get("duration", 0)
            thumbnail = info_dict.get("thumbnail")

            if title and video_id:
                # 🔽 Download
                ydl.download([youtube_link])

                video_filename = f"downloaded_video_{video_id}.mp4"
                if os.path.exists(video_filename):
                    await status_msg.edit_text("📤 **Uploading to Telegram...**")

                    await client.send_video(
                        chat_id=callback_query.message.chat.id,
                        video=open(video_filename, 'rb'),
                        caption=f"🎬 {title}",
                        duration=duration,
                        thumb=thumbnail,
                        progress=progress_bar,
                        progress_args=(status_msg, "📤 Uploading")
                    )
                    os.remove(video_filename)

                await status_msg.edit_text("✅ **Uploaded Successfully!**")
            else:
                logging.error("No video streams found.")
                await status_msg.edit_text("❌ Error: No downloadable video found.")

    except yt_dlp.utils.DownloadError as e:
        logging.exception("Error downloading YouTube video: %s", e)
        await status_msg.edit_text("❌ Error: The video is unavailable or restricted.")
    except Exception as e:
        logging.exception("Error processing YouTube link: %s", e)
        await status_msg.edit_text("❌ Error: Failed to process the YouTube link. Please try again later.")
