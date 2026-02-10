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

PHONE = os.getenv("PHONE")  # Ваш номер телефона (например, "79123456789")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
MY_PHONE_CODE = os.getenv("MY_PHONE_CODE")  # Код из SMS (6 цифр)

CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]

# 🔑 ССЫЛКИ БЕЗ ПРОБЕЛОВ! Проверьте визуально в репозитории
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
    # Функция для автоматического ввода кода из секрета
    def code_callback():
        if MY_PHONE_CODE:
            print(f"✅ Использую код из секрета MY_PHONE_CODE: {MY_PHONE_CODE}")
            return MY_PHONE_CODE
        else:
            print("⚠️ Секрет MY_PHONE_CODE не задан. Требуется ручной ввод кода.")
            return input("Введите код из SMS: ")

    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE, code_callback=code_callback)

    sent_ids = load_sent_ids()
    new_ids = set()

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
