import asyncio
import logging
from aiogram import Router, F, types, Bot
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder
from aiogram.exceptions import TelegramBadRequest, TelegramForbiddenError
from aiogram.types import BufferedInputFile, KeyboardButton, ReplyKeyboardMarkup
from datetime import datetime

from modules.database import Database
from modules.utils import get_current_status
from modules.visualizer import generate_schedule_image 

router = Router()
db = Database()

# --- НАЛАШТУВАННЯ ---
ADMIN_ID = 1052766611 # Твій ID
BTN_MENU = "🏠 Головне меню"
BTN_PROFILE = "👤 Мій профіль"
BTN_FEEDBACK = "✍️ Написати розробнику"

# --- КЛАВІАТУРИ ---

def get_reply_keyboard():
    """Кнопки під полем вводу."""
    builder = ReplyKeyboardBuilder()
    builder.row(KeyboardButton(text=BTN_MENU), KeyboardButton(text=BTN_PROFILE))
    builder.row(KeyboardButton(text=BTN_FEEDBACK))
    return builder.as_markup(resize_keyboard=True)

def get_main_keyboard():
    """Меню черг."""
    builder = InlineKeyboardBuilder()
    queues = ["1.1", "1.2", "2.1", "2.2", "3.1", "3.2", "4.1", "4.2", "5.1", "5.2", "6.1", "6.2"]
    for q in queues:
        builder.button(text=q, callback_data=f"show_q_{q}")
    
    builder.button(text="🔄 Актуальність", callback_data="app_check_rel")
    builder.button(text="👤 Мій профіль", callback_data="open_profile")
    builder.button(text="✍️ Написати адміну", url="https://t.me/akarumey29")
    
    builder.adjust(2, 2, 2, 2, 2, 2, 1, 1, 1)
    return builder.as_markup()

# --- АДМІН-КОМАНДИ ---

@router.message(Command("db_fix"))
async def cmd_db_fix(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    try:
        # Викликаємо новий метод, який ми додали в Database
        result = await db.fix_database_schema()
        if result == "exists":
            await message.answer("ℹ️ Колонка `premium_until` вже існує.")
        else:
            await message.answer("✅ Базу успішно оновлено! Поле `premium_until` додано.")
    except Exception as e:
        await message.answer(f"❌ Помилка при фіксі: {e}")

@router.message(Command("stats"))
async def cmd_stats(message: types.Message):
    if message.from_user.id != ADMIN_ID: return
    total, premium = await db.get_stats()
    text = (
        "📊 **Статистика проекту**\n\n"
        f"👥 Користувачів: **{total}**\n"
        f"💎 Premium: **{premium}**\n\n"
        f"🇺🇦 На ЗСУ (10%): ~**{premium * 5} грн**"
    )
    await message.answer(text, parse_mode="Markdown")

@router.message(Command("broadcast"))
async def cmd_broadcast(message: types.Message, bot: Bot):
    if message.from_user.id != ADMIN_ID: return
    content = message.caption if message.photo else message.text.replace("/broadcast", "").strip()
    if not content and not message.photo:
        await message.answer("❌ Введіть текст.")
        return
    users = await db.get_all_users()
    await message.answer(f"🚀 Розсилка на {len(users)} людей...")
    count = 0
    for uid in users:
        try:
            if message.photo: await bot.send_photo(uid, message.photo[-1].file_id, caption=content, parse_mode="Markdown")
            else: await bot.send_message(uid, content, parse_mode="Markdown")
            count += 1
            await asyncio.sleep(0.05)
        except: continue
    await message.answer(f"✅ Надіслано: {count}")

# ПРАВИЛЬНЕ РОЗМІЩЕННЯ КОМАНДИ ГРАНТ
@router.message(Command("grant_premium"))
async def cmd_grant(message: types.Message, bot: Bot):
    """Ручна активація Premium для користувача за його ID."""
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) > 1:
        try:
            tid = int(args[1])
            days = int(args[2]) if len(args) > 2 else 30
            exp = await db.set_premium(tid, days)
            await message.answer(f"✅ Premium активовано до {exp} для `{tid}`.")
            try: await bot.send_message(tid, "🎉 **Ваш Premium активовано!** 🇺🇦")
            except: pass
        except: await message.answer("❌ Формат: `/grant_premium ID дні`")

@router.message(Command("revoke_premium"))
async def cmd_revoke(message: types.Message):
    """Скасування Premium статусу адміністратором."""
    if message.from_user.id != ADMIN_ID: return
    args = message.text.split()
    if len(args) > 1:
        try:
            tid = int(args[1])
            await db.revoke_premium(tid)
            await message.answer(f"❌ Premium для `{tid}` скасовано.")
        except: await message.answer("❌ Помилка ID.")

# --- ГОЛОВНА ЛОГІКА ---

