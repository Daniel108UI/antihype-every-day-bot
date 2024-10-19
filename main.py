import random
import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import FSInputFile, Message
import db
from config import TOKEN, AUDIO_FILES

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

bot = Bot(token=TOKEN)
dp = Dispatcher()


# Функция для выбора случайного аудиофайла
def get_random_audio():
    if not AUDIO_FILES:
        logger.error("No audio files available.")
        return None
    selected_audio = random.choice(AUDIO_FILES)
    logger.info(f"Randomly selected audio file: {selected_audio}")
    return selected_audio


# Функция для генерации случайного времени в интервале
def get_random_time_in_interval(start_hour=10, start_minute=0, end_hour=21, end_minute=0):
    now = datetime.now()
    start_time = now.replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    end_time = now.replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)

    if now > end_time:
        logger.info("Current time is past the end of the interval. Scheduling for the next day.")
        start_time += timedelta(days=1)
        end_time += timedelta(days=1)

    random_time = start_time + timedelta(
        seconds=random.randint(0, int((end_time - start_time).total_seconds()))
    )
    return random_time


# Асинхронная функция для отправки случайного трека подписчику
async def send_random_audio(chat_id: int):
    try:
        # Получаем случайный трек
        audio_file = get_random_audio()
        if not audio_file:
            logger.error("No audio file selected.")
            return

        audio = FSInputFile(audio_file)

        # Логируем информацию о треке и времени отправки
        now = datetime.now()
        logger.info(f"Attempting to send audio '{audio_file}' to user {chat_id} at {now.strftime('%Y-%m-%d %H:%M:%S')}")

        # Отправляем аудиофайл
        await bot.send_audio(chat_id=chat_id, audio=audio)

        # Лог успешной отправки
        logger.info(f"Audio '{audio_file}' successfully sent to user {chat_id} at {now.strftime('%Y-%m-%d %H:%M:%S')}")
    except Exception as e:
        # Лог ошибки при отправке
        logger.error(f"Failed to send audio to {chat_id}: {e}")


# Функция для планирования отправок на каждый день
async def schedule_daily_sends():
    while True:
        now = datetime.now()

        # Генерация времени отправки для каждого подписчика в 9:00
        if now.hour == 9 and now.minute == 0:
            logger.info("Generating random times for subscribers...")
            subscribers = db.get_subscribers()

            if not subscribers:
                logger.info("No subscribers found.")
                await asyncio.sleep(60)  # Ожидание перед повторной попыткой
                continue

            # Для каждого подписчика генерируем случайное время отправки
            for chat_id in subscribers:
                next_send_datetime = get_random_time_in_interval()

                # Логируем время отправки для подписчика
                logger.info(f"Next send time for user {chat_id} is {next_send_datetime.strftime('%Y-%m-%d %H:%M:%S')}")

                # Отправляем трек в назначенное время
                asyncio.create_task(send_audio_at_time(chat_id, next_send_datetime))

        # Ждем 1 минуту перед следующей проверкой времени
        await asyncio.sleep(60)


# Функция для ожидания времени и отправки трека
async def send_audio_at_time(chat_id: int, send_time: datetime):
    now = datetime.now()
    time_until_next_send = (send_time - now).total_seconds()

    if time_until_next_send > 0:
        await asyncio.sleep(time_until_next_send)

    # Отправляем аудиофайл
    await send_random_audio(chat_id)


# Команда для добавления нового подписчика
@dp.message(Command(commands=['start']))
async def start_command(message: Message):
    chat_id = message.chat.id
    db.add_subscriber(chat_id)
    await message.answer('Ты подписан! Теперь тебе будут приходить треки Антихайпа каждый день.')
    logger.info(f"New subscriber added: {chat_id}")


async def main():
    logger.info('Starting bot...')
    db.create_table()

    # Запускаем планирование отправки треков для всех подписчиков
    asyncio.create_task(schedule_daily_sends())

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())
