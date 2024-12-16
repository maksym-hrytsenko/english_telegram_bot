import random
import telebot
import re
from telebot.types import ReplyKeyboardMarkup, KeyboardButton
from deep_translator import GoogleTranslator
from github import Github
WORD_FILE_PATH = r"unlearned_words.txt"

GITHUB_TOKEN = "b762dd84da576823223b389c8a884fae1619ce90"  # Замість "ваш_токен" вставте реальний токен
REPO_NAME = "MaKsYmKa28/english_telegram_bot"  # Наприклад: "username/my-bot-repo"
FILE_PATH = "https://raw.githubusercontent.com/MaKsYmKa28/english_telegram_bot/refs/heads/main/unlearned_words.txt?token=GHSAT0AAAAAAC3ZIWXKAGDVT5GK4HZ2XODYZ3ADDKA"  # Шлях до вашого файлу у репозиторії

# Ініціалізація клієнта GitHub
github = Github(GITHUB_TOKEN)
repo = github.get_repo(REPO_NAME)

def update_github_file(content, commit_message="Update words"):
    try:
        # Отримуємо поточний файл з репозиторію
        file = repo.get_contents(FILE_PATH)
        
        # Оновлюємо файл у репозиторії
        repo.update_file(
            path=FILE_PATH,
            message=commit_message,
            content=content,
            sha=file.sha
        )
        print("Файл успішно оновлено на GitHub.")
    except Exception as e:
        print(f"Помилка при оновленні файлу на GitHub: {e}")

# Функція перекладу слова
def translate_word(word):
    return GoogleTranslator(source='en', target='uk').translate(word)

# Створення об'єкта бота
bot = telebot.TeleBot('7908612781:AAGrjMOlyzldy8ifgBjlDdxnFZmmSF2ETDQ')

# Зчитування списку слів
def load_words():
    try:
        with open(WORD_FILE_PATH, "r", encoding="utf-8") as file:
            return [line.strip() for line in file if line.strip()]
    except FileNotFoundError:
        return []

# Збереження нового слова
def save_word(word_pair):
    with open(WORD_FILE_PATH, "a", encoding="utf-8") as file:
        file.write(word_pair + "\n")
    
    # Читаємо оновлений вміст файлу
    with open(WORD_FILE_PATH, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Оновлюємо файл на GitHub
    update_github_file(content, commit_message=f"Додано слово: {word_pair}")

# Оновлення списку слів
def update_words(words):
    with open(WORD_FILE_PATH, "w", encoding="utf-8") as file:
        file.writelines(word + "\n" for word in words)
    
    # Читаємо оновлений вміст файлу
    with open(WORD_FILE_PATH, "r", encoding="utf-8") as file:
        content = file.read()
    
    # Оновлюємо файл на GitHub
    update_github_file(content, commit_message="Оновлено список слів")

# Головне меню
def main_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("📋 Додати нове слово"),
        KeyboardButton("📚 Список з 20 слів"),
        KeyboardButton("📊 Кількість слів у базі")
    )
    return markup

# Перевірка слова
def is_english_word(word):
    return bool(re.match("^[a-zA-Z]+$", word))

# Обробник команди /start
@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "Привіт! Оберіть дію:", reply_markup=main_menu())

# Меню додавання слова
def add_word_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(
        KeyboardButton("↩️ Повернутися в головне меню")
    )
    return markup

# Обробка кнопки "📊 Кількість слів у базі"
@bot.message_handler(func=lambda message: message.text == "📊 Кількість слів у базі")
def count_words(message):
    words = load_words()
    word_count = len(words)
    bot.send_message(message.chat.id, f"📊 У базі даних {word_count} слів.", reply_markup=main_menu())

# Додавання нового слова
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

# Вибір 20 слів
@bot.message_handler(func=lambda message: message.text == "📚 Список з 20 слів")
def get_random_words(message):
    words = load_words()
    if len(words) < 20:
        bot.send_message(message.chat.id, "📭 У базі даних недостатньо слів.")
        return

    selected_words = random.sample(words, 20)
    numbered_list = "\n".join([f"{i + 1}. {word}" for i, word in enumerate(selected_words)])
    bot.send_message(message.chat.id, f"📚 Ось 20 слів:\n{numbered_list}", reply_markup=edit_menu(selected_words))

