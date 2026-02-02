import os
import json
from telethon import TelegramClient

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]
KEYWORDS = ["Москва", "из Москвы"]
GROUP_USERNAME = "to_road_mo"
HISTORY_FILE = "sent_messages.json"  # файл для хранения истории

def load_sent_ids():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_sent_ids(ids):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids), f)

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    sent_ids = load_sent_ids()
    new_ids = set()

    for channel in CHANNELS:
        print(f"🔍 Проверяю {channel}...")
        try:
            messages = await client.get_messages(channel, limit=10)
            for msg in messages:
                if not msg.text:
                    continue
                if any(kw.lower() in msg.text.lower() for kw in KEYWORDS):
                    composite_id = f"{channel}_{msg.id}"
if composite_id in sent_ids:
    ...
    new_ids.add(composite_id)
                        print(f"⏭️ Уже отправляли (ID: {msg.id})")
                        continue
                    print(f"📩 Отправляю в группу: {msg.text[:100]}...")
                    await client.send_message(GROUP_USERNAME, msg.text)
                    new_ids.add(msg.id)
        except Exception as e:
            print(f"❌ Ошибка в {channel}: {e}")

    # Обновляем историю
    sent_ids.update(new_ids)
    save_sent_ids(sent_ids)

    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
