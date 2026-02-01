import os
import random
import json
from telethon import TelegramClient
from datetime import datetime

# === Ваши данные ===
PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

# Замените на username или номер вашей жены
WIFE_USERNAME = "me"  # например: "+79991234567" или "anna_tg"

# Список милых фраз (минимум 6 штук, лучше 10+)
PHRASES = [
    "Ты делаешь мой мир ярче ❤️",
    "Пусть твой день будет таким же прекрасным, как ты!",
    "Я горжусь тобой — даже когда молчу.",
    "Ты сильнее, чем думаешь 💪",
    "Улыбнись — ты сегодня особенно хороша!",
    "Помни: я всегда рядом, даже если молчу.",
    "Ты вдохновляешь меня быть лучше.",
    "С тобой даже серое утро становится золотым.",
    "Ты — мой самый любимый человек на свете.",
    "Пусть удача идёт с тобой весь день!",
    "Ты справишься со всем — я верю в тебя!",
    "Ты — моё спокойствие и мой огонь.",
    "Каждый твой день достоин быть особенным.",
    "Ты красивее всех звёзд вместе взятых ✨",
    "Я люблю тебя — сейчас, всегда и везде.",
    "Ты делаешь меня счастливым просто своим существованием.",
    "Пусть кофе будет крепким, а день — лёгким ☕",
    "Ты — мой дом, куда бы я ни шёл.",
    "Ты заслуживаешь самого лучшего — начиная с этого утра.",
    "С добрым утром, моя любовь! 🌸"
]

HISTORY_FILE = "used_phrases.json"
HISTORY_SIZE = 5  # сколько последних фраз исключать

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
    available = [p for p in PHRASES if p not in used]

    # Если все фразы использованы — сбросить историю
    if not available:
        available = PHRASES
        used = []

    phrase = random.choice(available)
    used.append(phrase)
    save_used_phrases(used)

    message = f"Доброе утро! \n\n{phrase}"

    print(f"🌅 Отправляю сообщение жене: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    try:
        await client.send_message(WIFE_USERNAME, message)
        print("✅ Сообщение отправлено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
