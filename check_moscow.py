import os
import json
import re
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import (
    InviteHashInvalidError, UserAlreadyParticipantError, FloodWaitError,
    ChatAdminRequiredError, UserNotParticipantError, InviteHashExpiredError
)
from datetime import datetime, timedelta, timezone

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]

# ⚠️ КРИТИЧЕСКИ ВАЖНО: ссылки БЕЗ пробелов в конце!
PRIVATE_INVITE_LINKS = [
    "https://t.me/+b9eRLxlVIls4MzQy",
    "https://t.me/+GWM5t4jm-CZjOGZi"
]

GROUP_USERNAME = "to_road_mo"
HISTORY_FILE = "sent_messages.json"
MAX_POST_AGE_DAYS = 1

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
        json.dump(list(ids), f)

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    sent_ids = load_sent_ids()
    new_ids = set()

    # Обработка публичных каналов
    for channel in CHANNELS:
        print(f"\n🔍 Публичный канал: {channel}")
        try:
            messages = await client.get_messages(channel, limit=20)
            for msg in messages:
                if not msg.date or msg.date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(days=MAX_POST_AGE_DAYS):
                    continue
                text = msg.message or ""
                if matches_departure_from_moscow(text):
                    cid = f"{channel}_{msg.id}"
                    if cid in sent_ids:
                        print(f"⏭️ Уже отправлено: {cid}")
                        continue
                    print(f"✅ Отправляю: {text[:80]}...")
                    await client.send_message(GROUP_USERNAME, text)
                    new_ids.add(cid)
        except Exception as e:
            print(f"❌ Ошибка {channel}: {e}")

    # Обработка приватных чатов — БЕЗ импорта инвайта, если уже участник
    print("\n" + "="*60)
    print("ПРИВАТНЫЕ ЧАТЫ (работаем через прямой доступ)")
    print("="*60)
    
    for link in PRIVATE_INVITE_LINKS:
        link_clean = link.strip()
        print(f"\n🔗 Чат: {link_clean}")
        
        # Пробуем получить чат напрямую — БЕЗ использования инвайта!
        try:
            entity = await client.get_entity(link_clean)
            title = getattr(entity, 'title', 'Без названия')
            print(f"✅ Доступ получен: {title} (ID: {entity.id})")
        except Exception as e:
            print(f"⚠️ Не удалось получить напрямую ({e}), пробую через инвайт...")
            # Только если напрямую не получилось — используем инвайт
            try:
                hash_part = link_clean.split('+')[-1].split('?')[0].split('#')[0].strip()
                print(f"🔑 Хеш: '{hash_part}'")
                await client(ImportChatInviteRequest(hash_part))
                entity = await client.get_entity(link_clean)
                print(f"✅ Присоединились: {getattr(entity, 'title', 'Без названия')}")
            except InviteHashExpiredError:
                print(f"❌ ССЫЛКА ПРОСРОЧЕНА: {link_clean}")
                print("💡 Запросите НОВУЮ ссылку у администратора чата!")
                continue
            except Exception as ex:
                print(f"❌ Не удалось присоединиться: {ex}")
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
                        print(f"⏭️ Уже отправлено: {cid}")
                        continue
                    print(f"✅ Отправляю из '{getattr(entity, 'title', entity.id)}': {text[:80]}...")
                    await client.send_message(GROUP_USERNAME, text)
                    new_ids.add(cid)
        except Exception as e:
            print(f"❌ Ошибка чтения сообщений: {e}")

    sent_ids.update(new_ids)
    save_sent_ids(sent_ids)
    print(f"\n✅ Итого новых сообщений: {len(new_ids)}")
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
