import os
import random
from telethon import TelegramClient
from datetime import datetime

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WIFE_USERNAME = "+79509156095"

# Список нежных фраз на ночь (можно расширить)
NIGHT_PHRASES = [
    "Спокойной ночи, моя любовь. Завтра будет ещё один день с тобой 🌙",
    "Пусть тебе приснятся самые тёплые сны. Спокойной ночи! 💤",
    "Засыпай с мыслью, что ты — самое важное в моей жизни. Спокойной ночи! ❤️",
    "Пусть утро принесёт тебе радость. А пока — сладких снов! 🌜",
    "Ты сегодня была великолепна. Отдыхай, моя звезда! ✨"
]

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    message = random.choice(NIGHT_PHRASES)
    
    print(f"🌙 Отправляю 'Спокойной ночи': {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    try:
        await client.send_message(WIFE_USERNAME, message)
        print("✅ Сообщение отправлено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
