from telebot import types
from database.session import SessionLocal
from database.models import Admin
from services.faq_service import (
    add_question, 
    get_answered_questions,
    get_unanswered_questions,
    answer_question,
    delete_question,
    get_question_by_id
)

def show_faq_menu(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    buttons = [
        types.InlineKeyboardButton("📋 Список вопросов", callback_data="faq_list"),
        types.InlineKeyboardButton("❓ Задать вопрос", callback_data="faq_ask"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")
    ]

    # Проверка админских прав
    db = SessionLocal()
    user_id = message.from_user.id
    is_admin = db.query(Admin).filter(Admin.auth_token == str(user_id)).first() is not None
    db.close()

    #if is_admin:
    buttons.append(types.InlineKeyboardButton("🛠 Ответить на вопросы", callback_data="faq_admin"))

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "❓ Часто задаваемые вопросы:\n"
        "Выберите действие:",
        reply_markup=markup
    )

def show_question_list(bot, call):
    questions = get_answered_questions()
    
    if not questions:
        bot.send_message(call.message.chat.id, "Пока нет отвеченных вопросов.")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for question in questions:
        # Обрезаем длинный вопрос для кнопки
        btn_text = question.question[:30] + '...' if len(question.question) > 30 else question.question
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"faq_show:{question.id}"))
    
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="faq"))
    
    bot.send_message(call.message.chat.id, "📋 Выберите вопрос:", reply_markup=markup)

def show_question_detail(bot, call, question_id):
    question = get_question_by_id(question_id)
    
    if not question or not question.answer:
        bot.send_message(call.message.chat.id, "Вопрос не найден или еще не отвечен.")
        return
    
    response = f"❓ *Вопрос:*\n{question.question}\n\n"
    response += f"💡 *Ответ:*\n{question.answer}\n\n"
    response += f"🕒 *Отвечено:* {question.answered_at.strftime('%d.%m.%Y %H:%M')}"
    
    bot.send_message(call.message.chat.id, response, parse_mode="Markdown")

def ask_question(bot, message):
    bot.send_message(message.chat.id, "✍️ Напишите ваш вопрос:")
    bot.register_next_step_handler(message, lambda m: process_question(bot, m))

def process_question(bot, message):
    user_id = message.from_user.id
    question_text = message.text.strip()
    
    if not question_text:
        bot.send_message(message.chat.id, "❌ Вопрос не может быть пустым. Попробуйте еще раз.")
        return
    
    add_question(user_id, question_text)
    bot.send_message(message.chat.id, "✅ Ваш вопрос сохранен! Администратор ответит в ближайшее время.")

def show_unanswered_questions(bot, call):
    # Проверка прав администратора
    db = SessionLocal()
    is_admin = db.query(Admin).filter(Admin.auth_token == str(call.from_user.id)).first() is not None
    db.close()
    
    if not is_admin:
        bot.answer_callback_query(call.id, "❌ Доступ запрещен")
        return
    
    questions = get_unanswered_questions()
    
    if not questions:
        bot.send_message(call.message.chat.id, "🎉 Нет новых неотвеченных вопросов!")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    for question in questions:
        # Обрезаем длинный вопрос для кнопки
        btn_text = question.question[:30] + '...' if len(question.question) > 30 else question.question
        markup.add(types.InlineKeyboardButton(btn_text, callback_data=f"faq_admin_detail:{question.id}"))
    
    markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="faq"))
    
    bot.send_message(call.message.chat.id, "❓ Неотвеченные вопросы:", reply_markup=markup)

def show_question_admin_options(bot, call, question_id):
    # Проверка прав администратора
    db = SessionLocal()
    is_admin = db.query(Admin).filter(Admin.auth_token == str(call.from_user.id)).first() is not None
    db.close()
    
    if not is_admin:
        bot.answer_callback_query(call.id, "❌ Доступ запрещен")
        return
    
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("✏️ Ответить на вопрос", callback_data=f"faq_answer:{question_id}"),
        types.InlineKeyboardButton("🗑 Удалить вопрос", callback_data=f"faq_delete:{question_id}"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="faq_admin")
    )
    
    bot.send_message(call.message.chat.id, "Выберите действие:", reply_markup=markup)

def request_answer(bot, call, question_id):
    bot.send_message(call.message.chat.id, "✍️ Введите ответ на вопрос:")
    bot.register_next_step_handler(call.message, lambda m: process_answer(bot, m, question_id))

def process_answer(bot, message, question_id):
    answer_text = message.text.strip()
    
    if not answer_text:
        bot.send_message(message.chat.id, "❌ Ответ не может быть пустым. Попробуйте еще раз.")
        return
    
    if answer_question(question_id, answer_text):
        bot.send_message(message.chat.id, "✅ Ответ успешно сохранен!")
    else:
        bot.send_message(message.chat.id, "❌ Не удалось сохранить ответ. Вопрос не найден.")

def confirm_delete_question(bot, call, question_id):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("✅ Да, удалить", callback_data=f"faq_delete_confirm:{question_id}"),
        types.InlineKeyboardButton("❌ Отмена", callback_data=f"faq_admin_detail:{question_id}")
    )
    
    bot.send_message(call.message.chat.id, "Вы уверены, что хотите удалить этот вопрос?", reply_markup=markup)

def delete_question_handler(bot, call, question_id):
    if delete_question(question_id):
        bot.send_message(call.message.chat.id, "✅ Вопрос успешно удален!")
    else:
        bot.send_message(call.message.chat.id, "❌ Не удалось удалить вопрос.")