import pdfplumber
import re

def normalize_subqueue(text):
    text = text.upper()
    return "2" if "II" in text or "ІІ" in text else "1"

def extract_data_from_pdf(file_path):
    results = []
    current_queue = "0.0"
    current_context = "" # Тут зберігаємо останнє знайдене місто/село
    
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if not text: continue
            
            for line in text.split('\n'):
                line = line.strip()
                if not line: continue

                # 1. Визначаємо чергу
                q_match = re.search(r'(\d+)\s*черга', line, re.IGNORECASE)
                if q_match:
                    num = q_match.group(1)[-1]
                    sub = normalize_subqueue(line)
                    current_queue = f"{num}.{sub}"
                    continue

                # 2. Визначаємо МІСТО/СЕЛО (Контекст)
                # Шукаємо ключові слова: м., с., селище, філія
                city_match = re.search(r'(м\.|с\.|селище|філія)\s*([А-ЯІЄЇ][а-яієї\'\s]+)', line)
                if city_match:
                    # Очищаємо назву (напр. "Золотоніська філія" -> "Золотоноша")
                    city_name = city_match.group(0).replace('філія', '').replace('дільниця', '').strip()
                    if "Золотоні" in city_name: city_name = "Золотоноша"
                    current_context = city_name
                    continue

                # 3. Записуємо вулиці
                if current_queue != "0.0" and len(line) > 5:
                    if any(bad in line for bad in ["Сторінка", "Назва", "Перелік"]): continue
                    
                    # Склеюємо контекст міста з вулицею
                    full_address = f"{current_context} {line}".strip().replace('"', '')
                    results.append((current_queue, full_address))
                    
    return results