import telebot
import os
import time
import threading
import random
import sqlite3
from flask import Flask
from telebot import types
import logging

# =======================
# 🔧 НАСТРОЙКИ
# =======================

TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    raise ValueError("❌ BOT_TOKEN не установлен. Добавь его в Environment Variables на Render.")

bot = telebot.TeleBot(TOKEN)

# =======================
# 🗃️ БАЗА ДАННЫХ
# =======================

def init_db():
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            name TEXT,
            best_score INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

def save_user(user_id, name):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, name, best_score)
        VALUES (?, ?, COALESCE((SELECT best_score FROM users WHERE user_id = ?), 0))
    ''', (user_id, name, user_id))
    conn.commit()
    conn.close()

def update_score(user_id, attempts):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT best_score FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    current_best = result[0] if result and result[0] > 0 else None
    if not current_best or attempts < current_best:
        cursor.execute('UPDATE users SET best_score = ? WHERE user_id = ?', (attempts, user_id))
    conn.commit()
    conn.close()

# =======================
# 🤖 ЛОГИКА БОТА
# =======================

@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    name = message.from_user.first_name
    save_user(user_id, name)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("🎮 Начать игру")
    btn2 = types.KeyboardButton("🏆 Мой счёт")
    btn3 = types.KeyboardButton("🏅 Топ-10")
    markup.add(btn1, btn2, btn3)

    bot.send_message(
        message.chat.id,
        f"Привет, {name}! Я загадаю число от 1 до 100 — попробуй угадать!\nЖми 'Начать игру'.",
        reply_markup=markup
    )

@bot.message_handler(func=lambda message: message.text == "🎮 Начать игру")
def start_game(message):
    user_id = message.from_user.id
    bot.current_number = random.randint(1, 100)
    bot.attempts = 0
    bot.send_message(message.chat.id, "Я загадал число от 1 до 100. Какое число?")
    bot.register_next_step_handler(message, guess_number)

def guess_number(message):
    user_id = message.from_user.id
    try:
        guess = int(message.text)
    except ValueError:
        bot.reply_to(message, "Пожалуйста, введи число!")
        bot.register_next_step_handler(message, guess_number)
        return

    bot.attempts += 1

    if guess < bot.current_number:
        bot.reply_to(message, "Больше! 📈")
        bot.register_next_step_handler(message, guess_number)
    elif guess > bot.current_number:
        bot.reply_to(message, "Меньше! 📉")
        bot.register_next_step_handler(message, guess_number)
    else:
        bot.reply_to(message, f"🎉 Поздравляю! Ты угадал за {bot.attempts} попыток!")
        update_score(user_id, bot.attempts)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn1 = types.KeyboardButton("🎮 Сыграть ещё")
        btn2 = types.KeyboardButton("🏆 Мой счёт")
        btn3 = types.KeyboardButton("🏅 Топ-10")
        markup.add(btn1, btn2, btn3)

        bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

@bot.message_handler(func=lambda message: message.text == "🏆 Мой счёт")
def show_score(message):
    user_id = message.from_user.id
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('SELECT best_score FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    conn.close()

    if result and result[0] > 0:
        bot.reply_to(message, f"🏆 Твой лучший результат: {result[0]} попыток")
    else:
        bot.reply_to(message, "Ты ещё не угадал число. Нажми 'Начать игру'!")

@bot.message_handler(func=lambda message: message.text == "🎮 Сыграть ещё")
def play_again(message):
    start_game(message)

@bot.message_handler(commands=['top'])
@bot.message_handler(func=lambda message: message.text == "🏅 Топ-10")
def show_top_players(message):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT name, best_score
        FROM users
        WHERE best_score > 0
        ORDER BY best_score ASC
        LIMIT 10
    ''')
    results = cursor.fetchall()
    conn.close()

    if not results:
        bot.reply_to(message, "Пока нет рекордов. Сыграй и установи свой!")
        return

    text = "🏆 *ТОП-10 ЛУЧШИХ ИГРОКОВ*\n\n"
    for i, (name, score) in enumerate(results, 1):
        text += f"{i}. {name} — {score} попыток\n"

    bot.reply_to(message, text, parse_mode="Markdown")

# =======================
# 🌐 ВЕБ-СЕРВЕР (чтобы Render не ругался)
# =======================

app = Flask(__name__)

@app.route('/')
def home():
    return "✅ Telegram Bot with Game is running! Port is open.", 200

@app.route('/health')
def health():
    return {"status": "ok", "message": "Game bot is alive"}, 200

# =======================
# 🚀 ЗАПУСК БОТА В ОТДЕЛЬНОМ ПОТОКЕ
# =======================

def run_bot():
    time.sleep(3)
    try:
        bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
    except Exception as e:
        logging.error(f"❌ Ошибка бота: {e}")

# =======================
# 📊 ЛОГИРОВАНИЕ
# =======================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# =======================
# ▶️ ЗАПУСК
# =======================

if __name__ == '__main__':
    init_db()  # Инициализируем базу
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    PORT = int(os.environ.get('PORT', 5000))
    logging.info(f"🌐 Запуск веб-сервера на порту {PORT}...")
    app.run(host='0.0.0.0', port=PORT)