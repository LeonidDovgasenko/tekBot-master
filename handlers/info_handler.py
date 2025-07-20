from telebot import types
from database.session import SessionLocal
from database.content_session import ContentSessionLocal
from database.models import Admin, Content
import os

def show_info_menu(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    buttons = [
        types.InlineKeyboardButton("История компании", callback_data="history"),
        types.InlineKeyboardButton("Ценности", callback_data="values"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")
    ]
    db = SessionLocal()
    if (db.query(Admin).filter(message.from_user.id == Admin.auth_token)):
        buttons.append(types.InlineKeyboardButton(f"Изменить «{buttons[0].text}»", callback_data='edit_section:history'))
        buttons.append(types.InlineKeyboardButton(f"Изменить «{buttons[1].text}»", callback_data='edit_section:values'))

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "📚 Здесь вы найдете информацию о нашей компании.",
        reply_markup=markup
    )

    @bot.callback_query_handler(func=lambda call: call.data in ["history", "values"])
    def show_content(call):
        section = call.data
        db = ContentSessionLocal()
        try:
            content = db.query(Content).filter(Content.section == section).first()
            if content:
                bot.send_message(call.message.chat.id, f"📌 {content.title}\n\n{content.text}")

                for file in content.files:
                    if os.path.exists(file.file_path):
                        with open(file.file_path, "rb") as f:
                            bot.send_document(call.message.chat.id, f)
                    else:
                        bot.send_message(call.message.chat.id, f"Файл {file.file_path} не найден.")
            else:
                bot.send_message(call.message.chat.id, "Информация пока недоступна.")
        finally:
            db.close()