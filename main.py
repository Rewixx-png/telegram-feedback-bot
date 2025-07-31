import asyncio
import logging

from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart

from database import init_db, get_topic_id, set_topic_id, find_user_by_topic

# --- НАСТРОЙКИ ---
TOKEN_FILE = "token.txt"
OWNER_ID    = 7485721661
LOG_CHAT_ID = -1002765837683
# --- КОНЕЦ НАСТРОЕК ---

logging.basicConfig(level=logging.INFO)

# Загружаем токен
try:
    with open(TOKEN_FILE, "r") as f:
        TOKEN = f.read().strip()
except FileNotFoundError:
    logging.critical(f"Файл {TOKEN_FILE} не найден. Поместите в него токен бота.")
    exit()

bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp  = Dispatcher()

@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await message.answer(
        "Привет! 👋\n"
        "Я бот для обратной связи. Просто напиши мне свой вопрос."
    )

@dp.message(F.chat.id == LOG_CHAT_ID, F.from_user.id == OWNER_ID)
async def handle_admin_reply(message: types.Message):
    if not message.reply_to_message or not message.message_thread_id:
        return

    topic_id = message.message_thread_id
    user_id_to_reply = await find_user_by_topic(topic_id)

    if not user_id_to_reply:
        await message.reply("⚠️ Не могу найти, какому пользователю ответить.")
        return

    try:
        if message.text:
            await bot.send_message(chat_id=user_id_to_reply, text=message.text)
        else:
            await bot.copy_message(
                chat_id=user_id_to_reply,
                from_chat_id=LOG_CHAT_ID,
                message_id=message.message_id
            )
        logging.info(f"Ответ владельца переслан пользователю {user_id_to_reply}")

    except Exception as e:
        logging.error(f"Ошибка при отправке ответу: {e}")
        await message.reply(
            "❌ Не удалось отправить ответ. Возможно, пользователь заблокировал бота."
        )

@dp.message(F.chat.type == "private")
async def handle_user_message(message: types.Message):
    user_id = message.from_user.id

    if user_id == OWNER_ID:
        await message.answer(
            "Вы владелец. Отвечайте в группе логов."
        )
        return

    # Получаем или создаём topic
    topic_id = await get_topic_id(user_id)
    if topic_id is None:
        try:
            topic_name = f"Обращение от {message.from_user.full_name} (ID: {user_id})"
            created = await bot.create_forum_topic(
                chat_id=LOG_CHAT_ID,
                name=topic_name
            )
            topic_id = created.message_thread_id
            await set_topic_id(user_id, topic_id)
            logging.info(f"Создан топик {topic_id} для {user_id}")

            info = (
                f"<b>Новое обращение!</b>\n"
                f"Пользователь: {message.from_user.full_name}\n"
                f"ID: <code>{user_id}</code>"
            )
            await bot.send_message(
                chat_id=LOG_CHAT_ID,
                text=info,
                message_thread_id=topic_id
            )
        except Exception as e:
            logging.error(f"Не создал топик: {e}")
            await message.answer(
                "❌ Ошибка при отправке. Попробуйте позже."
            )
            return

    # Пересылаем любое содержимое пользователя в группу
    try:
        await message.forward(
            chat_id=LOG_CHAT_ID,
            message_thread_id=topic_id
        )
    except Exception as e:
        logging.error(f"Ошибка пересылки: {e}")
        await message.answer(
            "❌ Не удалось отправить. Попробуйте позже."
        )

async def main():
    await init_db()
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())