# Code by @AzRProjects_assistant_bot

import os
import subprocess
import threading
import shlex
import time
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes

BOT_TOKEN = '7711552770:AAF0PD8FtjGZo8wYcPMBOcQZxZTXtOw3KqY'

video_files = {}
srt_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bhej do video aur uska .srt subtitle. Pehle video bhejo.')

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = await update.message.video.get_file()
    path = await file.download_to_drive()
    video_files[update.effective_chat.id] = path
    await update.message.reply_text('Video mil gaya. Ab subtitle file (.srt) bhejo.')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document.file_name.endswith('.srt'):
        return await update.message.reply_text('Sirf .srt files hi bhejo.')

    file = await update.message.document.get_file()
    path = await file.download_to_drive()
    srt_files[update.effective_chat.id] = path

    if update.effective_chat.id in video_files:
        await update.message.reply_text('Subtitles processing shuru ho gaya hai...')

        # Thread start
        threading.Thread(target=process_ffmpeg, args=(update, context)).start()

def get_video_duration(video_path):
    try:
        result = subprocess.run(
            ['ffprobe', '-v', 'error', '-show_entries', 'format=duration',
             '-of', 'default=noprint_wrappers=1:nokey=1', video_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(result.stdout.decode().strip())
        return round(duration)
    except Exception:
        return 0

def estimate_time(duration_sec):
    if duration_sec <= 60:
        return '1 min se kam'
    elif duration_sec <= 300:
        return '2-5 mins'
    elif duration_sec <= 1200:
        return '5-15 mins'
    else:
        return '15+ mins (depending on system load)'

def process_ffmpeg(update, context):
    chat_id = update.effective_chat.id
    input_video = video_files[chat_id]
    input_srt = srt_files[chat_id]
    output = f'output_{chat_id}.mp4'

    duration = get_video_duration(input_video)
    est_time = estimate_time(duration)

    context.bot.send_message(chat_id=chat_id, text=f'Estimated Encode Time: {est_time}')
    context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

    safe_srt = shlex.quote(input_srt)
    cmd = f'ffmpeg -i "{input_video}" -vf subtitles={safe_srt} -preset ultrafast -c:a copy "{output}"'

    log_file = f'log_{chat_id}.txt'
    with open(log_file, 'w') as log:
        subprocess.run(cmd, shell=True, stdout=log, stderr=log)

    # Send video if done
    if os.path.exists(output):
        context.bot.send_video(chat_id=chat_id, video=open(output, 'rb'), caption='Done! Subtitles added.')
    else:
        context.bot.send_message(chat_id=chat_id, text='Encoding fail ho gaya. FFmpeg error aaya.')

    # Cleanup
    for f in [input_video, input_srt, output, log_file]:
        if os.path.exists(f):
            os.remove(f)

    video_files.pop(chat_id, None)
    srt_files.pop(chat_id, None)

# Bot Setup
app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

if __name__ == '__main__':
    app.run_polling()
        
