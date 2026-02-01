import os
from telethon import TelegramClient

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]
KEYWORDS = ["Москва", "из Москвы"]

# Используем публичный юзернейм группы (без @)
GROUP_USERNAME = "to_road_mo"

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)
    
    for channel in CHANNELS:
        print(f"🔍 Проверяю {channel}...")
        try:
            messages = await client.get_messages(channel, limit=20)
            for msg in messages:
                if msg.text and any(kw.lower() in msg.text.lower() for kw in KEYWORDS):
                    print(f"📩 Отправляю в группу: {msg.text[:100]}...")
                    # Отправляем в публичную группу по юзернейму
                    await client.send_message(GROUP_USERNAME, msg.text)
        except Exception as e:
            print(f"❌ Ошибка в {channel}: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
