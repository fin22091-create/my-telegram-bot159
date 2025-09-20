import requests
import logging
import os

# Настраиваем логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 🔁 Замени на URL своего Telegram-бота на Render!
BOT_WEBHOOK_URL = 'https://my-telegram-bot159-1.onrender.com'

# 🔑 Замени на токен твоего бота (можно временно вставить, но лучше вынести в переменную окружения)
BOT_TOKEN = "8055975981:AAHo-Tv7XoWqXqWge_-tkgbYSAgupF0vm0U"

# 🆔 Замени на свой Telegram ID (узнать можно у @userinfobot)
YOUR_TELEGRAM_ID = 483422005  # ← замени на свой!

# Функция отправки уведомления в Telegram
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    data = {
        "chat_id": YOUR_TELEGRAM_ID,
        "text": text,
        "parse_mode": "Markdown"
    }
    try:
        response = requests.post(url, data=data, timeout=5)
        if response.status_code == 200:
            logger.info("✅ Уведомление в Telegram отправлено")
        else:
            logger.error(f"❌ Ошибка отправки в Telegram: {response.text}")
    except Exception as e:
        logger.error(f"❌ Исключение при отправке в Telegram: {e}")

# Функция пробуждения бота
def wake_up_bot():
    try:
        response = requests.get(BOT_WEBHOOK_URL, timeout=5)
        status = response.status_code
        logger.info(f"✅ Пробуждение успешно! Статус: {status}")

        # Отправляем уведомление в Telegram
        send_telegram_message(f"⏰ *Пробуждение бота*\nСтатус: `{status}`\nВремя: {response.headers.get('Date', 'неизвестно')}")
    except Exception as e:
        error_msg = f"❌ *Ошибка пробуждения*\n`{str(e)}`"
        logger.error(f"❌ Ошибка при пробуждении: {e}")
        send_telegram_message(error_msg)

if __name__ == "__main__":
    logger.info("⏰ Запуск пробуждения бота...")
    wake_up_bot()
