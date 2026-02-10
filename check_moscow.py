import os
import json
import re
from telethon import TelegramClient
from telethon.tl.functions.messages import ImportChatInviteRequest
from telethon.errors import (
    InviteHashInvalidError, UserAlreadyParticipantError, FloodWaitError,
    ChatAdminRequiredError, UserNotParticipantError, BadRequestError
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
    if link.startswith("https://t.me/+"):
        return link.split("/")[-1]
    elif link.startswith("https://t.me/joinchat/"):
        return link.split("/")[-1]
    else:
        raise ValueError("Invalid invite link format")

async def join_and_get_private_channel(client, invite_link):
    try:
        hash_part = get_invite_hash(invite_link)
        updates = await client(ImportChatInviteRequest(hash_part))
        entity = None
        if hasattr(updates, 'chats') and updates.chats:
            entity = updates.chats[0]
        elif hasattr(updates, 'users') and updates.users:
            # Если это приватная группа с одним пользователем (редко)
            pass
        if not entity:
            entity = await client.get_entity(invite_link)
        print(f"✅ Присоединились к приватному чату: {entity.title}")
        return entity
    except UserAlreadyParticipantError:
        print("⚠️ Уже состою в этом чате.")
        entity = await client.get_entity(invite_link)
        return entity
    except InviteHashInvalidError:
        print(f"❌ Неверная ссылка-приглашение: {invite_link}")
        return None
    except FloodWaitError as e:
        print(f"⏰ Ожидание {e.seconds} секунд из-за ограничения API.")
        return "FLOOD_WAIT"
    except BadRequestError as e:
        print(f"❌ Ошибка запроса при присоединении к чату ({invite_link}): {e}")
        return None
    except Exception as e:
        print(f"❌ Ошибка при присоединении к приватному чату ({invite_link}): {e}")
        return None

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    sent_ids = load_sent_ids()
    new_ids = set()

    # Обработка обычных каналов
    for channel in CHANNELS:
        print(f"🔍 Проверяю {channel}...")
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
    for invite_link in PRIVATE_INVITE_LINKS:
        print(f"🔍 Проверяю приватный чат по ссылке: {invite_link}")
        chat_entity = await join_and_get_private_channel(client, invite_link)
        
        if chat_entity == "FLOOD_WAIT":
            continue
        if not chat_entity:
            continue

        try:
            messages = await client.get_messages(chat_entity, limit=20)
            if not messages:
                print(f"⚠️ Нет сообщений в приватном чате {chat_entity.title}.")
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
                    print(f"📩 Отправляю из приватного чата в группу: {original_text[:100]}...")
                    await client.send_message(GROUP_USERNAME, original_text)
                    new_ids.add(composite_id)
        except FloodWaitError as e:
            print(f"⏰ Ожидание {e.seconds} секунд из-за ограничения API.")
        except UserNotParticipantError:
            print(f"❌ Бот не является участником приватного чата {chat_entity.title}.")
        except ChatAdminRequiredError:
            print(f"❌ Недостаточно прав для чтения сообщений в приватном чате {chat_entity.title}.")
        except Exception as e:
            print(f"❌ Ошибка при работе с приватным чатом {chat_entity.title}: {e}")

    sent_ids.update(new_ids)
    save_sent_ids(sent_ids)
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
