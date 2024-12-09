import telebot
from telebot.types import BotCommand
from datetime import datetime
import threading
import re
from dotenv import load_dotenv
import os
# Инициализация бота
load_dotenv()

TOKEN = os.getenv("BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)

# Хранилище задач
tasks = {}

# Команда /start
@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Привет! Используй /add для добавления задачи.")

# Команда /add
@bot.message_handler(commands=["add"])
def add_task(message):
    bot.send_message(message.chat.id, "Введите текст задачи:")
    bot.register_next_step_handler(message, get_task_text)

# Шаг 1: Получаем текст задачи
def get_task_text(message):
    user_id = message.chat.id
    task_text = message.text
    tasks[user_id] = {"task": task_text}
    bot.send_message(user_id, "Введите дату (ДД.ММ или ДД.ММ.ГГГГ):")
    bot.register_next_step_handler(message, get_task_date)

# Шаг 2: Обрабатываем дату
def get_task_date(message):
    user_id = message.chat.id
    date_input = normalize_input(message.text)

    try:
        task_date = parse_date(date_input)
        tasks[user_id]["date"] = task_date
        bot.send_message(user_id, "Введите время (ЧЧ:ММ):")
        bot.register_next_step_handler(message, get_task_time)
    except ValueError:
        bot.send_message(user_id, "Неверный формат даты. Попробуйте снова.")
        bot.register_next_step_handler(message, get_task_date)

# Шаг 3: Обрабатываем время
def get_task_time(message):
    user_id = message.chat.id
    time_input = normalize_input(message.text)

    try:
        task_time = parse_time(time_input)
        tasks[user_id]["time"] = datetime.combine(tasks[user_id]["date"], task_time)

        task_datetime = tasks[user_id]["time"]
        bot.send_message(user_id, f"Задача добавлена: {tasks[user_id]['task']} на {task_datetime.strftime('%d.%m.%Y %H:%M')}")
        
        # Запускаем напоминание
        threading.Thread(target=schedule_task, args=(user_id,)).start()

    except ValueError:
        bot.send_message(user_id, "Неверный формат времени. Попробуйте снова.")
        bot.register_next_step_handler(message, get_task_time)

# Нормализация ввода
def normalize_input(text):
    if text is None:
        raise ValueError("Ввод не может быть пустым.")
    return re.sub(r'[.,/\\\-_бю!]', '', text)

# Парсинг даты
def parse_date(date_str):
    today = datetime.now()
    current_year = today.year

    if len(date_str) == 2:  # Только день
        day = int(date_str)
        return datetime(current_year, today.month, day).date()
    elif len(date_str) == 4:  # День и месяц
        day = int(date_str[:2])
        month = int(date_str[2:])
        return datetime(current_year, month, day).date()
    elif len(date_str) == 8:  # Полная дата
        return datetime.strptime(date_str, "%d%m%Y").date()
    else:
        raise ValueError("Неверный формат даты")

# Парсинг времени
def parse_time(time_str):
    if len(time_str) == 4:
        return datetime.strptime(time_str, "%H%M").time()
    elif len(time_str) == 5:
        return datetime.strptime(time_str, "%H:%M").time()
    else:
        raise ValueError("Неверный формат времени")

# Напоминание
def schedule_task(user_id):
    task_data = tasks.get(user_id)
    if task_data:
        delay = (task_data["time"] - datetime.now()).total_seconds()
        if delay > 0:
            threading.Event().wait(delay)
            bot.send_message(user_id, f"Напоминаю, что в {task_data['time'].strftime('%H:%M')} нужно: {task_data['task']}")


# Команда /tasks
@bot.message_handler(commands=["tasks"])
def list_tasks(message):
    user_id = message.chat.id
    if user_id in tasks:
        task_info = f"Задача: {tasks[user_id]['task']}\nДата и время: {tasks[user_id]['time'].strftime('%d.%m.%Y %H:%M')}"
        bot.send_message(user_id, f"Ваши задачи:\n{task_info}")
    else:
        bot.send_message(user_id, "Список задач пуст.")

# Команда /delete
@bot.message_handler(commands=["delete"])
def delete_task(message):
    user_id = message.chat.id
    if user_id in tasks:
        task_text = tasks[user_id]['task']
        del tasks[user_id]
        bot.send_message(user_id, f"Задача '{task_text}' удалена.")
    else:
        bot.send_message(user_id, "У вас нет активных задач.")

# Установка команд
bot.set_my_commands([
    BotCommand("start", "Запуск бота"),
    BotCommand("add", "Добавить задачу"),
    BotCommand("tasks", "Показать задачи"),
    BotCommand("delete", "Удалить задачу"),
])

# Запуск бота
bot.polling(none_stop=True)
