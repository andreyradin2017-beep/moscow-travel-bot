import os
import json
import re
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import (
    InviteHashExpiredError, InviteHashInvalidError, UserAlreadyParticipantError,
    FloodWaitError, ChatAdminRequiredError
)
from datetime import datetime, timedelta, timezone
import httpx

PHONE = os.getenv("PHONE")  # Ваш номер телефона (например, "79123456789")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")

CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]

# 🔑 ССЫЛКИ БЕЗ ПРОБЕЛОВ! Проверьте визуально в репозитории
PRIVATE_INVITE_LINKS = [
    "https://t.me/+b9eRLxlVIls4MzQy",
    "https://t.me/+GWM5t4jm-CZjOGZi"
]

GROUP_USERNAME = "to_road_mo"
HISTORY_FILE = "sent_messages.json"
PACHCA_ACCESS_TOKEN = os.getenv("PACHCA_ACCESS_TOKEN")
PACHCA_CHAT_ID = os.getenv("PACHCA_CHAT_ID", "35238217")

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
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code not in [200, 201]:
                print(f"❌ Ошибка API Пачки: {response.status_code} {response.text}")
    except Exception as e:
        print(f"❌ Исключение при отправке в Пачку: {e}")

def matches_departure_from_moscow(text):
    if not text:
        return False
    t = text.lower()
    patterns = [
        r'\b(?:москва|мск|msk)\s*[-—>→:]\s*\w',
        r'\bиз\s+(?:москвы?|мск|msk)\b',
    ]
    return any(re.search(pattern, t) for pattern in patterns)

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
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Сессия не найдена. Загрузите session.session файл в репозиторий.")
        return

    sent_ids = load_sent_ids()
    new_ids = set()

    MAX_POST_AGE_DAYS = 1

    # Публичные каналы
    for channel in CHANNELS:
        print(f"\n📡 {channel}")
        try:
            messages = await client.get_messages(channel, limit=20)
            for msg in messages:
                if not msg.date or msg.date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(days=MAX_POST_AGE_DAYS):
                    continue
                text = msg.message or ""
                if matches_departure_from_moscow(text):
                    cid = f"{channel}_{msg.id}"
                    if cid in sent_ids:
                        continue
                    print(f"✅ {text[:70]}")
                    await client.send_message(GROUP_USERNAME, text)
                    await send_pachca_notification(text)
                    new_ids.add(cid)
        except Exception as e:
            print(f"❌ {channel}: {e}")

    # Приватные чаты — КРИТИЧЕСКИ ВАЖНО: выводим ссылки в квадратных скобках для видимости пробелов
    print("\n" + "="*50)
    print("🔐 Приватные чаты (проверка на пробелы)")
    print("="*50)
    
    for link in PRIVATE_INVITE_LINKS:
        # Визуальная проверка пробелов — обрамляем скобками
        print(f"\n🔍 Исходная ссылка: [{link}]")
        link_clean = link.strip()
        print(f"   После .strip(): [{link_clean}]")
        
        # Извлекаем хеш БЕЗ пробелов
        try:
            hash_part = link_clean.split('+')[-1].split('?')[0].split('#')[0].strip()
            print(f"   Хеш приглашения: [{hash_part}]")
        except Exception as e:
            print(f"❌ Ошибка извлечения хеша: {e}")
            continue

        # Пробуем получить чат напрямую (если уже участник)
        try:
            entity = await client.get_entity(link_clean)
            print(f"✅ Уже в чате: {getattr(entity, 'title', entity.id)}")
        except Exception as e:
            print(f"   ℹ️ Не найден напрямую ({type(e).__name__}), пробую присоединиться...")
            # Присоединяемся через инвайт
            try:
                await client(ImportChatInviteRequest(hash_part))
                entity = await client.get_entity(link_clean)
                print(f"✅ Присоединились: {getattr(entity, 'title', entity.id)}")
            except InviteHashExpiredError:
                print(f"❌❌ ССЫЛКА ПРОСРОЧЕНА! ❌❌")
                print(f"💡 Решение: запросите НОВУЮ ссылку у администратора чата")
                continue
            except InviteHashInvalidError:
                print(f"❌ Неверный формат хеша (возможно, пробелы в ссылке)")
                continue
            except Exception as ex:
                print(f"❌ Ошибка присоединения: {type(ex).__name__}: {ex}")
                continue

        # Парсим сообщения
        try:
            messages = await client.get_messages(entity, limit=20)
            for msg in messages:
                if not msg.date or msg.date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(days=MAX_POST_AGE_DAYS):
                    continue
                text = msg.message or ""
                if matches_departure_from_moscow(text):
                    cid = f"{entity.id}_{msg.id}"
                    if cid in sent_ids:
                        continue
                    print(f"✅ [{getattr(entity, 'title', str(entity.id))[:15]}] {text[:60]}")
                    await client.send_message(GROUP_USERNAME, text)
                    await send_pachca_notification(text)
                    new_ids.add(cid)
        except Exception as e:
            print(f"❌ Ошибка чтения: {e}")

    sent_ids.update(new_ids)
    save_sent_ids(sent_ids)
    print(f"\n✨ Новых сообщений: {len(new_ids)}")
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
