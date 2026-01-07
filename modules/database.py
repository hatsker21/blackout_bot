import aiosqlite
import config
import os
from datetime import datetime, timedelta

class Database:
    def __init__(self):
        self.path = os.path.abspath(config.DB_PATH)
    
    async def get_premium_users(self):
        """Отримує список усіх активних преміум-користувачів."""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            today = datetime.now().strftime("%d.%m.%Y")
            # Вибираємо користувачів, у яких активований преміум
            async with db.execute(
                "SELECT * FROM users WHERE is_premium = 1"
            ) as cursor:
                return await cursor.fetchall()

    async def setup(self):
        """Ініціалізація всіх таблиць бази даних."""
        async with aiosqlite.connect(self.path) as db:
            await db.execute('CREATE TABLE IF NOT EXISTS address_map (queue_id TEXT, city_street TEXT)')
            await db.execute('CREATE TABLE IF NOT EXISTS schedules (queue_id TEXT PRIMARY KEY, hours TEXT)')
            await db.execute('CREATE TABLE IF NOT EXISTS settings (key TEXT PRIMARY KEY, value TEXT)')
            await db.execute('''
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY, 
                    queue_id TEXT, 
                    is_premium INTEGER DEFAULT 0,
                    notify_time INTEGER DEFAULT 30,
                    notify_return INTEGER DEFAULT 1,
                    premium_until TEXT,
                    last_notified TEXT DEFAULT ''
                )
            ''')
            await db.commit()
    
    async def clear_schedules(self):
        """Очищає графіки перед оновленням (виправляє твою помилку)."""
        async with aiosqlite.connect(self.path) as db_conn:
            await db_conn.execute("DELETE FROM schedules")
            await db_conn.commit()

    async def fix_database_schema(self):
        """Метод для ручного оновлення структури бази."""
        async with aiosqlite.connect(self.path) as db:
            try:
                await db.execute("ALTER TABLE users ADD COLUMN premium_until TEXT")
                await db.commit()
                return True
            except Exception as e:
                if "duplicate column name" in str(e).lower(): return "exists"
                raise e

    async def get_stats(self):
        """Статистика для адмін-панелі."""
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total = (await cursor.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM users WHERE is_premium = 1") as cursor:
                premium = (await cursor.fetchone())[0]
            return total, premium

    async def get_user(self, user_id):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

    async def set_premium(self, user_id, days=30):
        expiry = (datetime.now() + timedelta(days=days)).strftime("%d.%m.%Y")
        async with aiosqlite.connect(self.path) as db:
            await db.execute("""
                INSERT INTO users (user_id, is_premium, premium_until) 
                VALUES (?, 1, ?) ON CONFLICT(user_id) 
                DO UPDATE SET is_premium=1, premium_until=?
            """, (user_id, expiry, expiry))
            await db.commit()
        return expiry

    async def revoke_premium(self, user_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?", (user_id,))
            await db.commit()

    async def check_and_revoke_expired_premium(self):
        """Автоматичне зняття Premium."""
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT user_id, premium_until FROM users WHERE is_premium = 1") as cursor:
                users = await cursor.fetchall()
            count = 0
            now = datetime.now()
            for user in users:
                until_str = user['premium_until']
                if until_str and until_str != 'невизначено':
                    try:
                        expiry_date = datetime.strptime(until_str, "%d.%m.%Y")
                        if expiry_date < now:
                            await db.execute("UPDATE users SET is_premium = 0, premium_until = NULL WHERE user_id = ?", (user['user_id'],))
                            count += 1
                    except: continue
            if count > 0: await db.commit()
            return count

    async def get_all_users(self):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT user_id FROM users") as cursor:
                rows = await cursor.fetchall()
                return [row[0] for row in rows]

    async def update_schedule(self, queue_id, hours):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR REPLACE INTO schedules (queue_id, hours) VALUES (?, ?)", (queue_id, hours))
            await db.commit()

    async def get_schedule(self, queue_id):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT hours FROM schedules WHERE queue_id = ?", (queue_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else "Графік поки відсутній"

    async def set_last_update(self, ts):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT OR REPLACE INTO settings (key, value) VALUES ('last_update', ?)", (ts,))
            await db.commit()

    async def get_last_update(self):
        async with aiosqlite.connect(self.path) as db:
            async with db.execute("SELECT value FROM settings WHERE key = 'last_update'") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else "невідомо"

    async def set_subscription(self, user_id, queue_id):
        async with aiosqlite.connect(self.path) as db:
            await db.execute("INSERT INTO users (user_id, queue_id) VALUES (?, ?) ON CONFLICT(user_id) DO UPDATE SET queue_id=excluded.queue_id", (user_id, queue_id))
            await db.commit()

    async def update_user_setting(self, user_id, col, val):
        async with aiosqlite.connect(self.path) as db:
            await db.execute(f"UPDATE users SET {col} = ? WHERE user_id = ?", (val, user_id))
            await db.commit()

    async def search_street(self, query):
        async with aiosqlite.connect(self.path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT queue_id, city_street FROM address_map") as cursor:
                rows = await cursor.fetchall()
            words = query.lower().replace(',', ' ').replace('.', ' ').split()
            if not words: return {}
            grouped = {}
            for r in rows:
                txt = r['city_street'].lower()
                if all(w in txt for w in words):
                    q = r['queue_id']; grouped.setdefault(q, [])
                    if r['city_street'] not in grouped[q]: grouped[q].append(r['city_street'])
            return grouped