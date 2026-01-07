import os

# 1. Вставте сюди свій токен
BOT_TOKEN = "8410107814:AAFDXhaFwvvHUKpA6anMc7GRvwByLxD81K0"

# 2. Налаштування папок (не змінюйте, якщо структура папок як ми домовлялися)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "bot_database.db")
PDF_DIR = os.path.join(BASE_DIR, "data")

# 3. Налаштування для скрепера (щоб Telegram нас не заблокував)
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TG_CHANNEL_URL = "https://t.me/s/pat_cherkasyoblenergo"

