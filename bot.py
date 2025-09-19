import telebot
from telebot import types
import json
import os

# Вставь свой токен
TOKEN = os.getenv('BOT_TOKEN')
bot = telebot.TeleBot(TOKEN)

# 📁 Файл для хранения данных пользователей
DATA_FILE = "user_data.json"

# 🗃️ Загружаем данные при запуске
if os.path.exists(DATA_FILE):
    with open(DATA_FILE, "r", encoding="utf-8") as f:
        user_data = json.load(f)
        # Конвертируем user_id из строки в int
        user_data = {int(k): v for k, v in user_data.items()}
else:
    user_data = {}  # { user_id: { "name": "Алексей", "color": "color_red" }, ... }

# 💾 Функция для сохранения данных в файл
def save_data():
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(user_data, f, ensure_ascii=False, indent=4)

# 🎯 Обработчик команды /start
@bot.message_handler(commands=['start'])
def send_welcome(message):
    user_id = message.from_user.id

    # Если имя уже есть — приветствуем по имени
    if user_id in user_data and user_data[user_id].get("name"):
        name = user_data[user_id]["name"]
        bot.reply_to(message, f"С возвращением, {name}! 😊\nНапиши /myname, чтобы изменить имя.")
    else:
        # Если имени нет — просим ввести
        msg = bot.reply_to(message, "Привет! 👋 Как тебя зовут?")
        bot.register_next_step_handler(msg, save_name)

# 📝 Функция сохранения имени
def save_name(message):
    user_id = message.from_user.id
    name = message.text.strip()

    # Инициализируем запись пользователя, если её нет
    if user_id not in user_data:
        user_data[user_id] = {}

    # Сохраняем имя
    user_data[user_id]["name"] = name
    save_data()  # 💾 Сохраняем в файл

    bot.reply_to(message, f"Приятно познакомиться, {name}! 😊\nТеперь я буду обращаться к тебе по имени.")

# 🧾 Команда /myname — показать или изменить имя
@bot.message_handler(commands=['myname'])
def handle_myname(message):
    user_id = message.from_user.id

    if user_id in user_data and user_data[user_id].get("name"):
        current_name = user_data[user_id]["name"]
        markup = types.InlineKeyboardMarkup()
        btn_change = types.InlineKeyboardButton("✏️ Изменить имя", callback_data="change_name")
        markup.add(btn_change)

        bot.reply_to(
            message,
            f"Твоё текущее имя: *{current_name}*",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    else:
        msg = bot.reply_to(message, "Ты ещё не указал своё имя. Как тебя зовут?")
        bot.register_next_step_handler(msg, save_name)

# 🔄 Обработчик инлайн-кнопки "Изменить имя"
@bot.callback_query_handler(func=lambda call: call.data == "change_name")
def change_name_request(call):
    bot.answer_callback_query(call.id)
    msg = bot.send_message(call.message.chat.id, "Введи новое имя:")
    bot.register_next_step_handler(msg, update_name)

# 🔄 Функция обновления имени
def update_name(message):
    user_id = message.from_user.id
    new_name = message.text.strip()

    user_data[user_id]["name"] = new_name
    save_data()

    bot.reply_to(message, f"Готово! Теперь я буду звать тебя: {new_name} 😊")

# 🎨 Добавим ещё выбор цвета (как в прошлом уроке) — чтобы показать, как хранить несколько данных
@bot.message_handler(commands=['color'])
def choose_color(message):
    markup = types.InlineKeyboardMarkup()
    btn1 = types.InlineKeyboardButton("🎨 Красный", callback_data="color_red")
    btn2 = types.InlineKeyboardButton("🌿 Зелёный", callback_data="color_green")
    btn3 = types.InlineKeyboardButton("💙 Синий", callback_data="color_blue")
    markup.add(btn1, btn2, btn3)

    bot.send_message(
        message.chat.id,
        "Выбери свой любимый цвет:",
        reply_markup=markup
    )

# 🎯 Обработчик выбора цвета
@bot.callback_query_handler(func=lambda call: call.data.startswith("color_"))
def handle_color_choice(call):
    user_id = call.from_user.id
    choice = call.data

    if user_id not in user_data:
        user_data[user_id] = {}

    user_data[user_id]["color"] = choice
    save_data()

    color_names = {
        "color_red": "Красный",
        "color_green": "Зелёный",
        "color_blue": "Синий"
    }

    bot.answer_callback_query(call.id, "Цвет сохранён! ✅")
    bot.send_message(
        call.message.chat.id,
        f"Отлично! Твой любимый цвет — {color_names[choice]}."
    )

# 📊 Команда /profile — показать профиль
@bot.message_handler(commands=['profile'])
def show_profile(message):
    user_id = message.from_user.id

    if user_id not in user_data:
        bot.reply_to(message, "Ты ещё не вводил свои данные. Напиши /start и /color.")
        return

    name = user_data[user_id].get("name", "не указано")
    color = user_data[user_id].get("color", "не выбран")
    color_names = {
        "color_red": "Красный",
        "color_green": "Зелёный",
        "color_blue": "Синий"
    }

    color_display = color_names.get(color, color)

    bot.reply_to(
        message,
        f"*ТВОЙ ПРОФИЛЬ*\n\n"
        f"👤 *Имя:* {name}\n"
        f"🎨 *Любимый цвет:* {color_display}\n\n"
        f"Используй /myname и /color, чтобы изменить.",
        parse_mode="Markdown"
    )

# 🔄 Обработчик любых сообщений
@bot.message_handler(func=lambda message: True)
def echo_all(message):
    user_id = message.from_user.id
    name = user_data[user_id].get("name") if user_id in user_data else None

    if name:
        bot.reply_to(message, f"Привет, {name}! 😊\nНапиши /profile, чтобы увидеть свой профиль.")
    else:
        bot.reply_to(message, "Привет! Напиши /start, чтобы представиться.")

# Запуск бота
bot.polling()