def edit_menu(selected_words):
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("✅ Все добре"), KeyboardButton("✏️ Змінити список слів"))
    bot.selected_words = selected_words  # Зберігаємо поточний список у властивості об'єкта бота
    return markup

# Обробка кнопки "Змінити список слів"
@bot.message_handler(func=lambda message: message.text == "✏️ Змінити список слів")
@bot.message_handler(func=lambda message: message.text == "✏️ Змінити список слів")
def change_words_prompt(message):
    bot.send_message(message.chat.id, "Введіть номери слів для заміни через пробіл:", reply_markup=back_button_menu())
    bot.register_next_step_handler(message, change_words)

def change_words(message):
    if message.text == "↩️ Повернутися назад":
        return_to_edit_menu(message)
        return

    try:
        # Обробка введених номерів слів для заміни
        indices = list(map(int, message.text.split()))
        indices = [i - 1 for i in indices if 0 < i <= len(bot.selected_words)]  # Перетворення на індекси

        words = load_words()  # Завантажуємо всі слова з бази даних

        # Видаляємо слова з бази, що будуть замінені
        words_to_remove = [bot.selected_words[i] for i in indices]
        updated_words = [word for word in words if word not in words_to_remove]

        # Оновлюємо базу даних
        update_words(updated_words)

        # Генеруємо нові слова для заміни
        new_selected_words = random.sample(updated_words, min(20, len(updated_words)))

        # Оновлюємо поточний список вибраних слів
        for i in indices:
            new_word = random.choice(updated_words)
            bot.selected_words[i] = new_word  # Замінюємо обрані слова на нові

        # Виводимо новий список
        numbered_list = "\n".join([f"{i + 1}. {word}" for i, word in enumerate(bot.selected_words)])
        bot.send_message(message.chat.id, f"🔄 Оновлений список слів:\n{numbered_list}", reply_markup=edit_menu(bot.selected_words))

    except Exception as e:
        bot.send_message(message.chat.id, f"❌ Помилка: {e}. Спробуйте ще раз.", reply_markup=back_button_menu())

def return_to_edit_menu(message):
    if hasattr(bot, 'selected_words') and bot.selected_words:
        numbered_list = "\n".join([f"{i + 1}. {word}" for i, word in enumerate(bot.selected_words)])
        bot.send_message(message.chat.id, f"📚 Поточний список слів:\n{numbered_list}", reply_markup=edit_menu(bot.selected_words))
    else:
        bot.send_message(message.chat.id, "📭 Немає поточного списку для редагування.", reply_markup=main_menu())

# Меню з кнопкою повернення назад
def back_button_menu():
    markup = ReplyKeyboardMarkup(resize_keyboard=True)
    markup.add(KeyboardButton("↩️ Повернутися назад"))
    return markup

# Обробка кнопки "Все добре"
@bot.message_handler(func=lambda message: message.text == "✅ Все добре")
def confirm_words(message):
    # Отримуємо поточний список слів, що були обрані
    selected_words = bot.selected_words
    
    # Завантажуємо всі слова з бази
    words = load_words()

    # Видаляємо 20 слів, що знаходяться в поточному списку
    words_to_remove = [word for word in words if word in selected_words]
    updated_words = [word for word in words if word not in words_to_remove]
    
    # Оновлюємо базу даних без цих 20 слів
    update_words(updated_words)

    bot.send_message(message.chat.id, "✅ Список затверджено. Вибрані слова видалено з бази. Повертаємося в головне меню.", reply_markup=main_menu())

# Обробка кнопки "Повернутися назад"
@bot.message_handler(func=lambda message: message.text == "↩️ Повернутися назад")
def return_to_edit_menu(message):
    if hasattr(bot, 'selected_words'):
        numbered_list = "\n".join([f"{i + 1}. {word}" for i, word in enumerate(bot.selected_words)])
        bot.send_message(message.chat.id, f"📚 Поточний список слів:\n{numbered_list}", reply_markup=edit_menu(bot.selected_words))
    else:
        bot.send_message(message.chat.id, "📭 Немає поточного списку для редагування.", reply_markup=main_menu())

# Запуск бота
bot.polling(non_stop=True)
