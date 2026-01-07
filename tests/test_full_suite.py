import pytest
import asyncio
from datetime import datetime, timedelta
from modules.database import Database

# Налаштовуємо асинхронний режим для pytest
@pytest.mark.asyncio
async def test_blackout_bot_suite():
    db = Database()
    test_id = 12345
    
    # 1. ТЕСТ: Реєстрація користувача (Positive)
    await db.set_subscription(test_id, "Черга 3")
    user = await db.get_user(test_id)
    assert user is not None
    assert user['queue_id'] == "Черга 3"

    # 2. ТЕСТ: Неіснуючий користувач (Negative/Edge Case)
    non_existent = await db.get_user(999999)
    assert non_existent is None

    # 3. ТЕСТ: Нарахування Premium (Business Logic)
    await db.set_premium(test_id, days=30)
    user_prem = await db.get_user(test_id)
    assert user_prem['is_premium'] == 1
    assert user_prem['premium_until'] is not None

    # 4. ТЕСТ: Валідація дати Premium (Data Integrity)
    # Перевіряємо формат дати DD.MM.YYYY, як у твоїй базі
    try:
        datetime.strptime(user_prem['premium_until'], "%d.%m.%Y")
        date_valid = True
    except ValueError:
        date_valid = False
    assert date_valid is True

    # 5. ТЕСТ: Оновлення графіка (Integration)
    new_hours = "00-04, 12-16"
    await db.update_schedule("Черга 3", new_hours)
    saved_hours = await db.get_schedule("Черга 3")
    assert saved_hours == new_hours

    # 6. ТЕСТ: Очищення старих графіків (Maintenance)
    await db.clear_schedules()
    empty_schedule = await db.get_schedule("Черга 3")
    assert empty_schedule == "Графік поки відсутній"

    # 7. ТЕСТ: Пошук вулиці (Search Logic)
    # Перевіряємо, чи працює логіка пошуку з твого database.py
    results = await db.search_street("Головна")
    assert isinstance(results, dict)

    # 8. ТЕСТ: Збереження часу актуальності (UX Sync)
    now_str = datetime.now().strftime("%H:%M %d.%m")
    await db.set_last_update(now_str)
    last_upd = await db.get_last_update()
    assert last_upd == now_str

    # 9. ТЕСТ: Оновлення налаштувань користувача (Settings)
    await db.update_user_setting(test_id, "notify_time", 15)
    updated_user = await db.get_user(test_id)
    assert updated_user['notify_time'] == 15

    # 10. ТЕСТ: Відкликання Premium (Edge Case)
    await db.revoke_premium(test_id)
    final_user = await db.get_user(test_id)
    assert final_user['is_premium'] == 0

    print("\n🚀 ВСІ 10 ТЕСТІВ ПРОЙДЕНО УСПІШНО!")