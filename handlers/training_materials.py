from telebot import types
from database.content_session import ContentSessionLocal
from database.session import SessionLocal
from database.models import Content
from database.models import Admin, Content
import os

def show_training_menu(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=2)  # 2 кнопки в ряду
    user_id = message.from_user.id
    db = SessionLocal()
    is_admin = db.query(Admin).filter(Admin.auth_token == str(user_id)).first() is not None
    db.close()

    buttons = []
    print(f"User ID: {user_id}, is_admin: {is_admin}")
    # Категории
    buttons.append(types.InlineKeyboardButton("📂 Категории", callback_data="training_categories"))

    # Поиск
    buttons.append(types.InlineKeyboardButton("🔍 Поиск", callback_data="training_search"))

    # Тесты
    buttons.append(types.InlineKeyboardButton("📝 Тесты", callback_data="training_section:training_tests"))
    #if is_admin:
    buttons.append(types.InlineKeyboardButton("✏️ Изменить «📝 Тесты»", callback_data="edit_section:training_tests"))

    markup.add(*buttons)

    # Кнопка назад — на отдельной строке
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="training"))

    bot.send_message(
        message.chat.id,
        "🎓 Добро пожаловать в обучающие материалы. Выберите действие:",
        reply_markup=markup
    )

def show_training_by_section(bot, call, section_name):
    db = ContentSessionLocal()
    content = db.query(Content).filter(Content.section == section_name).first()
    if not content:
        bot.send_message(call.message.chat.id, "Материалы отсутствуют.")
        return

    text = f"📘 {content.title}\n\n{content.text}" if content.title or content.text else "📎 Материалы:"
    bot.send_message(call.message.chat.id, text)

    for file in content.files:
        if os.path.exists(file.file_path):
            with open(file.file_path, "rb") as f:
                bot.send_document(call.message.chat.id, f)
        else:
            bot.send_message(call.message.chat.id, f"❌ Файл не найден: {file.file_path}")
            
user_search_state = {}    

def ask_training_search(bot, message):
    bot.send_message(message.chat.id, "🔍 Введите начало названия материала для поиска:")
    user_search_state[message.from_user.id] = True
def show_training_categories(bot, call):
    # Создаём основное меню подкатегорий: PDF, Видео, Презентации
    markup = types.InlineKeyboardMarkup(row_width=1)
    categories = [
        ("📄 PDF", "training_materials_pdf"),
        ("🎥 Видео", "training_materials_video"),
        ("📊 Презентации", "training_materials_presentation"),
    ]
    
    for label, callback in categories:
        markup.add(types.InlineKeyboardButton(label, callback_data=f"training_section:{callback}"))

    db = SessionLocal()
    user_id = call.from_user.id
    if db.query(Admin).filter(Admin.auth_token == str(user_id)).first():
        for label, callback in categories:
            # training_materials_pdf → pdf
            subcategory = callback.replace("training_materials_", "")
            markup.add(types.InlineKeyboardButton(f"✏️ Изменить «{label}»", callback_data=f"edit_section:{callback}"))

    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="training"))

    bot.send_message(
        call.message.chat.id,
        "📂 Выберите категорию материалов:",
        reply_markup=markup
    )
    
               

