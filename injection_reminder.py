import os
import json
from datetime import datetime, timedelta
from telethon import TelegramClient
import httpx

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
PACHCA_ACCESS_TOKEN = os.getenv("PACHCA_ACCESS_TOKEN")
PACHCA_CHAT_ID = os.getenv("PACHCA_CHAT_ID", "35238217")
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

async def send_pachca_notification(text):
    if not PACHCA_ACCESS_TOKEN:
        return
    url = "https://api.pachca.com/api/shared/v1/messages"
    headers = {
        "Authorization": f"Bearer {PACHCA_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "message": {
            "entity_type": "discussion",
            "entity_id": int(PACHCA_CHAT_ID),
            "content": text
        }
    }
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code not in [200, 201]:
                print(f"❌ Ошибка API Пачки: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Исключение при отправке в Пачку: {e}")

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Сессия не найдена. Загрузите session.session файл в репозиторий.")
        return

    last_date = load_last_date()
    today = datetime.now().date()
    days_since = (today - last_date.date()).days

    print(f"Последний укол: {last_date.date()}, прошло дней: {days_since}")

    if days_since >= 5:
        message = "💉 Напоминание: сегодня нужно сделать укол!"
        await client.send_message(CHAT_ID, message)
        await send_pachca_notification(message)
        print("✅ Отправлено напоминание")
        # Обновляем дату последнего укола на СЕГОДНЯ
        save_last_date(datetime.combine(today, datetime.min.time()))
    else:
        print(f"⏳ Следующий укол через {5 - days_since} дней")

    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
