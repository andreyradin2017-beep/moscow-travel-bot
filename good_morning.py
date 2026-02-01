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
WIFE_USERNAME = "+79509156095"

# Список милых фраз (без изменений)
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

# Случайные приветствия
GREETINGS = [
    "Доброе утро, красавица!",
    "Доброе утро, моя звезда! ✨",
    "Доброе утро, солнышко! ☀️",
    "Доброе утро, любимая! 💕",
    "Доброе утро, моя радость! 🌸"
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

def get_season():
    """Определяет сезон по месяцу"""
    month = datetime.now().month
    if month in [12, 1, 2]:
        return "winter"
    elif month in [3, 4, 5]:
        return "spring"
    elif month in [6, 7, 8]:
        return "summer"
    else:
        return "autumn"

def get_weather():
    """Возвращает P.S. с погодой и сезонным советом"""
    try:
        lat, lon = 54.1931, 37.6178
        url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true&timezone=Europe%2FMoscow"
        response = requests.get(url, timeout=10)
        data = response.json()
        
        temp = int(data["current_weather"]["temperature"])
        weather_code = data["current_weather"]["weathercode"]
        season = get_season()

        # Базовые параметры
        if weather_code in [51, 53, 55, 61, 63, 65]:
            desc, emoji = "дождь", "☔"
            if season == "winter":
                advice = "не забудь зонт и тёплые носки!"
            elif season == "summer":
                advice = "зонт и лёгкую куртку!"
            else:
                advice = "не забудь зонт!"
        elif weather_code in [71, 73, 75]:
            desc, emoji = "снег", "❄️"
            advice = "шапку, перчатки и тёплую обувь!"
        elif weather_code == 0:
            desc, emoji = "ясно", "☀️"
            if season == "summer":
                advice = "солнцезащитные очки и крем!"
            elif season == "winter":
                advice = "не забудь про защиту от мороза!"
            else:
                advice = "отличный день для прогулки!"
        elif weather_code in [1, 2, 3]:
            desc, emoji = "облачно", "⛅"
            if season == "autumn":
                advice = "возьми что-то тёплое и плед!"
            elif season == "spring":
                advice = "берегись весенней хандры — ты прекрасна!"
            else:
                advice = "хороший день для кофе!"
        elif weather_code in [45, 48]:
            desc, emoji = "туман", "🌫️"
            advice = "будь осторожна за рулём!"
        elif weather_code == 95:
            desc, emoji = "гроза", "⛈️"
            advice = "лучше остаться дома!"
        else:
            desc, emoji = "погода", "🌤️"
            advice = "хорошего дня!"

        return f"P.S. На улице {temp}°C и {desc} — {advice} {emoji}"
    
    except Exception as e:
        print(f"Ошибка погоды: {e}")
        return "P.S. Не смог узнать погоду, но всё равно оденься по погоде! 🧥"

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

    greeting = random.choice(GREETINGS)
    weather_line = get_weather()
    message = f"{greeting}\n\n{phrase}\n\n{weather_line}"

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
