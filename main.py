# Code by @AzRProjects_assistant_bot

import os
import subprocess
import threading
import shlex
from telegram import Update
from telegram.ext import ApplicationBuilder, MessageHandler, filters, CommandHandler, ContextTypes

video_files = {}
srt_files = {}

BOT_TOKEN = '7711552770:AAF0PD8FtjGZo8wYcPMBOcQZxZTXtOw3KqY'

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
        await update.message.reply_text('Subtitles processing shuru ho gaya hai. Thoda time lagega...')

        # Start thread
        threading.Thread(target=process_ffmpeg, args=(update, context)).start()

def process_ffmpeg(update, context):
    chat_id = update.effective_chat.id
    input_video = video_files[chat_id]
    input_srt = srt_files[chat_id]
    output = f'output_{chat_id}.mp4'
    safe_srt = shlex.quote(input_srt)

    cmd = f'ffmpeg -i "{input_video}" -vf subtitles={safe_srt} -preset ultrafast -c:a copy "{output}"'
    subprocess.run(cmd, shell=True)

    context.bot.send_video(chat_id=chat_id, video=open(output, 'rb'), caption='Done! Subtitles added.')

    os.remove(input_video)
    os.remove(input_srt)
    os.remove(output)
    video_files.pop(chat_id)
    srt_files.pop(chat_id)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

if __name__ == '__main__':
    app.run_polling()
    
