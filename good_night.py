import os
import random
import json
from telethon import TelegramClient
from datetime import datetime

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WIFE_USERNAME = "+79509156095"

NIGHT_PHRASES = [
    "Спокойной ночи, моя любовь. Завтра будет ещё один день с тобой 🌙",
    "Пусть тебе приснятся самые тёплые сны. Спокойной ночи! 💤",
    "Засыпай с мыслью, что ты — самое важное в моей жизни. Спокойной ночи! ❤️",
    "Пусть утро принесёт тебе радость. А пока — сладких снов! 🌜",
    "Ты сегодня была великолепна. Отдыхай, моя звезда! ✨",
    "Мир может ждать до утра. А ты — отдыхай. Спокойной ночи! 🌌",
    "Пусть эта ночь подарит тебе покой. Я рядом — даже во сне. 🌠",
    "Ты заслуживаешь самого сладкого сна. Спокойной ночи, любимая! 🌕"
]

HISTORY_FILE = "used_night_phrases.json"
HISTORY_SIZE = 3  # не повторять 3 дня подряд

def load_used_phrases():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_used_phrases(phrases):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(phrases[-HISTORY_SIZE:], f, ensure_ascii=False)

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    used = load_used_phrases()
    available = [p for p in NIGHT_PHRASES if p not in used]

    if not available:
        # Если все фразы использованы — сбрасываем историю
        available = NIGHT_PHRASES
        used = []

    phrase = random.choice(available)
    used.append(phrase)
    save_used_phrases(used)

    print(f"🌙 Отправляю 'Спокойной ночи': {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    try:
        await client.send_message(WIFE_USERNAME, phrase)
        print("✅ Сообщение отправлено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
