import telebot
from telebot import types
import sqlite3
import random
import os

# Вставь свой токен (из переменной окружения)
# обновление для теста3
import os
TOKEN = os.getenv('BOT_TOKEN')
if not TOKEN:
    TOKEN = '8055975981:AAHo-Tv7XoWqXqWge_-tkgbYSAgupF0vm0U'  

bot = telebot.TeleBot(TOKEN)

# 🗃️ Инициализация базы данных
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

# 💾 Сохраняем или обновляем игрока
def save_user(user_id, name):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT OR REPLACE INTO users (user_id, name, best_score)
        VALUES (?, ?, COALESCE((SELECT best_score FROM users WHERE user_id = ?), 0))
    ''', (user_id, name, user_id))
    conn.commit()
    conn.close()

# 🎯 Начать игру
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id
    name = message.from_user.first_name

    # Сохраняем пользователя
    save_user(user_id, name)

    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn1 = types.KeyboardButton("🎮 Начать игру")
    btn2 = types.KeyboardButton("🏆 Мой счёт")
    markup.add(btn1, btn2)

    bot.send_message(
        message.chat.id,
        f"Привет, {name}! Я загадаю число от 1 до 100 — попробуй угадать!\nЖми 'Начать игру'.",
        reply_markup=markup
    )

# 🎲 Начало игры
@bot.message_handler(func=lambda message: message.text == "🎮 Начать игру")
def start_game(message):
    user_id = message.from_user.id

    # Генерируем число и сохраняем в памяти бота
    bot.current_number = random.randint(1, 100)
    bot.attempts = 0

    bot.send_message(message.chat.id, "Я загадал число от 1 до 100. Какое число?")

    # Регистрируем следующий шаг — ожидаем число
    bot.register_next_step_handler(message, guess_number)

# 🔢 Обработка попытки
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

        # Обновляем рекорд, если лучше предыдущего
        update_score(user_id, bot.attempts)

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        btn1 = types.KeyboardButton("🎮 Сыграть ещё")
        btn2 = types.KeyboardButton("🏆 Мой счёт")
        markup.add(btn1, btn2)

        bot.send_message(message.chat.id, "Выбери действие:", reply_markup=markup)

# 📊 Обновляем счёт игрока
def update_score(user_id, attempts):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()

    # Получаем текущий рекорд
    cursor.execute('SELECT best_score FROM users WHERE user_id = ?', (user_id,))
    result = cursor.fetchone()
    current_best = result[0] if result and result[0] > 0 else None

    # Если рекорд не установлен или лучше — обновляем
    if not current_best or attempts < current_best:
        cursor.execute('UPDATE users SET best_score = ? WHERE user_id = ?', (attempts, user_id))

    conn.commit()
    conn.close()

# 🏆 Показать счёт
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

# 🔄 Обработчик "Сыграть ещё"
@bot.message_handler(func=lambda message: message.text == "🎮 Сыграть ещё")
def play_again(message):
    start_game(message)

# Запуск бота
if __name__ == '__main__':
    init_db()  # Инициализируем базу при запуске
    bot.infinity_polling(timeout=10, long_polling_timeout=5, skip_pending=True)
