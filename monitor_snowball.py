import os
import json
import asyncio
from telethon import TelegramClient
from playwright.async_api import async_playwright
from datetime import datetime, timezone

PHONE = os.getenv("PHONE")
API_ID = int(os.getenv("API_ID"))
API_HASH = os.getenv("API_HASH")
CHAT_ID = "me"

PORTFOLIOS = {
    "Купонный Концентрат 💸": "qzuscipxtn",
    "Другой портфель": "ukbrjaxjfg"
}

async def get_transactions_with_playwright(portfolio_id):
    url = f"https://snowball-income.com/public/portfolios/{portfolio_id}#transactions"
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        await page.wait_for_timeout(5000)

        table_selector = "table"
        try:
            await page.wait_for_selector(table_selector, timeout=30000)
        except Exception:
            await browser.close()
            return []

        rows = await page.query_selector_all(f"{table_selector} tbody tr")
        if not rows:
            rows = await page.query_selector_all(f"{table_selector} tr")

        transactions = []

        for row in rows:
            cells = await row.query_selector_all("td")
            texts = []
            for cell in cells:
                text = await cell.inner_text()
                texts.append(text.strip())

            if len(texts) >= 4 and texts[0] and texts[1]:
                operation = texts[0]
                ticker = texts[1]
                date = texts[2] if len(texts) > 2 else ""
                key = f"{date}|{ticker}|{operation}"
                raw = " | ".join(texts[:6])
                transactions.append({"key": key, "raw": raw})

        await browser.close()
        return transactions

def load_saved_state(portfolio_id):
    filename = f"snowball_{portfolio_id}_transactions.json"
    if os.path.exists(filename):
        with open(filename, 'r', encoding='utf-8') as f:
            return set(json.load(f))
    return set()

def save_state(portfolio_id, keys):
    filename = f"snowball_{portfolio_id}_transactions.json"
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(list(keys)[-100:], f)  # сохраняем последние 100 записей

async def main():
    print(f"🕒 Запуск: {datetime.now(timezone.utc).isoformat()}")
    client = TelegramClient('session', API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("❌ Сессия не найдена. Загрузите session.session файл в репозиторий.")
        return

    try:
        for name, pid in PORTFOLIOS.items():
            print(f"🔍 Проверяю портфель: {name}")
            current = await get_transactions_with_playwright(pid)
            current_keys = {t['key'] for t in current}
            saved_keys = load_saved_state(pid)

            new_transactions = [t for t in current if t['key'] not in saved_keys]

            if new_transactions:
                message = f"🔔 **Новая сделка в Snowball!**\n\n📌 **{name}**\n\n"
                for t in new_transactions[:3]:
                    message += f"• {t['raw']}\n"
                await client.send_message(CHAT_ID, message, parse_mode='md')
                print(f"✅ Новых сделок в '{name}': {len(new_transactions)}")
            else:
                print(f"📭 Новых сделок в '{name}' нет")

            save_state(pid, current_keys)

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        await client.send_message(CHAT_ID, f"⚠️ Ошибка мониторинга Snowball:\n{str(e)}")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
