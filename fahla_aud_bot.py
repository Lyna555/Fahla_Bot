import asyncio
import os
import uuid
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
from pytgcalls import PyTgCalls
from dotenv import load_dotenv
from pytube import Playlist
import yt_dlp

load_dotenv()

# Telegram app information
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# Telegram userbot information
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
CLIENT_CODE = os.getenv("CLIENT_CODE")

client = TelegramClient("session_name", API_ID, API_HASH)

pytgcalls = PyTgCalls(client)

uploaded_files = {}

SAVE_FOLDER = "./audios"
os.makedirs(SAVE_FOLDER, exist_ok=True)

active_groups = set()

# verify if the command sender is an admin
async def is_admin(event):
    if not event.is_group:
        return True
    
    chat_id = event.chat_id
    sender_id = event.sender_id

    # get all admins
    admins = await client.get_participants(chat_id, filter=ChannelParticipantsAdmins)
    
    return any(admin.id == sender_id for admin in admins)

# get youtube playlist videos
async def get_playlist_videos(playlist_url):
    try:
        playlist = Playlist(playlist_url)
        video_urls = playlist.video_urls
        return video_urls
    except Exception as e:
        print(f"Error fetching playlist: {e}")
        return []

# start the bot
@client.on(events.NewMessage(pattern="/ابدا"))
async def start_bot(event):
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return
    
    chat_id = event.chat_id
    active_groups.add(chat_id)

    await event.reply("""✅ البوت مفعل الآن ويمكنك استخدام الأوامر!

    🔹 **كيف يعمل البوت؟**
    1️⃣ **تفعيل البوت**: عند إرسال `/ابدا`، يتم تشغيل البوت ويصبح جاهزًا للاستجابة للأوامر.
    2️⃣ **حفظ الملفات الصوتية**: عند إرسال الملف الصوتي، سيتم حفظه تلقائيًا (فقط من قبل المشرفين).
    3️⃣ **تشغيل الصوت في المحادثة الصوتية**: قم بالرد على الملف الصوتي الذي أرسلته وأرسل `/حفظ` لحفظه ثم `/شغل` لتشغيله.
    4️⃣ **التحكم في التشغيل**:
    - ⏸ `/توقف` لإيقاف التشغيل مؤقتًا.
    - ▶ `/اكمل` لاستئناف التشغيل.
    - ⛔ `/اغلق` لإيقاف البوت والخروج من المحادثة الصوتية.
    5️⃣ **تعليمات إضافية**:
    - `/قرآن` لتشغيل القرآن كاملا.
    - `/الملك` لتشغيل سورة الملك.
    - `/البقرة` لتشغيل سورة البقرة.
    - `/دعاء` لتشغيل دعاء من الكتاب والسنة.
    - `/مستجاب` لتشغيل دعاء مستجاب.
    - `/يوسف` لتشغيل سورة يوسف.
    - `/اذكار`  لتشغيل دعاء الصباح والمساء.
    - `/تكبيرات`  لتشغيل تكبيرات العيد.""")


VIDEO_FILES = {
    "/دعاء": "audios/kitab.mp4",
    "/الملك": "audios/mulk.mp4",
    "/البقرة": "audios/bakara.mp4",
    "/مستجاب": "audios/mustajab.mp4",
    "/يوسف": "audios/youssef.mp4",
    "/اذكار": "audios/adkar.mp4",
    "/تكبيرات" : "audios/takbirat.ogg"
    
}

# playing existed videos
@client.on(events.NewMessage(pattern=r"/(دعاء|الملك|البقرة|مستجاب|يوسف|اذكار|تكبيرات)"))
async def play_specific_video(event):
    
    chat_id = event.chat_id
    
    # get command
    command = event.text.strip()
    
    # Check if the user bot is active in this group
    if chat_id not in active_groups:
        await event.reply("⚠️ البوت غير مفعل في هذه المجموعة! استخدم `/ابدا` أولًا.")
        return
    
    # Check if the user is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return
    
    file_path = VIDEO_FILES.get(command)
    
    # check if the video exists
    if not file_path:
        await event.reply("⚠️ لم يتم العثور على الفيديو المطلوب!")
        return
    
    try:
        await event.reply("📹 جارٍ تشغيل الفيديو...")
        try:
            await pytgcalls.start()
            await pytgcalls.play(chat_id, file_path)
        except:
            await pytgcalls.play(chat_id, file_path)
            
        await event.reply("🎥 تم تشغيل الفيديو بنجاح")
    except Exception as e:
        await event.reply("⚠️ يرجى فتح الغرفة الصوتية أولًا!")
        print(f"Error: {e}")

# playing quran by Yassin El-Djazairi 
@client.on(events.NewMessage(pattern="/قرآن"))
async def play_youtube_playlist(event):
    
    chat_id = event.chat_id
    
    # Check if the user bot is active in this group
    if chat_id not in active_groups:
        await event.reply("⚠️ البوت غير مفعل في هذه المجموعة! استخدم `/ابدا` أولًا.")
        return
    
    # Check if the user is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    playlist_url = "https://www.youtube.com/watch?v=oj1dIsucvaU&list=PLBmYhnNemtrxMMJKZ8q6HZYXKMNlfmq_y"

    # Fetch video URLs from the playlist
    video_urls = await get_playlist_videos(playlist_url)
    
    if not video_urls:
        await event.reply("❌ لم يتم العثور على أي فيديوهات في قائمة التشغيل!")
        return

    await event.reply(f"🔄 جاري تشغيل قائمة التشغيل ({len(video_urls)} فيديوهات)...")

    # Play each video in the playlist
    for video_url in video_urls:
        await event.reply(f"🎶 تشغيل: {video_url}")

        # Extract audio URL using yt_dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'extract_audio': True,
            'noplaylist': True,
            'quiet': True
        }
    
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(video_url, download=False)
            audio_url = info.get('url', None)
            
        # playing video
        if audio_url:
            try:
                try:
                    await pytgcalls.start()
                    await pytgcalls.play(chat_id, audio_url)
                except:
                    await pytgcalls.play(chat_id, audio_url)
                    
                await asyncio.sleep(info.get('duration', 5))
            except Exception as e:
                await event.reply(f"⚠️ يرجى التأكد من أن الغرفة مفتوحة")


