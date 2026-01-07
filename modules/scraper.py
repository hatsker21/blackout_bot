import requests
from bs4 import BeautifulSoup
import re
import config

def get_latest_schedule():
    try:
        response = requests.get(config.TG_CHANNEL_URL, headers=config.HEADERS, timeout=15)
        soup = BeautifulSoup(response.text, 'lxml')
        messages = soup.find_all('div', class_='tgme_widget_message_text')
        if not messages: return None
        
        for msg in reversed(messages):
            text = msg.get_text(separator=" ")
            # Шукаємо черги 1.1 - 6.2. 
            # Зупиняємося, коли бачимо наступний номер або слова "Перелік", "Зверніть"
            matches = re.findall(r'(\d\.\d)\s+([\d:,\s\-–—]+?)(?=\s+\d\.\d|Перелік|Зверніть|$)', text)
            
            if len(matches) >= 6:
                schedule = {q: h.strip().strip(',') for q, h in matches if len(h) > 5}
                return schedule
        return None
    except Exception as e:
        print(f"❌ Помилка скрепера: {e}")
        return None