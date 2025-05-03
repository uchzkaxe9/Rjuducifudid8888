# Code by @AzRProjects_assistant_bot

import os
import subprocess
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
    await update.message.reply_text('Video mil gaya. Ab subtitle file bhejo (.srt).')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.document.file_name.endswith('.srt'):
        return await update.message.reply_text('Sirf .srt files hi bhejo.')

    file = await update.message.document.get_file()
    path = await file.download_to_drive()
    srt_files[update.effective_chat.id] = path

    if update.effective_chat.id in video_files:
        await update.message.reply_text('Subtitles add ho rahe hain...')

        input_video = video_files[update.effective_chat.id]
        input_srt = srt_files[update.effective_chat.id]
        output = f'output_{update.effective_chat.id}.mp4'

        cmd = [
            'ffmpeg', '-i', input_video,
            '-vf', f"subtitles={input_srt}",
            '-c:a', 'copy', output
        ]
        subprocess.run(cmd)

        await update.message.reply_video(video=open(output, 'rb'), caption='Done! Subtitles added.')

        os.remove(input_video)
        os.remove(input_srt)
        os.remove(output)
        video_files.pop(update.effective_chat.id)
        srt_files.pop(update.effective_chat.id)

app = ApplicationBuilder().token(BOT_TOKEN).build()
app.add_handler(CommandHandler('start', start))
app.add_handler(MessageHandler(filters.VIDEO, handle_video))
app.add_handler(MessageHandler(filters.Document.ALL, handle_document))

if __name__ == '__main__':
    app.run_polling()
  
