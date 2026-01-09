import requests
import time
import logging
import config  

MONO_TOKEN = config.MONO_TOKEN
ACCOUNT_ID = config.MONO_ACCOUNT_ID

async def check_monobank_payments(bot, db):
    """Перевіряє транзакції по картці за останні 10 хвилин"""
    now = int(time.time())
    past = now - 600 
    
    # URL для звичайного рахунку такий самий, як і для Банки
    url = f"https://api.monobank.ua/personal/statement/{ACCOUNT_ID}/{past}/{now}"
    headers = {"X-Token": MONO_TOKEN}
    
    try:
        res = requests.get(url, headers=headers, timeout=10)
        if res.status_code != 200: return
        
        transactions = res.json()
        for tx in transactions:
            # Сума додатна, якщо це поповнення
            amount = tx['amount'] / 100 
            if amount <= 0: continue # Ігноруємо витрати (від'ємні суми)
            
            comment = tx.get('comment', '').strip()
            
            # Перевіряємо, чи є в коментарі ваш ID
            if comment.isdigit():
                user_id = int(comment)
                days = 0
                
                # Тарифи для тесту
                if amount >= 300: days = 9999
                elif amount >= 120: days = 93
                elif amount >= 50: days = 31
                # Тимчасово додамо 1 день за 1 грн для тесту
                elif amount >= 1: days = 1 
                
                if days > 0:
                    new_expiry = await db.add_premium_days(user_id, days)
                    try:
                        await bot.send_message(
                            user_id, 
                            f"✅ **Тестова оплата прийнята!**\n\nДодано днів: {days}. Premium діє до: **{new_expiry}**.",
                            parse_mode="Markdown"
                        )
                        logging.info(f"💰 Тестовий преміум для {user_id}")
                    except: pass
    except Exception as e:
        logging.error(f"💳 Помилка карткового API: {e}")