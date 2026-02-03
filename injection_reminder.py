import os
import json
from datetime import datetime, timedelta
from telethon import TelegramClient

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHAT_ID = "me"

STATE_FILE = "last_injection.json"

def load_last_date():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            return datetime.fromisoformat(data["date"])
    else:
        # Первый запуск: считаем, что последний укол был СЕГОДНЯ - 5 дней
        today = datetime.now().date()
        last_date = datetime.combine(today - timedelta(days=5), datetime.min.time())
        save_last_date(last_date)
        return last_date

def save_last_date(dt):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"date": dt.isoformat()}, f)

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    last_date = load_last_date()
    today = datetime.now().date()
    days_since = (today - last_date.date()).days

    print(f"Последний укол: {last_date.date()}, прошло дней: {days_since}")

    if days_since >= 5:
        message = "💉 Напоминание: сегодня нужно сделать укол!"
        await client.send_message(CHAT_ID, message)
        print("✅ Отправлено напоминание")
        # Обновляем дату последнего укола на СЕГОДНЯ
        save_last_date(datetime.combine(today, datetime.min.time()))
    else:
        print(f"⏳ Следующий укол через {5 - days_since} дней")

    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
