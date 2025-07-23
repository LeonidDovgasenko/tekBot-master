from telebot import types
from database.content_session import ContentSessionLocal
from database.session import SessionLocal
from database.models import Admin, Content, CompanyTour
from services.sections import SECTIONS
import os

def show_employee_info_menu(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    user_id = message.from_user.id
    db = SessionLocal()
    is_admin = db.query(Admin).filter(Admin.auth_token == str(user_id)).first() is not None
    db.close()
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
    if is_admin:
        buttons.append(types.InlineKeyboardButton("⏰ Напоминания", callback_data="reminders"))
        buttons.append(types.InlineKeyboardButton("📊 Отчетность", callback_data="analytics_menu"))  
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
                callback_data=f"edit_section:{section_name}:training"
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
    markup = types.InlineKeyboardMarkup(row_width=1)
    buttons = [
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")
    ]
    db = SessionLocal()
    user_id = str(message.from_user.id)
    is_admin = db.query(Admin).filter(Admin.auth_token == str(user_id)).first()
    if is_admin is not None:
        buttons.append(
            types.InlineKeyboardButton(
                "Добавить экскурсию",
                callback_data="add_tour"
            )
        )
    markup.add(*buttons)
    bot.send_message(message.chat.id, "🚌 Экскурсии по компании — выберите интересующую", reply_markup=markup)

    tours = db.query(CompanyTour).filter(CompanyTour.is_active == True).all()

    if not tours:
        bot.send_message(message.chat.id, "Пока нет активных экскурсий")
        return
    for tour in tours:
        text = f"🏛 {tour.title}\n" \
               f"🕒 {tour.meeting_time.strftime('%d.%m.%Y %H:%M')}\n" \
               f"📍 {tour.meeting_place}\n" \
               f"📝 {tour.description or 'Описание отсутствует'}\n\n" \
               f"Участников: {len(tour.registrations)} / {tour.max_participants}"

        reg_button = types.InlineKeyboardButton(
            "✅ Записаться",
            callback_data=f"register_tour:{tour.id}"
        )
        tour_markup = types.InlineKeyboardMarkup()
        tour_markup.add(reg_button)

        bot.send_message(message.chat.id, text, reply_markup=tour_markup)

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
    

