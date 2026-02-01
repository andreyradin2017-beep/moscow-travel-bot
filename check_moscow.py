import os
import json
from telethon import TelegramClient

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]
KEYWORDS = ["Москва", "из Москвы", "МСК", "московский"]
LAST_IDS_FILE = "last_ids.json"

def load_last_ids():
    if os.path.exists(LAST_IDS_FILE):
        with open(LAST_IDS_FILE) as f:
            return {k: int(v) for k, v in json.load(f).items()}
    return {}

def save_last_ids(ids):
    with open(LAST_IDS_FILE, "w") as f:
        json.dump(ids, f)

def contains_keyword(text):
    return text and any(kw.lower() in text.lower() for kw in KEYWORDS)

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    last_ids = load_last_ids()
    new_last_ids = {}

    for channel in CHANNELS:
        print(f"🔍 Проверяю {channel}...")
        try:
            messages = await client.get_messages(channel, limit=20)
            last_id = last_ids.get(channel, 0)
            
            for msg in messages:
                if not msg.text or msg.id <= last_id:
                    continue
                if contains_keyword(msg.text):
                    print(f"📩 Найдено: {msg.text[:100]}...")
                    await client.forward_messages('me', msg)
                new_last_ids[channel] = max(new_last_ids.get(channel, 0), msg.id)
                
        except Exception as e:
            print(f"❌ Ошибка: {e}")

    save_last_ids(new_last_ids)
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())