# main.py
# Hardsub Encode Bot by AzR Projects

import os
import ffmpeg
import time
import shlex
import asyncio
from pathlib import Path
from telegram import Update, ChatAction
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.environ.get('7711552770:AAF0PD8FtjGZo8wYcPMBOcQZxZTXtOw3KqY')
video_files = {}
srt_files = {}

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Bhej do video aur uska .srt subtitle. Pehle video bhejo.')

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    file = update.message.document
    chat_id = update.message.chat_id
    file_path = f'downloads/{chat_id}_{file.file_name}'
    os.makedirs('downloads', exist_ok=True)
    new_file = await context.bot.get_file(file.file_id)
    await new_file.download_to_drive(file_path)

    if file.file_name.endswith('.mp4'):
        video_files[chat_id] = Path(file_path)
        await update.message.reply_text('Video mil gaya. Ab .srt subtitle bhejo.')
    elif file.file_name.endswith('.srt'):
        srt_files[chat_id] = Path(file_path)
        await update.message.reply_text('Subtitle mil gaya. Encode shuru ho raha hai...')
        await encode_video(update, context, chat_id)
    else:
        await update.message.reply_text('Sirf .mp4 ya .srt files bhejo.')

def get_estimated_time(video_path):
    try:
        probe = ffmpeg.probe(str(video_path))
        duration = float(probe['format']['duration'])
        return round(duration / 2, 2)  # Rough estimate: half of video length in seconds
    except:
        return 30

async def encode_video(update: Update, context: ContextTypes.DEFAULT_TYPE, chat_id):
    input_video = video_files.get(chat_id)
    input_srt = srt_files.get(chat_id)

    if not input_video or not input_srt:
        await context.bot.send_message(chat_id=chat_id, text='Video ya subtitle missing hai.')
        return

    output_path = f'output/{chat_id}_hardsub.mp4'
    os.makedirs('output', exist_ok=True)

    est_time = get_estimated_time(input_video)
    await context.bot.send_message(chat_id=chat_id, text=f'Estimated Encode Time: {est_time} sec')
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.UPLOAD_VIDEO)

    def process_ffmpeg():
        safe_video = shlex.quote(str(input_video))
        safe_srt = shlex.quote(str(input_srt))
        safe_output = shlex.quote(output_path)

        cmd = f'ffmpeg -i {safe_video} -vf subtitles={safe_srt} -c:a copy {safe_output}'
        os.system(cmd)

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, process_ffmpeg)

    await context.bot.send_video(chat_id=chat_id, video=open(output_path, 'rb'))
    await context.bot.send_message(chat_id=chat_id, text='Done!')

if __name__ == '__main__':
    app = ApplicationBuilder().token(TOKEN).build()
    app.add_handler(CommandHandler('start', start))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    print('Bot started...')
    app.run_polling()
    
