import os
import asyncio
import sqlite3
from modules.pdf_parser import extract_data_from_pdf
import config

def run_init():
    # 1. Створюємо з'єднання (синхронне для початкової ініціалізації зручніше)
    conn = sqlite3.connect(config.DB_PATH)
    cursor = conn.cursor()
    
    # Очищуємо стару таблицю, якщо вона була, щоб не було дублікатів
    cursor.execute("DROP TABLE IF EXISTS address_map")
    cursor.execute("CREATE TABLE address_map (queue_id TEXT, city_street TEXT)")
    
    # 2. Шукаємо всі PDF у папці data
    pdf_files = [f for f in os.listdir(config.PDF_DIR) if f.endswith('.pdf')]
    
    if not pdf_files:
        print(f"❌ Файлів не знайдено в {config.PDF_DIR}. Покладіть туди PDF!")
        return

    print(f"🚀 Починаємо обробку {len(pdf_files)} файлів...")

    for file_name in pdf_files:
        full_path = os.path.join(config.PDF_DIR, file_name)
        print(f"📄 Обробка: {file_name}...")
        
        data = extract_data_from_pdf(full_path)
        
        # 3. Записуємо пачкою в базу
        cursor.executemany("INSERT INTO address_map VALUES (?, ?)", data)
        conn.commit()
        print(f"✅ Додано {len(data)} записів.")

    conn.close()
    print("\n✨ База даних готова до роботи!")

if __name__ == "__main__":
    run_init()