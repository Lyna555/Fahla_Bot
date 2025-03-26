import asyncio
import os
import uuid
from telethon import TelegramClient, events
from telethon.tl.types import ChannelParticipantsAdmins
from pytgcalls import PyTgCalls
from dotenv import load_dotenv

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

# check if the sender if it's an admin
async def check_if_admin(event):
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return
    
# check if the bot is active on this group
async def check_if_bot_active(chat_id, event):
    if chat_id not in active_groups:
        await event.reply("⚠️ البوت غير مفعل في هذه المجموعة! استخدم `/ابدا` أولًا.")
        return

# start the bot
@client.on(events.NewMessage(pattern="/ابدا"))
async def start_bot(event):
    
    check_if_admin(event)
    
    chat_id = event.chat_id
    active_groups.add(chat_id)

    await event.reply("""✅ البوت مفعل الآن ويمكنك استخدام الأوامر!

    🔹 **كيف يعمل البوت؟**
    1️⃣ **تفعيل البوت**: عند إرسال `/ابدا`، يتم تشغيل البوت ويصبح جاهزًا للاستجابة للأوامر.
    2️⃣ **حفظ الملفات الصوتية**: عند إرسال الملف الصوتي، سيتم حفظه تلقائيًا (فقط من قبل المشرفين).
    3️⃣ **تشغيل الصوت في المحادثة الصوتية**: قم بالرد على الملف الصوتي الذي أرسلته وأرسل `/شغل` لتشغيله.
    4️⃣ **التحكم في التشغيل**:
    - ⏸ `/توقف` لإيقاف التشغيل مؤقتًا.
    - ▶ `/اكمل` لاستئناف التشغيل.
    - ⛔ `/اغلق` لإيقاف البوت والخروج من المحادثة الصوتية.""")

# saving the audio sended
@client.on(events.NewMessage(func=lambda e: e.file and (e.file.mime_type.startswith('audio') or e.file.name)))
async def save_audio(event):
    
    chat_id = event.chat_id
    
    # check if the user bot is active
    if chat_id not in active_groups: return
    
    check_if_admin(event)
    
    await event.reply("جار حفظ الملف ...")
    
    if event.file.name:
        filename = event.file.name # get filename for external audio file
    else:
        filename = f"voice_{uuid.uuid4().hex}.ogg" # create a filename for Telegram vocals
    
    file_path = os.path.join(SAVE_FOLDER, filename)

    # Save the audio file
    await event.download_media(file_path)
    uploaded_files[chat_id] = filename  

    await event.reply(f"✅ تم حفظ الملف بنجاح: `{filename}`")


# join the chat voice and play the audio file
@client.on(events.NewMessage(pattern="/شغل"))
async def play_voice_chat(event):
    
    chat_id = event.chat_id
    
    check_if_bot_active(chat_id, event)
    check_if_admin(event)

    # check if the sender is replying on the wanted audio file
    if not event.reply_to_msg_id:
        await event.reply("⚠️ يرجى الرد على الملف الصوتي الذي تريد تشغيله باستخدام /شغل")
        return
    
    # searching for the audio file
    filename = uploaded_files.get(chat_id)
    
    # get audio file path
    file_path = os.path.join(SAVE_FOLDER, filename)

    # check if the audio file is available
    if not filename:
        await event.reply("⚠️ الملف غير متوفر! أعد إرساله فضلا.")
        return
    
    # playing the audio file
    try:
        await event.reply(f"🔊 جارٍ تشغيل: `{filename}`")
        try:
            await pytgcalls.start()
            await pytgcalls.play(chat_id, file_path)
        except:
            await pytgcalls.play(chat_id, file_path)

        await event.reply("🎶 تم تشغيل الملف الصوتي")
            
    except Exception as e:
        await event.reply("❌ خطأ أثناء التشغيل")
        print(f"Error: {e}")  

# pause the audio file
@client.on(events.NewMessage(pattern="/توقف"))
async def pause_voice_chat(event):
    
    chat_id = event.chat_id
     
    check_if_admin(event)
    check_if_bot_active(chat_id, event)

    # stoping the audio
    if event.is_group:
        await event.reply("⏸ توقف")
        await pytgcalls.pause(chat_id)

# resume the audio file
@client.on(events.NewMessage(pattern="/اكمل"))
async def resume_voice_chat(event):
    
    chat_id = event.chat_id
    
    check_if_admin(event)
    check_if_bot_active(chat_id, event)

    # resuming the audio
    if event.is_group:
        await event.reply("▶ أكمل")
        await pytgcalls.resume(chat_id)

# stop the bot
@client.on(events.NewMessage(pattern="/اغلق"))
async def stop_bot(event):
    
    chat_id = event.chat_id

    check_if_admin(event)
    check_if_bot_active(chat_id, event)
    
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
