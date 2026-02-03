import os
import json
import re
from telethon import TelegramClient

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]
GROUP_USERNAME = "to_road_mo"
HISTORY_FILE = "sent_messages.json"

def matches_departure_from_moscow(text):
    if not text:
        return False
    t = text.lower()
    patterns = [
        r'\b(?:москва|мск|msk)\s*[-—>→:]\s*\w',
        r'\bиз\s+(?:москвы?|мск|msk)\b',
        r'\b(?:москва|мск|msk)\s+to\s+\w',
        r'\b(?:москва|мск|msk)\s+[а-яa-z]',
    ]
    return any(re.search(pattern, t) for pattern in patterns)

def load_sent_ids():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return set(json.load(f))
    return set()

def save_sent_ids(ids):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(list(ids)[-200:], f)

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    sent_ids = load_sent_ids()
    new_ids = set()

    for channel in CHANNELS:
        print(f"🔍 Проверяю {channel}...")
        try:
            messages = await client.get_messages(channel, limit=20)
            for msg in messages:
                if matches_departure_from_moscow(msg.text):
                    composite_id = f"{channel}_{msg.id}"
                    if composite_id in sent_ids:
                        print(f"⏭️ Уже отправляли (ID: {composite_id})")
                        continue
                    print(f"📩 Отправляю в группу: {msg.text[:100]}...")
                    await client.send_message(GROUP_USERNAME, msg.text)
                    new_ids.add(composite_id)
        except Exception as e:
            print(f"❌ Ошибка в {channel}: {e}")

    sent_ids.update(new_ids)
    save_sent_ids(sent_ids)
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
