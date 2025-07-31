import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode

# --- НАСТРОЙКИ ---
# Укажи путь к файлу с токеном.
TOKEN_FILE = "token.txt"

# Укажи свой числовой ID. Узнать можно у @userinfobot
OWNER_ID = 7485721661 

# Укажи ID чата для логов (ОБЯЗАТЕЛЬНО отрицательное число)
LOG_CHAT_ID = -1002765837683 # ВАЖНО: Замени на свой ID, он должен быть отрицательным!

# --- КОНЕЦ НАСТРОЕК ---

# Настройка логирования для отладки
logging.basicConfig(level=logging.INFO)

# Загрузка токена из файла
try:
    with open(TOKEN_FILE, "r") as f:
        TOKEN = f.read().strip()
except FileNotFoundError:
    logging.critical(f"Файл {TOKEN_FILE} не найден. Создайте его и поместите туда токен бота.")
    exit()

# Инициализация бота и диспетчера
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

# Временное хранилище для сопоставления "пользователь <-> топик"
user_topic_map = {}


# --- ОБРАБОТЧИКИ СООБЩЕНИЙ ---

# 1. Обработчик команды /start
@dp.message(CommandStart())
async def handle_start(message: types.Message):
    """Отвечает на команду /start."""
    await message.answer(
        "Привет! 👋\n"
        "Я бот для обратной связи. Просто напиши мне свой вопрос, и я передам его администратору."
    )

# 2. Обработчик сообщений от владельца в группе логов
@dp.message(F.chat.id == LOG_CHAT_ID, F.from_user.id == OWNER_ID)
async def handle_admin_reply(message: types.Message):
    """
    Пересылает ответ владельца из топика в личный чат с пользователем.
    """
    if not message.reply_to_message or not message.message_thread_id:
        return

    topic_id = message.message_thread_id
    user_id_to_reply = None
    
    for user_id, t_id in user_topic_map.items():
        if t_id == topic_id:
            user_id_to_reply = user_id
            break
            
    if user_id_to_reply:
        try:
            await bot.send_message(user_id_to_reply, message.text)
            logging.info(f"Отправлен ответ от {OWNER_ID} пользователю {user_id_to_reply}")
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение пользователю {user_id_to_reply}: {e}")
            await message.reply(f"❌ Не удалось отправить ответ пользователю {user_id_to_reply}.\nВозможно, он заблокировал бота.")
    else:
        logging.warning(f"Не найден пользователь для топика {topic_id}")
        await message.reply("⚠️ Не могу найти, какому пользователю ответить. Возможно, бот перезапускался.")


# 3. Обработчик всех остальных сообщений от пользователей в личном чате
@dp.message(F.chat.type == "private")
async def handle_user_message(message: types.Message):
    """
    Обрабатывает сообщение от пользователя, создает топик (если нужно) и пересылает сообщение.
    """
    user_id = message.from_user.id
    
    if user_id == OWNER_ID:
        await message.answer("Вы являетесь владельцем этого бота. Отвечать пользователям нужно в группе логов.")
        return

    topic_id = user_topic_map.get(user_id)

    if topic_id is None:
        try:
            topic_name = f"Обращение от {message.from_user.full_name} (ID: {user_id})"
            created_topic = await bot.create_forum_topic(
                chat_id=LOG_CHAT_ID,
                name=topic_name
            )
            topic_id = created_topic.message_thread_id
            user_topic_map[user_id] = topic_id
            logging.info(f"Создан новый топик {topic_id} для пользователя {user_id}")
            
            user_info = (
                f"<b>Новое обращение!</b>\n"
                f"Пользователь: {message.from_user.full_name}\n"
                f"Username: @{message.from_user.username if message.from_user.username else 'не указан'}\n"
                f"ID: <code>{user_id}</code>"
            )
            await bot.send_message(LOG_CHAT_ID, user_info, message_thread_id=topic_id)

        except Exception as e:
            logging.error(f"Не удалось создать топик для чата {LOG_CHAT_ID}: {e}")
            await message.answer("Произошла ошибка при отправке вашего сообщения. Пожалуйста, попробуйте позже.")
            return

    try:
        await message.forward(chat_id=LOG_CHAT_ID, message_thread_id=topic_id)
        # Строка ниже удалена, чтобы не отправлять подтверждение пользователю
        # await message.answer("✅ Ваше сообщение отправлено администратору. Ожидайте ответа.")
    except Exception as e:
        logging.error(f"Не удалось переслать сообщение в топик {topic_id}: {e}")
        await message.answer("Произошла ошибка при отправке вашего сообщения. Пожалуйста, попробуйте позже.")


# --- ЗАПУСК БОТА ---

async def main():
    """Главная функция для запуска бота."""
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())