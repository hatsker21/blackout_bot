# 🛡️ Blackout Bot: Outage Schedule Monitoring System

A professional Telegram bot designed to automate tracking and notifying users about scheduled power outages. The system integrates web scraping of official power utility resources, data visualization, and a premium subscription model.

## 🚀 Features
* **Automated Monitoring**: Continuous tracking of schedule updates on official Oblenergo websites.
* **Smart Notifications**: Proactive alerts 30 minutes before a blackout and notifications upon power restoration.
* **Data Visualization**: Generates personalized image-based schedules for better UX using the Pillow library.
* **Premium System**: Automated subscription management with expiration control.
* **Admin Dashboard**: Tools for real-time statistics, privilege management, and database maintenance.
* **Automated Testing**: Built-in integration tests for database and business logic validation.

## 🛠 Tech Stack
* **Language**: Python 3.11
* **Framework**: `aiogram 3.x` (Asynchronous Telegram API framework)
* **Database**: `aiosqlite` (Asynchronous SQLite wrapper)
* **Task Scheduling**: `APScheduler` (Managing background updates and cleanup tasks)
* **DevOps**: `Docker` & `Docker Compose` (Containerization for stable deployment)
* **Testing**: `pytest` & `pytest-asyncio`

## 📂 Project Structure
The project follows a modular architecture to ensure maintainability:
```text
├── main.py              # Entry point: initializes bot and scheduler
├── bot.py               # Command handlers and message logic
├── config.py            # Environment configuration (Token management)
├── modules/             # Isolated functional modules
│   ├── database.py      # Database abstraction layer (SQLite)
│   ├── scraper.py       # Web scraping logic
│   ├── visualizer.py    # Image generation logic (Pillow)
│   └── pdf_parser.py    # Official PDF document processing
├── tests/               # Automated test suite (Pytest)
├── data/                # Persistent storage for DB and temporary files
├── Dockerfile           # Docker image build instructions
└── requirements.txt     # Project dependencies
⚙️ Setup & Installation
1. Local Deployment
Clone the repository:

git clone [https://github.com/hatsker21/blackout_bot.git](https://github.com/hatsker21/blackout_bot.git)
cd blackout_bot
Install dependencies:


pip install -r requirements.txt
Configuration: Create a .env file (refer to config.py) and add your BOT_TOKEN.

Run tests (Recommended):


python -m pytest tests/test_full_suite.py
Start the bot:


python main.py
2. Docker Deployment (Recommended for Servers)

docker-compose up -d --build
📊 Database Schema
The system uses a relational model optimized for the Third Normal Form (3NF). The users table includes:

user_id: Unique Telegram identifier (Primary Key).

is_premium: Subscription status (Boolean 0/1).

premium_until: Expiration date (Format: DD.MM.YYYY).

queue_id: The specific outage group assigned to the user.
