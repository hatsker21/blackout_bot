import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
MONO_TOKEN = os.getenv("MONO_TOKEN")
MONO_ACCOUNT_ID = os.getenv("MONO_ACCOUNT_ID")
ADMIN_ID = int(os.getenv("ADMIN_ID", 0))

# Папки та шляхи
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "data", "bot_database.db")
PDF_DIR = os.path.join(BASE_DIR, "data")

# Налаштування для скрепера
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
TG_CHANNEL_URL = "https://t.me/s/pat_cherkasyoblenergo"