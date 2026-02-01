import os
import random
import json
import requests
from datetime import datetime
from telethon import TelegramClient

# === Ваши данные ===
PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
WIFE_USERNAME = "+79509156095"  # Убедитесь, что это номер вашей жены

# Список милых фраз
PHRASES = [
    "💖 Ты делаешь мой мир ярче!",
    "🌸 Пусть твой день будет таким же прекрасным, как ты!",
    "✨ Я горжусь тобой — даже когда молчу.",
    "💪 Ты сильнее, чем думаешь!",
    "😊 Улыбнись — ты сегодня особенно хороша!",
    "❤️ Помни: я всегда рядом, даже если молчу.",
    "🌟 Ты вдохновляешь меня быть лучше.",
    "☀️ С тобой даже серое утро становится золотым.",
    "🥰 Ты — мой самый любимый человек на свете.",
    "🍀 Пусть удача идёт с тобой весь день!",
    "🔥 Ты справишься со всем — я верю в тебя!",
    "🕊️ Ты — моё спокойствие и мой огонь.",
    "🌈 Каждый твой день достоин быть особенным.",
    "💫 Ты красивее всех звёзд вместе взятых!",
    "💞 Я люблю тебя — сейчас, всегда и везде.",
    "🌻 Ты делаешь меня счастливым просто своим существованием.",
    "☕ Пусть кофе будет крепким, а день — лёгким!",
    "🏡 Ты — мой дом, куда бы я ни шёл.",
    "🎁 Ты заслуживаешь самого лучшего — начиная с этого утра.",
    "🌷 С добрым утром, моя любовь!"
]

HISTORY_FILE = "used_phrases.json"
HISTORY_SIZE = 5

def load_used_phrases():
    if os.path.exists(HISTORY_FILE):
        with open(HISTORY_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def save_used_phrases(phrases):
    with open(HISTORY_FILE, "w", encoding="utf-8") as f:
        json.dump(phrases[-HISTORY_SIZE:], f, ensure_ascii=False)

def get_weather():
    """Получает погоду в Туле на сегодня"""
    try:
        # Координаты Тулы
        lat, lon = 54.1931, 37.6178
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Europe%2FMoscow"
        
        response = requests.get(url, timeout=10)
        data = response.json()
        
        temp = int(data["current_weather"]["temperature"])
        weather_code = data["current_weather"]["weathercode"]
        
        # Расшифровка погоды (упрощённая)
        weather_map = {
            0: "ясно",
            1: "преимущественно ясно",
            2: "переменная облачность",
            3: "облачно",
            45: "туман",
            48: "изморозь",
            51: "слабый дождь",
            53: "дождь",
            55: "сильный дождь",
            61: "слабый дождь",
            63: "дождь",
            65: "сильный дождь",
            71: "слабый снег",
            73: "снег",
            75: "сильный снег",
            95: "гроза",
        }
        desc = weather_map.get(weather_code, "погода")
        
        return f"🌦️ **Тула**: {temp}°C, {desc}"
    except Exception as e:
        print(f"Ошибка погоды: {e}")
        return "🌦️ Погода: не удалось загрузить"

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    used = load_used_phrases()
    available = [p for p in PHRASES if p not in used]
    if not available:
        available = PHRASES
        used = []

    phrase = random.choice(available)
    used.append(phrase)
    save_used_phrases(used)

    weather = get_weather()
    today = datetime.now().strftime("%d %B")

    message = f"Доброе утро, красавица!\n\n{phrase}\n\n{weather}\n📅 Сегодня, {today}"

    print(f"🌅 Отправляю сообщение жене: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    
    try:
        await client.send_message(WIFE_USERNAME, message, parse_mode='md')
        print("✅ Сообщение отправлено!")
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
