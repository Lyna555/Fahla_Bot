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

async def is_admin(event):
    if not event.is_group:
        return True
    
    chat_id = event.chat_id
    sender_id = event.sender_id
    admins = await client.get_participants(chat_id, filter=ChannelParticipantsAdmins)
    
    return any(admin.id == sender_id for admin in admins)


@client.on(events.NewMessage(pattern="/ابدا"))
async def start_bot(event):
    global bot_active
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    bot_active = True
    await event.reply("✅ البوت مفعل الآن ويمكنك استخدام الأوامر!")


@client.on(events.NewMessage(func=lambda e: e.file and getattr(e.file, 'name', None) and e.file.name.endswith('.mp3')))
async def save_audio(event):
    global bot_active
    if not bot_active:
        return
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return 
    
    await event.reply("جار حفظ الملف ...")

    chat_id = event.chat_id
    filename = event.file.name
    file_path = os.path.join(SAVE_FOLDER, filename)

    await event.download_media(file_path)
    uploaded_files[chat_id] = filename  

    await event.reply(f"✅ تم حفظ الملف بنجاح: `{filename}`")


@client.on(events.NewMessage(pattern="/شغل"))
async def play_voice_chat(event):
    global bot_active
    if not bot_active:
        return
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    chat_id = event.chat_id

    if not event.reply_to_msg_id:
        await event.reply("⚠️ يرجى الرد على الملف الصوتي الذي تريد تشغيله باستخدام /ابدا")
        return

    filename = uploaded_files.get(chat_id)

    if not filename:
        await event.reply("⚠️ الملف غير متوفر! أعد إرساله فضلا.")
        return

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


@client.on(events.NewMessage(pattern="/توقف"))
async def pause_voice_chat(event):
    global bot_active
    if not bot_active:
        return
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    chat_id = event.chat_id
    if event.is_group:
        await event.reply("⏸ توقف")
        await pytgcalls.pause(chat_id)


@client.on(events.NewMessage(pattern="/اكمل"))
async def resume_voice_chat(event):
    global bot_active
    if not bot_active:
        return
    
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    chat_id = event.chat_id
    if event.is_group:
        await event.reply("▶ أكمل")
        await pytgcalls.resume(chat_id)


@client.on(events.NewMessage(pattern="/اغلق"))
async def stop_bot(event):
    global bot_active
    if not await is_admin(event):
        await event.reply("🚫 فقط المشرفين يمكنهم استخدام هذا الأمر!")
        return

    bot_active = False
    chat_id = event.chat_id
    
    await pytgcalls.leave_call(chat_id)
    await event.reply("⛔ البوت متوقف الآن!")


async def main():
    await client.connect()
    
    if not await client.is_user_authorized():
        await client.send_code_request(PHONE_NUMBER)
        await client.sign_in(phone=PHONE_NUMBER, code=CLIENT_CODE)

    print("User bot is running...")
    await client.run_until_disconnected()


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main())