@router.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("💡 **Blackout Bot активовано!**", reply_markup=get_reply_keyboard(), parse_mode="Markdown")
    await message.answer("Оберіть чергу для перевірки:", reply_markup=get_main_keyboard())

# --- ЧЕРГИ ТА ГРАФІКИ ---

@router.callback_query(F.data.startswith("show_q_"))
async def view_queue(callback: types.CallbackQuery):
    """Відображення статусу черги та текстового графіка."""
    q_id = callback.data.replace("show_q_", "")
    last_update = await db.get_last_update()
    
    # 1. Логіка вибору тексту залежно від режиму (ГАВ або звичайний)
    if "⚠️ ГАВ" in last_update:
        status_text = "⚠️ **ЕКСТРЕНІ ВІДКЛЮЧЕННЯ (ГАВ)**"
        timer_text = "Планові графіки зараз не діють. Світло вимикають аварійно."
        hours_text = ""
    else:
        hours = await db.get_schedule(q_id)
        status_text, timer_text = get_current_status(hours)
        
        # Перевірка наявності даних у базі для виводу тексту
        if hours and len(str(hours)) > 5:
            hours_text = f"🕒 **Години відключень:**\n`{hours}`\n\n"
        else:
            hours_text = "❌ _Дані про години відсутні в базі._\n\n"

    # 2. Створення кнопок меню
    builder = InlineKeyboardBuilder()
    builder.button(text="📌 Обрати цю чергу", callback_data=f"save_sub_{q_id}")
    builder.button(text="🖼 Графік картинкою", callback_data=f"gen_img_{q_id}")
    builder.button(text="⬅️ Назад", callback_data="p_back_main")
    builder.adjust(1)
    
    # 3. Формування фінального тексту повідомлення
    full_msg = (
        f"📅 **Черга {q_id}**\n\n"
        f"{status_text}\n"
        f"{timer_text}\n\n"
        f"{hours_text}"
        f"🕓 Оновлено: {last_update}"
    )
    
    # 4. Редагування повідомлення з обробкою помилок
    try:
        await callback.message.edit_text(
            full_msg, 
            reply_markup=builder.as_markup(), 
            parse_mode="Markdown"
        )
    except Exception as e:
        # Ігноруємо помилку, якщо текст не змінився (щоб бот не "падав")
        if "message is not modified" not in str(e).lower():
            logging.error(f"Помилка виводу у view_queue: {e}")

@router.callback_query(F.data.startswith("gen_img_")) 
async def send_img(callback: types.CallbackQuery):
    q_id = callback.data.replace("gen_img_", "")
    hours = await db.get_schedule(q_id)
    await callback.answer("⌛️ Малюю...")
    photo_buf = generate_schedule_image(q_id, hours)
    await callback.message.answer_photo(
        photo=BufferedInputFile(photo_buf.read(), filename="s.png"), 
        caption=f"🖼 Графік для черги {q_id}"
    )

# --- ПРОФІЛЬ ТА НАЛАШТУВАННЯ ---

async def view_profile_logic(event):
    """Відображення профілю з виправленням для дати."""
    uid = event.from_user.id
    raw_user = await db.get_user(uid)
    
    # ПЕРЕТВОРЮЄМО В СЛОВНИК
    user = dict(raw_user) if raw_user else {}
    is_p = user.get('is_premium', 0)
    
    if is_p:
        status_str = "💎 Premium"
        # Читаємо поле, яке ти додав у database.py
        until = user.get('premium_until', 'невизначено')
        expiry_str = f"\n📅 Діє до: `{until}`"
    else:
        status_str = "🆓 Безкоштовно"
        expiry_str = ""
        
    txt = (
        f"👤 **Мій профіль**\n\n"
        f"🆔 ID: `{uid}`\n"
        f"Статус: {status_str}{expiry_str}\n"
        f"📍 Черга: {user.get('queue_id', 'Не обрана')}"
    )
    
    b = InlineKeyboardBuilder()
    if is_p: b.button(text="⚙️ Налаштування", callback_data="p_settings")
    else: b.button(text="☕️ Отримати Premium", callback_data="p_how_to")
    b.button(text="⬅️ Назад", callback_data="p_back_main")
    b.adjust(1)
    
    if isinstance(event, types.Message):
        await event.answer(txt, reply_markup=b.as_markup(), parse_mode="Markdown")
    else:
        try: await event.message.edit_text(txt, reply_markup=b.as_markup(), parse_mode="Markdown")
        except: await event.message.answer(txt, reply_markup=b.as_markup(), parse_mode="Markdown")
@router.message(F.text == BTN_PROFILE)
async def btn_profile(message: types.Message): await view_profile_logic(message)
# --- ОБРОБНИКИ ТЕКСТОВИХ КНОПОК (REPLY) ---

