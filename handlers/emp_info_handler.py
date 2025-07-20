from telebot import types
from database.content_session import ContentSessionLocal
from database.session import SessionLocal
from database.models import Admin, Content
from services.sections import SECTIONS
import os

def show_employee_info_menu(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    buttons = [
        types.InlineKeyboardButton("Обучающие материалы", callback_data="training_materials"),
        types.InlineKeyboardButton("Экскурсии по компании", callback_data="company_tours"),
        types.InlineKeyboardButton("Виртуальная экскурсия", callback_data="virtual_tour"),
        types.InlineKeyboardButton("Организационная структура", callback_data="org_structure"),
        types.InlineKeyboardButton("Столовая", callback_data="canteen"),
        types.InlineKeyboardButton("Корпоративные мероприятия", callback_data="corporate_events"),
        types.InlineKeyboardButton("Оформление документов", callback_data="document_filling"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")
    ]

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "🎓 Информация для сотрудников:\n"
        "Выберите нужный раздел.",
        reply_markup=markup
    )
def show_section(bot, message, section_name):
    section_info = SECTIONS.get(section_name, {})
    title = section_info.get("title", section_name.capitalize())
    description = section_info.get("description", section_name.capitalize())
    # Кнопки
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")
    ]

    # Проверка, админ ли
    db= SessionLocal()
    if (db.query(Admin).filter(message.from_user.id == Admin.auth_token)):
        buttons.append(
            types.InlineKeyboardButton(
                f"Изменить «{title}»",
                callback_data=f"edit_section:{section_name}"
            )
        )
    markup.add(*buttons)

    # Отправляем заголовок и описание
    bot.send_message(
        message.chat.id,
        f"{description}",
        reply_markup=markup
    )
    # Получаем контент из БД
    db= ContentSessionLocal()
    content = db.query(Content).filter(Content.section == section_name).first()

    if content:
        if content.title or content.text:
            bot.send_message(message.chat.id, f"💎 {content.title}\n\n{content.text}")
        for file in content.files:
            if os.path.exists(file.file_path):
                with open(file.file_path, "rb") as f:
                    bot.send_document(message.chat.id, f)
    else:
        bot.send_message(message.chat.id, "Информация пока недоступна.")

    db.close()


# --- Обработчики для каждого пункта меню ---
from handlers.training_materials import show_training_menu
def show_training_materials(bot, message):
    show_training_menu(bot, message)


def show_company_tours(bot, message):
    bot.send_message(message.chat.id, "🚌 Здесь вы можете узнать о предстоящих экскурсиях по компании.")

def show_virtual_tour(bot, message):
    show_section(bot, message, "virtual_tour")

def show_organizational_structure(bot, message):
    show_section(bot, message, "structure")

def show_canteen_info(bot, message):
    show_section(bot, message, "canteen")

def show_corporate_events(bot, message):
    show_section(bot, message, "events")

def show_document_filling(bot, message):
    show_section(bot, message, "documents")
    

