import os
import json
import re
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import (
    InviteHashInvalidError, UserAlreadyParticipantError, FloodWaitError,
    ChatAdminRequiredError, UserNotParticipantError, BadRequestError, InviteHashExpiredError
)
from datetime import datetime, timedelta, timezone

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHANNELS = ["@nachemodanah", "@trvlclick", "@vandroukiru"]
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

def get_invite_hash(link):
    link = link.strip()
    if "t.me/+" in link:
        return link.split("t.me/+")[1].split("?")[0].split("#")[0].strip()
    elif "t.me/joinchat/" in link:
        return link.split("t.me/joinchat/")[1].split("?")[0].split("#")[0].strip()
    else:
        raise ValueError(f"Некорректный формат ссылки: {link}")

async def join_and_get_private_channel(client, invite_link):
    invite_link = invite_link.strip()
    print(f"🔍 Обрабатываю приватный чат: {invite_link}")
    
    # Шаг 1: Пробуем получить чат напрямую (если уже участник)
    try:
        entity = await client.get_entity(invite_link)
        title = getattr(entity, 'title', getattr(entity, 'first_name', 'Без названия'))
        print(f"✅ Уже состою в чате: {title} (ID: {entity.id})")
        return entity
    except (ValueError, Exception) as e:
        print(f"ℹ️ Чат не найден напрямую ({e}), пробую присоединиться через инвайт...")

    # Шаг 2: Если не участник — используем инвайт
    try:
        hash_part = get_invite_hash(invite_link)
        print(f"🔑 Извлечён хеш приглашения: '{hash_part}'")
        
        updates = await client(ImportChatInviteRequest(hash_part))
        entity = updates.chats[0] if hasattr(updates, 'chats') and updates.chats else None
        
        if entity:
            print(f"✅ Успешно присоединились к чату: {entity.title} (ID: {entity.id})")
            return entity
        else:
            print(f"❌ Не удалось получить сущность чата после присоединения")
            return None
            
    except UserAlreadyParticipantError:
        print("⚠️ Уже состою в чате (через исключение).")
        return await client.get_entity(invite_link)
    except InviteHashExpiredError:
        print(f"❌ ССЫЛКА ПРОСРОЧЕНА: {invite_link}")
        print("💡 Решение: запросите у администратора чата НОВУЮ ссылку-приглашение.")
        return None
    except InviteHashInvalidError:
        print(f"❌ НЕВЕРНЫЙ ХЕШ приглашения: {invite_link}")
        print("💡 Проверьте корректность ссылки или запросите новую у администратора.")
        return None
    except FloodWaitError as e:
        print(f"⏰ FloodWait: нужно подождать {e.seconds} секунд")
        return "FLOOD_WAIT"
    except Exception as e:
        print(f"❌ Неизвестная ошибка при работе с чатом {invite_link}: {type(e).__name__}: {e}")
        return None

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    sent_ids = load_sent_ids()
    new_ids = set()

    # Обработка обычных каналов
    for channel in CHANNELS:
        print(f"\n🔍 Проверяю публичный канал: {channel}")
        try:
            messages = await client.get_messages(channel, limit=20)
            if not messages:
                print(f"⚠️ Нет сообщений в {channel}.")
                continue

            for msg in messages:
                if not msg.date or msg.date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(days=MAX_POST_AGE_DAYS):
                    continue

                original_text = msg.message if hasattr(msg, 'message') else getattr(msg, 'text', '')
                if matches_departure_from_moscow(original_text):
                    composite_id = f"{channel}_{msg.id}"
                    if composite_id in sent_ids:
                        print(f"⏭️ Уже отправляли (ID: {composite_id})")
                        continue
                    print(f"📩 Отправляю в группу: {original_text[:100]}...")
                    await client.send_message(GROUP_USERNAME, original_text)
                    new_ids.add(composite_id)
        except FloodWaitError as e:
            print(f"⏰ Ожидание {e.seconds} секунд из-за ограничения API.")
        except Exception as e:
            print(f"❌ Ошибка в {channel}: {e}")

    # Обработка приватных групп
    print("\n" + "="*60)
    print("РАБОТА С ПРИВАТНЫМИ ЧАТАМИ")
    print("="*60)
    
    for invite_link in PRIVATE_INVITE_LINKS:
        print(f"\n🔍 Обрабатываю приватный чат: {invite_link.strip()}")
        chat_entity = await join_and_get_private_channel(client, invite_link)
        
        if chat_entity == "FLOOD_WAIT":
            print("⚠️ Пропускаем из-за FloodWait")
            continue
        if not chat_entity:
            print(f"❌ Не удалось получить доступ к чату: {invite_link.strip()}")
            continue

        try:
            messages = await client.get_messages(chat_entity, limit=20)
            if not messages:
                print(f"⚠️ Нет сообщений в приватном чате '{getattr(chat_entity, 'title', chat_entity.id)}'.")
                continue

            for msg in messages:
                if not msg.date or msg.date.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc) - timedelta(days=MAX_POST_AGE_DAYS):
                    continue

                original_text = msg.message if hasattr(msg, 'message') else getattr(msg, 'text', '')
                if matches_departure_from_moscow(original_text):
                    composite_id = f"{chat_entity.id}_{msg.id}"
                    if composite_id in sent_ids:
                        print(f"⏭️ Уже отправляли (ID: {composite_id})")
                        continue
                    print(f"📩 Отправляю из приватного чата '{getattr(chat_entity, 'title', chat_entity.id)}': {original_text[:100]}...")
                    await client.send_message(GROUP_USERNAME, original_text)
                    new_ids.add(composite_id)
        except FloodWaitError as e:
            print(f"⏰ Ожидание {e.seconds} секунд из-за ограничения API.")
        except UserNotParticipantError:
            print(f"❌ Не являюсь участником чата '{getattr(chat_entity, 'title', chat_entity.id)}'.")
        except ChatAdminRequiredError:
            print(f"❌ Недостаточно прав для чтения сообщений в чате '{getattr(chat_entity, 'title', chat_entity.id)}'.")
        except Exception as e:
            print(f"❌ Ошибка при работе с приватным чатом '{getattr(chat_entity, 'title', chat_entity.id)}': {e}")

    sent_ids.update(new_ids)
    save_sent_ids(sent_ids)
    print(f"\n✅ Обработано новых сообщений: {len(new_ids)}")
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
