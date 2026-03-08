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
        # Ждём только DOMContentLoaded, затем явно ждём появления таблицы
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)

        # Даём время на загрузку динамического контента
        await page.wait_for_timeout(5000)

        # Сохраняем скриншот для отладки
        await page.screenshot(path=f"snowball_{portfolio_id}_debug.png")
        print(f"📸 Скриншот сохранён: snowball_{portfolio_id}_debug.png")

        # Получаем HTML страницы для отладки
        html = await page.content()
        print(f"📄 Длина HTML: {len(html)} символов")

        # Проверяем наличие сообщения о пустоте разными способами
        empty_texts = ["Здесь пока что пусто", "Нет данных", "Пусто", "No transactions"]
        for empty_text in empty_texts:
            empty_elements = await page.query_selector_all(f"text={empty_text}")
            if empty_elements:
                print(f"⚠️ Найдено сообщение: '{empty_text}' (элементов: {len(empty_elements)})")

        # Пробуем разные селекторы для таблицы
        table_selector = "table"
        try:
            await page.wait_for_selector(table_selector, timeout=30000)
            print("✅ Таблица найдена")
        except Exception as e:
            print(f"⚠️ Таблица не найдена: {e}")
            await browser.close()
            return []

        # Получаем все строки таблицы
        rows = await page.query_selector_all(f"{table_selector} tbody tr")
        if not rows:
            rows = await page.query_selector_all(f"{table_selector} tr")

        print(f"📊 Найдено строк в таблице: {len(rows)}")

        transactions = []

        for i, row in enumerate(rows):
            cells = await row.query_selector_all("td")
            texts = []
            for cell in cells:
                text = await cell.inner_text()
                texts.append(text.strip())

            print(f"   Строка {i}: {texts[:4]}...")  # Первые 4 ячейки для отладки

            if len(texts) >= 4 and texts[0] and texts[1]:
                operation = texts[0]
                ticker = texts[1]
                date = texts[2] if len(texts) > 2 else ""
                key = f"{date}|{ticker}|{operation}"
                raw = " | ".join(texts[:6])
                transactions.append({"key": key, "raw": raw})

        print(f"✅ Распарсено транзакций: {len(transactions)}")
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
