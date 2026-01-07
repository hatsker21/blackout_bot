import sqlite3

conn = sqlite3.connect("data/bot_database.db")
cursor = conn.cursor()

# Шукаємо всі згадки "Шевченка"
cursor.execute("SELECT * FROM address_map WHERE city_street LIKE '%Шевченка%' LIMIT 20")
rows = cursor.fetchall()

print("--- ВМІСТ БАЗИ (ПЕРШІ 20 ЗАПИСІВ З ШЕВЧЕНКА) ---")
for r in rows:
    print(f"Черга {r[0]} | Текст: {r[1]}")
conn.close()