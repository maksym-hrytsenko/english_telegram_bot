import random
import telebot
import mysql.connector
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
import re
from deep_translator import GoogleTranslator

# Підключення до бази даних MySQL
def get_db_connection():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # Вкажіть ваш пароль, якщо він є
        database="unlearned_words"
    )

# Функція перекладу слова
def translate_word(word):
    return GoogleTranslator(source='en', target='uk').translate(word)

# Створення об'єкта бота
bot = telebot.TeleBot('7908612781:AAGrjMOlyzldy8ifgBjlDdxnFZmmSF2ETDQ')

def load_words():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT word, translation FROM words")
        words = cursor.fetchall()
        cursor.close()
        conn.close()
        return [f"{word} -> {translation}" for word, translation in words]
    except mysql.connector.Error as err:
        print(f"Помилка при зчитуванні слів з бази: {err}")
        return []

def save_word(word_pair):
    word, translation = word_pair.split(" -> ")
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO words (word, translation) VALUES (%s, %s)", (word, translation))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Помилка при збереженні слова в базі: {err}")

def delete_words_from_db(words_to_delete):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        for word in words_to_delete:
            word_to_remove = word.split(" -> ")[0]  # Отримуємо тільки слово (без перекладу)
            cursor.execute("DELETE FROM words WHERE word = %s", (word_to_remove,))
        conn.commit()
        cursor.close()
        conn.close()
    except mysql.connector.Error as err:
        print(f"Помилка при видаленні слів з бази: {err}")

# Головне меню з новою кнопкою
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("📋 Додати нове слово"),
        KeyboardButton("📚 Список з 20 слів"),
        KeyboardButton("📊 Кількість слів у базі")
    )
    return markup

# Обробка кнопки "📊 Кількість слів у базі"
@bot.message_handler(func=lambda message: message.text == "📊 Кількість слів у базі")
def count_words(message):
    words = load_words()
    word_count = len(words)
    bot.send_message(message.chat.id, f"📊 У базі даних {word_count} слів.", reply_markup=main_menu())

# Обробник команди /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Оберіть дію:", reply_markup=main_menu())

# Перевірка слова
def is_english_word(word):
    return bool(re.match("^[a-zA-Z]+$", word))

# Меню додавання слова
def add_word_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("↩️ Повернутися в головне меню")
    )
    return markup

@bot.message_handler(func=lambda message: message.text == "📋 Додати нове слово")
def add_word_prompt(message):
    bot.send_message(message.chat.id, "Напишіть слово англійською", reply_markup=add_word_menu())
    bot.register_next_step_handler(message, add_word)

def add_word(message):
    if message.text == "↩️ Повернутися в головне меню":
        bot.send_message(message.chat.id, "Повернення в головне меню.", reply_markup=main_menu())
        return

    word = message.text.strip()
    if not is_english_word(word):
        bot.send_message(message.chat.id, "❌ Слово має містити лише англійські літери.")
        bot.register_next_step_handler(message, add_word)
        return

    words = load_words()
    existing_words = [entry.split(" -> ")[0] for entry in words]
    if word in existing_words:
        bot.send_message(message.chat.id, "❌ Це слово вже є в базі даних.")
        bot.register_next_step_handler(message, add_word)
        return

    try:
        translation = translate_word(word)
        save_word(f"{word} -> {translation}")
        bot.send_message(message.chat.id, f"✅ Слово '{word}' додано з перекладом '{translation}'. Напишіть наступне слово.")
        bot.register_next_step_handler(message, add_word)
    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка: {e}")

# Обробка кнопки "📚 Список з 20 слів"
@bot.message_handler(func=lambda message: message.text == "📚 Список з 20 слів")
def get_random_words(message):
    words = load_words()
    if len(words) < 20:
        bot.send_message(message.chat.id, "📭 У базі даних недостатньо слів.")
        return

    selected_words = random.sample(words, 20)
    numbered_list = "\n".join([f"{i + 1}. {word}" for i, word in enumerate(selected_words)])

    # Видаляємо вибрані слова з бази даних
    delete_words_from_db(selected_words)

    # Після видалення слів з бази, повертаємось у головне меню
    bot.send_message(message.chat.id, f"📚 Ось 20 слів:\n{numbered_list}", reply_markup=main_menu())

# Запуск бота
bot.polling(non_stop=True)
