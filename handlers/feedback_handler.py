from telebot import types
from database.session import SessionLocal
from database.models import Feedback, Admin
import re

def ask_feedback(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Проверка прав администратора
    db = SessionLocal()
    is_admin = db.query(Admin).filter(Admin.auth_token == str(message.from_user.id)).first() is not None
    db.close()
    
    buttons = [
        types.InlineKeyboardButton("Оставить отзыв", callback_data="give_feedback"),
        types.InlineKeyboardButton("Пройти опрос", callback_data="take_quiz"),
    ]
    
    # Только админы могут просматривать отзывы
    if is_admin:
        buttons.append(types.InlineKeyboardButton("Просмотреть отзывы", callback_data="view_feedbacks"))
    
    buttons.append(types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main"))
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id,
        "💬 Обратная связь:\n"
        "Вы можете оставить отзыв, пройти опрос или посмотреть результаты.",
        reply_markup=markup
    )

def request_feedback_text(bot, call):
    bot.send_message(call.message.chat.id, "✍️ Напишите ваш отзыв:")
    bot.register_next_step_handler(call.message, lambda m: save_feedback(bot, m))

def save_feedback(bot, message):
    try:
        db = SessionLocal()
        
        # Очищаем текст от HTML-тегов
        clean_text = re.sub(r'<[^>]*>', '', message.text)
        
        new_feedback = Feedback(
            user_id=message.from_user.id,
            full_name=message.from_user.full_name,
            feedback_text=clean_text
        )
        db.add(new_feedback)
        db.commit()
        
        bot.send_message(message.chat.id, "✅ Ваш отзыв успешно сохранен!")
    except Exception as e:
        bot.send_message(message.chat.id, "⚠️ Произошла ошибка при сохранении отзыва")
        print(f"Error saving feedback: {e}")
    finally:
        db.close()
    
    # Возвращаем в меню обратной связи
    ask_feedback(bot, message)

def show_feedbacks(bot, call):
    try:
        db = SessionLocal()
        feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(20).all()
        
        if not feedbacks:
            bot.send_message(call.message.chat.id, "📭 Пока нет отзывов")
            return
            
        response = "📋 Последние отзывы:\n\n"
        for feedback in feedbacks:
            response += (
                f"👤 {feedback.full_name} (ID: {feedback.user_id})\n"
                f"🕒 {feedback.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                f"💬 {feedback.feedback_text}\n\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )
        
        # Разбиваем на части если слишком длинное сообщение
        max_length = 4000
        if len(response) > max_length:
            parts = [response[i:i+max_length] for i in range(0, len(response), max_length)]
            for part in parts:
                bot.send_message(call.message.chat.id, part)
        else:
            bot.send_message(call.message.chat.id, response)
            
    except Exception as e:
        bot.send_message(call.message.chat.id, "⚠️ Произошла ошибка при загрузке отзывов")
        print(f"Error loading feedbacks: {e}")
    finally:
        db.close()
    
    # Возвращаем в меню обратной связи
    ask_feedback(bot, call.message)