import os
import json
import asyncio
from telethon import TelegramClient
from playwright.async_api import async_playwright

# === Настройки ===
PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHAT_ID = "me"  # временно — замените на "+79509156095", когда всё заработает

URL = "https://snowball-income.com/public/portfolios/qzuscipxtn#transactions"
STATE_FILE = "snowball_transactions.json"

async def get_transactions_with_playwright():
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(URL, wait_until="networkidle")
        
        # Ждём появления таблицы со сделками (по заголовку "Операция")
        await page.wait_for_selector("table:has(th:text('Операция'))", timeout=20000)
        
        # Извлекаем все строки из tbody
        rows = await page.query_selector_all("table:has(th:text('Операция')) tbody tr")
        transactions = []
        
        for row in rows:
            cells = await row.query_selector_all("td")
            texts = []
            for cell in cells:
                text = await cell.inner_text()
                texts.append(text.strip())
            
            if len(texts) >= 8:
                operation = texts[0]      # Операция
                ticker = texts[1]         # Актив
                date = texts[2]           # Дата
                key = f"{date}|{ticker}|{operation}"
                raw = " | ".join(texts[:6])
                transactions.append({"key": key, "raw": raw})
        
        await browser.close()
        return transactions

def load_saved_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_state(keys):
    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(list(keys), f)

async def main():
    client = TelegramClient('session', API_ID, API_HASH)
    await client.start(phone=PHONE)

    try:
        current = await get_transactions_with_playwright()
        current_keys = {t['key'] for t in current}
        saved_keys = load_saved_state()

        new_transactions = [t for t in current if t['key'] not in saved_keys]

        if new_transactions:
            message = "🔔 **Новая сделка в Snowball!**\n\n"
            for t in new_transactions[:3]:
                message += f"• {t['raw']}\n"
            await client.send_message(CHAT_ID, message, parse_mode='md')
            print(f"✅ Новых сделок: {len(new_transactions)}")
        else:
            print("📭 Новых сделок нет")

        save_state(current_keys)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await client.send_message(CHAT_ID, f"⚠️ Ошибка мониторинга Snowball:\n{str(e)}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
