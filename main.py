import asyncio
import logging
import sys
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import BotCommand
from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import config
import bot
from bot import router, db
import modules.scraper as scraper
import modules.utils as utils

# --- НАЛАШТУВАННЯ ІНТЕРФЕЙСУ ---

async def set_commands(bot_instance: Bot):
    """Встановлює меню команд."""
    commands = [
        BotCommand(command="start", description="🏠 Головне меню"),
        BotCommand(command="profile", description="👤 Мій профіль")
    ]
    try:
        await bot_instance.set_my_commands(commands)
    except Exception as e:
        logging.error(f"❌ Не вдалося встановити команди: {e}")

# --- ЛОГІКА МОНІТОРИНГУ ТА ОНОВЛЕНЬ ---

async def check_upd(bot_instance: Bot):
    """
    Виправлена логіка: тепер час актуальності оновлюється ЗАВЖДИ 
    після успішного звернення до сайту.
    """
    logging.info("⏳ Запуск планової перевірки оновлень...")
    data = scraper.get_latest_schedule() # Або scraper.get_all_queues() залежно від твого модуля
    
    if data == "EMERGENCY_MODE":
        logging.warning("⚠️ УВАГА: Введено графіки аварійних відключень (ГАВ)!")
        return

    if not data:
        logging.error("❌ Не вдалося отримати дані з сайту Обленерго.")
        return

    # --- ФІКС ЧАСУ (Психологія користувача) ---
    # Оновлюємо час останньої перевірки ВЖЕ ЗАРАЗ, бо ми успішно отримали дані.
    now_str = datetime.now().strftime("%H:%M %d.%m")
    await bot.db.set_last_update(now_str)
    logging.info(f"⏱ Час перевірки оновлено: {now_str}")

    # Перевірка на зміни вмісту
    has_changes = False
    for q_id, new_hours in data.items():
        old_hours = await bot.db.get_schedule(q_id)
        if str(new_hours).strip() != str(old_hours).strip():
            has_changes = True
            break 

    if not has_changes:
        logging.info("😴 Дані ідентичні базі. Повідомлення не надсилаємо.")
        return

    # Якщо зміни таки є — оновлюємо графіки
    await bot.db.clear_schedules()
    for q_id, hours in data.items():
        await bot.db.update_schedule(q_id, hours)
    
    logging.info(f"✅ ВИЯВЛЕНО ЗМІНИ ГРАФІКІВ. Базу синхронізовано.")

    # Розсилка для Premium
    try:
        premium_users = await bot.db.get_premium_users()
        for user in premium_users:
            try:
                await bot_instance.send_message(
                    user['user_id'], 
                    "🆕 **Опубліковано оновлений графік відключень!**\n\nБот автоматично оновив дані для вашої черги.",
                    parse_mode="Markdown"
                )
                await asyncio.sleep(0.05) # Захист від спам-флуду
            except TelegramForbiddenError:
                continue # Користувач заблокував бота
            except Exception:
                continue
    except AttributeError:
        logging.error("❌ ПОМИЛКА: Метод get_premium_users відсутній у database.py!")

# --- ПУШ-СПОВІЩЕННЯ ПРО ВІДКЛЮЧЕННЯ ---

async def run_notifications(bot_instance: Bot):
    """Персональні сповіщення за X хвилин до події."""
    try:
        users = await bot.db.get_premium_users()
    except AttributeError:
        logging.error("❌ AttributeError: Додайте get_premium_users у database.py!")
        return

    now = datetime.now()
    for user in users:
        if not user['queue_id']: continue
        
        hours = await bot.db.get_schedule(user['queue_id'])
        status, timer = utils.get_current_status(hours)
        
        try:
            if "**" in timer:
                event_time_str = timer.split("**")[-2]
                event_time = datetime.strptime(event_time_str, "%H:%M").replace(
                    year=now.year, month=now.month, day=now.day
                )
                
                diff = int((event_time - now).total_seconds() / 60)
                
                if "Наступне вимкнення" in timer and diff == user['notify_time']:
                    notification_key = f"off_{event_time_str}"
                    
                    if user['last_notified'] != notification_key:
                        await bot_instance.send_message(
                            user['user_id'], 
                            f"🚨 **УВАГА! Вимкнення за {diff} хв!**\nПочаток: **{event_time_str}**"
                        )
                        await bot.db.update_user_setting(user['user_id'], "last_notified", notification_key)
        except Exception:
            continue

# --- ГОЛОВНИЙ ЦИКЛ (З АНТИКРИЗОВИМ ЗАХИСТОМ) ---

async def main():
    logging.basicConfig(
        level=logging.INFO, 
        stream=sys.stdout, 
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    await bot.db.setup()
    bot_obj = Bot(token=config.BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(bot.router)
    
    await set_commands(bot_obj)

    scheduler = AsyncIOScheduler()
    scheduler.add_job(check_upd, 'interval', minutes=2, args=[bot_obj])
    scheduler.add_job(run_notifications, 'interval', minutes=1, args=[bot_obj])
    scheduler.start()

    # Перша перевірка при старті
    await check_upd(bot_obj) 
    
    logging.info("🚀 БОТ ЗАПУЩЕНИЙ. Очікування повідомлень...")
    
    while True:
        try:
            await dp.start_polling(bot_obj)
        except TelegramNetworkError:
            logging.error("📡 Помилка мережі Telegram. Перепідключення через 30 сек...")
            await asyncio.sleep(30)
        except Exception as e:
            logging.error(f"🧨 Критична помилка: {e}. Перезапуск...")
            await asyncio.sleep(10)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logging.info("🔌 Бот зупинений.")