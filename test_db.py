import pytest
import asyncio
from modules.database import Database

@pytest.mark.asyncio
async def test_get_non_existent_user():
    # 1. Готуємо базу
    db = Database()
    
    # 2. Дія: пробуємо знайти юзера, якого точно немає (ID = 999)
    user = await db.get_user(999999999)
    
    # 3. Перевірка (Assertion): результат має бути None
    assert user is None
    print("\n✅ Тест пройдено: база правильно реагує на відсутнього юзера!")

if __name__ == "__main__":
    asyncio.run(test_get_non_existent_user())

@pytest.mark.asyncio
async def test_set_and_get_user():
    db = Database()
    test_id = 777
    test_queue = "Черга 1"
    
    # Дія: реєструємо юзера
    await db.set_subscription(test_id, test_queue)
    
    # Перевірка: дістаємо юзера
    user = await db.get_user(test_id)
    
    assert user is not None
    assert user['user_id'] == test_id
    assert user['queue_id'] == test_queue
    print(f"\n✅ Позитивний тест пройдено: Юзер {test_id} успішно створений та отриманий!")