@router.message(F.text == BTN_MENU)
async def btn_main_menu_handler(message: types.Message):
    """Відкриває меню черг при натисканні на кнопку '🏠 Головне меню'."""
    await message.answer("Оберіть вашу чергу кнопкою:", reply_markup=get_main_keyboard())

@router.message(F.text == BTN_FEEDBACK)
async def btn_feedback_handler(message: types.Message):
    """Надсилає контакт адміна при натисканні на '✍️ Написати розробнику'."""
    await message.answer("З будь-яких питань або побажань щодо роботи бота пишіть адміну: @akarumey29")
@router.callback_query(F.data == "p_settings")
async def premium_settings(callback: types.CallbackQuery):
    user = await db.get_user(callback.from_user.id)
    builder = InlineKeyboardBuilder()
    for t in [30, 60, 120]:
        icon = "✅" if user['notify_time'] == t else "⏰"
        builder.button(text=f"{icon} за {t} хв", callback_data=f"set_t_{t}")
    ret_icon = "🔔" if user['notify_return'] else "🔕"
    builder.button(text=f"{ret_icon} Світло за 15 хв", callback_data="tgl_ret")
    builder.button(text="⬅️ Назад", callback_data="open_profile")
    builder.adjust(3, 1, 1)
    await callback.message.edit_text("⚙️ **Налаштування сповіщень**", reply_markup=builder.as_markup())

# --- ОБРОБНИКИ НАЛАШТУВАНЬ ПРЕМІУМУ ---

@router.callback_query(F.data.startswith("set_t_"))
async def set_time_handler(callback: types.CallbackQuery):
    """Оновлює час за який прийде сповіщення (30, 60 або 120 хв)."""
    new_time = int(callback.data.replace("set_t_", ""))
    await db.update_user_setting(callback.from_user.id, "notify_time", new_time)
    
    # Оновлюємо меню, щоб користувач побачив нову "галочку"
    await premium_settings(callback)

@router.callback_query(F.data == "tgl_ret")
async def toggle_return_handler(callback: types.CallbackQuery):
    """Вмикає або вимикає сповіщення про повернення світла за 15 хв."""
    user = await db.get_user(callback.from_user.id)
    # Змінюємо 1 на 0 або 0 на 1
    new_val = 0 if user['notify_return'] else 1
    await db.update_user_setting(callback.from_user.id, "notify_return", new_val)
    
    # Оновлюємо меню для відображення змін
    await premium_settings(callback)

# --- ПОШУК ТА СЕРВІС ---

@router.message()
async def search_handler(message: types.Message):
    if message.text in [BTN_MENU, BTN_PROFILE, BTN_FEEDBACK]: return
    results = await db.search_street(message.text)
    if not results:
        await message.answer("❌ Вулицю не знайдено."); return
    text = "📍 **Знайдені черги:**\n\n"
    for q_id, streets in results.items():
        text += f"🔹 **ЧЕРГА {q_id}**\n🏠 {streets[0]}...\n⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯⎯\n"
    await message.answer(text, parse_mode="Markdown")

@router.callback_query(F.data == "p_back_main")
async def back_to_main(callback: types.CallbackQuery):
    await callback.message.edit_text("Оберіть чергу для перевірки:", reply_markup=get_main_keyboard())

@router.callback_query(F.data.startswith("save_sub_"))
async def sub_save(callback: types.CallbackQuery):
    q = callback.data.replace("save_sub_", ""); await db.set_subscription(callback.from_user.id, q)
    await callback.answer(f"✅ Чергу {q} обрано!", show_alert=True)

# --- ОБРОБНИКИ КНОПОК ГОЛОВНОГО МЕНЮ ---

@router.callback_query(F.data == "open_profile")
async def cb_open_profile(callback: types.CallbackQuery):
    """Відкриває профіль користувача при натисканні на кнопку."""
    await view_profile_logic(callback)

@router.callback_query(F.data == "app_check_rel")
async def check_rel(callback: types.CallbackQuery):
    """Показує спливаюче вікно з часом останнього оновлення бази."""
    t = await db.get_last_update()
    await callback.answer(f"🕒 База актуальна на: {t}", show_alert=True)

@router.message(Command("db_fix"))
async def cmd_db_fix(message: types.Message):
    """Команда для оновлення структури бази даних (додавання колонки дати)."""
    if message.from_user.id != ADMIN_ID: return
    try:
        # Спроба додати колонку, якщо її ще немає
        await db.db.execute("ALTER TABLE users ADD COLUMN premium_until TEXT")
        await db.db.commit()
        await message.answer("✅ Базу даних успішно оновлено! Колонка `premium_until` додана.")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            await message.answer("ℹ️ Колонка вже існує в базі.")
        else:
            await message.answer(f"❌ Помилка: {e}")