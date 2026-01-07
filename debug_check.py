import sqlite3

conn = sqlite3.connect("data/bot_database.db")
cursor = conn.cursor()

cursor.execute("SELECT COUNT(*) FROM address_map")
print(f"Загалом записів у базі: {cursor.fetchone()[0]}")

cursor.execute("SELECT * FROM address_map WHERE city_street LIKE '%Золотоноша%' LIMIT 5")
rows = cursor.fetchall()

if not rows:
    print("❌ ПОМИЛКА: У базі НЕМАЄ слова 'Золотоноша'. Парсер не спрацював.")
else:
    print("✅ Знайдено записи про Золотоношу:")
    for r in rows: print(f" - {r}")

conn.close()