from telethon import TelegramClient
import asyncio

# Ваши данные
api_id = 33866699
api_hash = "4dd360d47a5c8e5bdf986a38320ec554"
phone = "+79539723763"

client = TelegramClient('session', api_id, api_hash)

async def main():
    await client.start(phone=phone)
    print("✅ Сессия создана! Файл 'session.session' сохранён.")
    await client.disconnect()

asyncio.run(main())