# saving the audio sended
@client.on(events.NewMessage(pattern="/حفظ"))
async def save_audio(event):
    
    chat_id = event.chat_id

    # Check if the user bot is active in this group
    if chat_id not in active_groups:
        return

    # Ensure the command is in reply to a message
    if not event.reply_to_msg_id:
        await event.reply("⚠️ يرجى الرد على ملف صوتي لاستخدام الأمر `/حفظ`")
        return

    # Check if the user is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    await event.reply("🔄 جار حفظ الملف ...")

    # Get the replied message
    reply_msg = await event.get_reply_message()

    # Check if the replied message contains an audio file
    if not reply_msg.file or not reply_msg.file.ext not in ("mp4", "mp3", "ogg"):
        await event.reply("⚠️ يجب الرد على ملف صوتي فقط!")
        return

    # Extract filename if available; otherwise, generate one
    filename = reply_msg.file.name if reply_msg.file.name else f"voice_{uuid.uuid4().hex}.ogg"
    file_path = os.path.join(SAVE_FOLDER, filename)

    # Save the audio file
    await reply_msg.download_media(file_path)
    uploaded_files[chat_id] = filename  

    await event.reply(f"✅ تم حفظ الملف بنجاح: `{filename}`")


# join the chat voice and play the replied audio file
@client.on(events.NewMessage(pattern="/شغل"))
async def play_voice_chat(event):
    chat_id = event.chat_id

    if chat_id not in active_groups:
        await event.reply("⚠️ البوت غير مفعل في هذه المجموعة! استخدم `/ابدا` أولًا.")
        return

    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    # Check if the sender is replying to a message
    if not event.reply_to_msg_id:
        await event.reply("⚠️ يرجى الرد على الملف الصوتي الذي تريد تشغيله باستخدام /شغل")
        return

    # Get the replied message
    reply_msg = await event.get_reply_message()

    # Check if the replied message contains an audio file
    if not reply_msg.file or not reply_msg.file.ext not in ("mp4", "mp3", "ogg"):
        await event.reply("⚠️ يجب الرد على ملف صوتي فقط!")
        return

    # Extract filename if available; otherwise, generate a unique one
    filename = reply_msg.file.name if reply_msg.file.name else f"voice_{uuid.uuid4().hex}.ogg"
    file_path = os.path.join(SAVE_FOLDER, filename)

    # Download the audio file
    await event.reply("🔄 جارٍ تحميل الملف الصوتي ...")
    await reply_msg.download_media(file_path)

    # Playing the audio file
    try:
        await event.reply(f"🔊 جارٍ تشغيل: `{filename}`")

        try:
            await pytgcalls.start()
            await pytgcalls.play(chat_id, file_path)
        except:
            await pytgcalls.play(chat_id, file_path)

        await event.reply("🎶 تم تشغيل الملف الصوتي")
    
    except Exception as e:
        await event.reply("⚠️ يرجى التأكد من أن الغرفة مفتوحة")
        print(f"Error: {e}")

# pause the audio file
@client.on(events.NewMessage(pattern="/توقف"))
async def pause_voice_chat(event):
    
    chat_id = event.chat_id
     
    if chat_id not in active_groups:
        await event.reply("⚠️ البوت غير مفعل في هذه المجموعة! استخدم `/ابدا` أولًا.")
        return
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    # stoping the audio
    if event.is_group:
        await event.reply("⏸ توقف")
        await pytgcalls.pause(chat_id)

# resume the audio file
@client.on(events.NewMessage(pattern="/اكمل"))
async def resume_voice_chat(event):
    
    chat_id = event.chat_id
    
    if chat_id not in active_groups:
        await event.reply("⚠️ البوت غير مفعل في هذه المجموعة! استخدم `/ابدا` أولًا.")
        return
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    # resuming the audio
    if event.is_group:
        await event.reply("▶ أكمل")
        await pytgcalls.resume(chat_id)

# stop the bot
@client.on(events.NewMessage(pattern="/اغلق"))
async def stop_bot(event):
    
    chat_id = event.chat_id
    
    if chat_id not in active_groups:
        await event.reply("⚠️ البوت غير مفعل في هذه المجموعة! استخدم `/ابدا` أولًا.")
        return
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return
    
    # stopping the bot and leaving the chat voice
    if chat_id in active_groups:
        active_groups.remove(chat_id)
        await pytgcalls.leave_call(chat_id)
        
    await event.reply("⛔ البوت متوقف الآن!")


async def main():
    await client.connect()
    
    # sign in the user
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        await client.sign_in(phone=PHONE_NUMBER, code=CLIENT_CODE)
    
    # running the bot
    print("User bot is running...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
