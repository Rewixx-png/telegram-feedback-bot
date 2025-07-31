import aiosqlite

DB_PATH = "bot_data.db"

async def init_db():
    """Инициализация базы: создаём таблицу, если её ещё нет."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS topics (
                user_id   INTEGER PRIMARY KEY,
                topic_id  INTEGER NOT NULL
            )
        """)
        await db.commit()

async def get_topic_id(user_id: int) -> int | None:
    """Получаем topic_id по user_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT topic_id FROM topics WHERE user_id = ?", (user_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None

async def set_topic_id(user_id: int, topic_id: int):
    """Сохраняем или обновляем соответствие."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO topics(user_id, topic_id)
            VALUES(?, ?)
            ON CONFLICT(user_id) DO UPDATE SET topic_id=excluded.topic_id
        """, (user_id, topic_id))
        await db.commit()

async def find_user_by_topic(topic_id: int) -> int | None:
    """Ищем user_id по topic_id."""
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT user_id FROM topics WHERE topic_id = ?", (topic_id,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None