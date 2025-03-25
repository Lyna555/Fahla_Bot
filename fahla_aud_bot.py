import asyncio
import os
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
from pytgcalls import PyTgCalls
from dotenv import load_dotenv

load_dotenv()

# Telegram app information + Telegram account information
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PHONE_NUMBER = os.getenv("PHONE_NUMBER")
CLIENT_CODE = os.getenv("CLIENT_CODE")

client = TelegramClient("session_name", API_ID, API_HASH)

pytgcalls = PyTgCalls(client)

uploaded_files = {}

SAVE_FOLDER = "./audios"
os.makedirs(SAVE_FOLDER, exist_ok=True)

bot_active = False

# verify if the command sender is an admin
async def is_admin(event):
    if not event.is_group:
        return True
    
    chat_id = event.chat_id
    sender_id = event.sender_id

    # get all admins
    admins = await client.get_participants(chat_id, filter=ChannelParticipantsAdmins)
    
    return any(admin.id == sender_id for admin in admins)

# start the bot
@client.on(events.NewMessage(pattern="/ابدا"))
async def start_bot(event):

    global bot_active

    # check if the sender if it's an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    bot_active = True

    await event.reply("""✅ البوت مفعل الآن ويمكنك استخدام الأوامر!

    🔹 **كيف يعمل البوت؟**
    1️⃣ **تفعيل البوت**: عند إرسال `/ابدا`، يتم تشغيل البوت ويصبح جاهزًا للاستجابة للأوامر.
    2️⃣ **حفظ الملفات الصوتية**: عند إرسال ملف `.mp3`، سيتم حفظه تلقائيًا (فقط من قبل المشرفين).
    3️⃣ **تشغيل الصوت في المحادثة الصوتية**: استخدم `/شغل` لتشغيل الملف الصوتي الذي أرسلته.
    4️⃣ **التحكم في التشغيل**:
    - ⏸ `/توقف` لإيقاف التشغيل مؤقتًا.
    - ▶ `/اكمل` لاستئناف التشغيل.
    - ⛔ `/اغلق` لإيقاف البوت والخروج من المحادثة الصوتية.""")

# saving the audio sended if its type is .mp3
@client.on(events.NewMessage(func=lambda e: e.file and getattr(e.file, 'name', None) and e.file.name.endswith('.mp3')))
async def save_audio(event):

    global bot_active

    # check if the bot is ON
    if not bot_active:
        return
    
    # check if the sende r is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return 
    
    await event.reply("جار حفظ الملف ...")

    chat_id = event.chat_id

    # get the path to download the audio in
    filename = event.file.name
    file_path = os.path.join(SAVE_FOLDER, filename)

    # save the audio file
    await event.download_media(file_path)
    uploaded_files[chat_id] = filename  

    await event.reply(f"✅ تم حفظ الملف بنجاح: `{filename}`")

# join the chat voice and play the audio file
@client.on(events.NewMessage(pattern="/شغل"))
async def play_voice_chat(event):
    
    global bot_active

    # check if the bot is active
    if not bot_active:
        return
    
    # check if the sender is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    chat_id = event.chat_id

    # check if the sender is replying on the wanted audio file
    if not event.reply_to_msg_id:
        await event.reply("⚠️ يرجى الرد على الملف الصوتي الذي تريد تشغيله باستخدام /شغل")
        return
    
    # searching for the audio file
    filename = uploaded_files.get(chat_id)

    # check if the audio file is available
    if not filename:
        await event.reply("⚠️ الملف غير متوفر! أعد إرساله فضلا.")
        return
    
    # playing the audio file
    try:
        await event.reply(f"🔊 جارٍ تشغيل: `{filename}`")
        try:
            await pytgcalls.start()
            await pytgcalls.play(chat_id, os.path.join(SAVE_FOLDER, filename))
        except:
            await pytgcalls.play(chat_id, os.path.join(SAVE_FOLDER, filename))

        await event.reply("🎶 جارٍ تشغيل الملف الصوتي")
    except Exception as e:
        await event.reply("❌ خطأ أثناء التشغيل")
        print(f"Error: {e}")  

# pause the audio file
@client.on(events.NewMessage(pattern="/توقف"))
async def pause_voice_chat(event):
    global bot_active

    # check if the bot is active
    if not bot_active:
        return
    
    # check is the sender is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return
    
    chat_id = event.chat_id

    # stoping the audio
    if event.is_group:
        await event.reply("⏸ توقف")
        await pytgcalls.pause(chat_id)

# resume the audio file
@client.on(events.NewMessage(pattern="/اكمل"))
async def resume_voice_chat(event):

    global bot_active

    # check if the bot is active
    if not bot_active:
        return
    
    # check if the sender is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    chat_id = event.chat_id

    # resuming the audio
    if event.is_group:
        await event.reply("▶ أكمل")
        await pytgcalls.resume(chat_id)

# stop the bot
@client.on(events.NewMessage(pattern="/اغلق"))
async def stop_bot(event):

    global bot_active

    # check if the sender is an admin
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    bot_active = False

    chat_id = event.chat_id
    
    # stopping the bot and leaving the chat voice
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
