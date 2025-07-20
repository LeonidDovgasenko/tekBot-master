from telebot import types
from database.session import SessionLocal
from database.models import Reminder, User
from datetime import datetime, timedelta
import re

def save_reminder(bot, text, interval=None, is_instant=False):
    """Сохранить напоминание в базу данных"""
    db = SessionLocal()
    try:
        reminder = Reminder(
            text=text,
            is_recurring=bool(interval),
            interval=interval
        )
        
        if is_instant:
            send_reminder_to_all(bot, text)
            reminder.next_send = datetime.now()
        else:
            reminder.next_send = calculate_next_send(interval)
        
        db.add(reminder)
        db.commit()
        return True
    except Exception as e:
        print(f"Error saving reminder: {e}")
        return False
    finally:
        db.close()

def request_reminder_schedule(bot, call, text):
    """Запросить расписание для напоминания"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Ежедневно", callback_data=f"reminder_interval:daily:{text}"),
        types.InlineKeyboardButton("Еженедельно", callback_data=f"reminder_interval:weekly:{text}"),
        types.InlineKeyboardButton("Ежемесячно", callback_data=f"reminder_interval:monthly:{text}"),
        types.InlineKeyboardButton("Каждый час", callback_data=f"reminder_interval:hourly:{text}")
    )
    
    bot.send_message(
        call.message.chat.id,
        "⏰ Выберите интервал для повторяющегося напоминания:",
        reply_markup=markup
    )
    
def show_reminders_menu(bot, message):
    """Показать меню управления напоминаниями"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    buttons = [
        types.InlineKeyboardButton("🔔 Отправить напоминание", callback_data="send_reminder"),
        types.InlineKeyboardButton("⏰ Настроить напоминания", callback_data="configure_reminders"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="employee_info")
    ]
    
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id,
        "⏰ Управление напоминаниями:\n"
        "Вы можете отправить моментальное напоминание или настроить периодические.",
        reply_markup=markup
    )

def request_reminder_text(bot, call):
    """Запросить текст напоминания"""
    bot.send_message(call.message.chat.id, "✍️ Введите текст напоминания:")
    bot.register_next_step_handler(call.message, lambda m: process_reminder_text(bot, m))

def process_reminder_text(bot, message):
    """Обработать текст напоминания и запросить тип"""
    text = message.text.strip()
    if len(text) < 5:
        bot.send_message(message.chat.id, "❌ Текст напоминания должен содержать минимум 5 символов")
        return request_reminder_text(bot, message)
    
    # Сохраняем текст в контексте
    bot.reply_to(message, "✅ Текст напоминания принят!")
    
    # Предлагаем выбрать тип напоминания
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("🔔 Отправить сейчас", callback_data=f"reminder_type:instant:{text}"),
        types.InlineKeyboardButton("⏰ Запланировать", callback_data=f"reminder_type:scheduled:{text}"),
        types.InlineKeyboardButton("🔄 Настроить повтор", callback_data=f"reminder_type:recurring:{text}")
    )
    
    bot.send_message(
        message.chat.id,
        "Выберите тип напоминания:",
        reply_markup=markup
    )

def request_reminder_schedule(bot, call, text):
    """Запросить расписание для напоминания"""
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("Ежедневно", callback_data=f"reminder_interval:daily:{text}"),
        types.InlineKeyboardButton("Еженедельно", callback_data=f"reminder_interval:weekly:{text}"),
        types.InlineKeyboardButton("Ежемесячно", callback_data=f"reminder_interval:monthly:{text}"),
        types.InlineKeyboardButton("Каждый час", callback_data=f"reminder_interval:hourly:{text}")
    )
    
    bot.send_message(
        call.message.chat.id,
        "⏰ Выберите интервал для повторяющегося напоминания:",
        reply_markup=markup
    )

def save_reminder(bot, text, interval=None, is_instant=False):
    """Сохранить напоминание в базу данных"""
    db = SessionLocal()
    try:
        reminder = Reminder(
            text=text,
            is_recurring=bool(interval),
            interval=interval
        )
        
        if is_instant:
            # Отправляем немедленно
            send_reminder_to_all(bot, text)
            reminder.next_send = datetime.now()
        else:
            # Для повторяющихся напоминаний установим следующее время отправки
            reminder.next_send = calculate_next_send(interval)
        
        db.add(reminder)
        db.commit()
        return True
    except Exception as e:
        print(f"Error saving reminder: {e}")
        return False
    finally:
        db.close()

def send_reminder_to_all(bot, text):
    """Отправить напоминание всем пользователям"""
    db = SessionLocal()
    try:
        users = db.query(User).all()
        for user in users:
            try:
                bot.send_message(user.auth_token, f"🔔 Напоминание:\n\n{text}")
            except Exception as e:
                print(f"Не удалось отправить напоминание пользователю {user.auth_token}: {e}")
    finally:
        db.close()

def calculate_next_send(interval):
    """Вычислить следующее время отправки для повторяющихся напоминаний"""
    now = datetime.now()
    if interval == "daily":
        return now + timedelta(days=1)
    elif interval == "weekly":
        return now + timedelta(weeks=1)
    elif interval == "monthly":
        # Простое приближение для месяца
        return now + timedelta(days=30)
    elif interval == "hourly":
        return now + timedelta(hours=1)
    return now

def show_scheduled_reminders(bot, call):
    """Показать список запланированных напоминаний"""
    db = SessionLocal()
    try:
        reminders = db.query(Reminder).filter(Reminder.is_active == True).all()
        
        if not reminders:
            bot.send_message(call.message.chat.id, "ℹ️ Нет активных напоминаний")
            return
            
        response = "⏰ Активные напоминания:\n\n"
        for reminder in reminders:
            status = "🔁 Повторяющееся" if reminder.is_recurring else "⏱️ Однократное"
            interval = f"({reminder.interval})" if reminder.interval else ""
            response += (
                f"📝 {reminder.text[:50]}...\n"
                f"🆔 ID: {reminder.id} | {status} {interval}\n"
                f"⏳ Следующая отправка: {reminder.next_send.strftime('%d.%m.%Y %H:%M')}\n"
                "━━━━━━━━━━━━━━━━━━━━\n\n"
            )
        
        # Добавляем кнопки управления
        markup = types.InlineKeyboardMarkup(row_width=2)
        markup.add(
            types.InlineKeyboardButton("❌ Удалить напоминание", callback_data="delete_reminder_menu"),
            types.InlineKeyboardButton("⬅ Назад", callback_data="reminders_menu")
        )
        
        bot.send_message(call.message.chat.id, response, reply_markup=markup)
    finally:
        db.close()

def request_reminder_to_delete(bot, call):
    """Запросить ID напоминания для удаления"""
    bot.send_message(call.message.chat.id, "✍️ Введите ID напоминания, которое хотите удалить:")
    bot.register_next_step_handler(call.message, lambda m: delete_reminder(bot, m))

def delete_reminder(bot, message):
    """Удалить напоминание по ID"""
    try:
        reminder_id = int(message.text.strip())
        db = SessionLocal()
        reminder = db.query(Reminder).get(reminder_id)
        
        if reminder:
            db.delete(reminder)
            db.commit()
            bot.send_message(message.chat.id, f"✅ Напоминание #{reminder_id} успешно удалено!")
        else:
            bot.send_message(message.chat.id, f"❌ Напоминание с ID {reminder_id} не найдено")
    except ValueError:
        bot.send_message(message.chat.id, "❌ Пожалуйста, введите числовой ID")
    except Exception as e:
        bot.send_message(message.chat.id, f"⚠️ Ошибка при удалении: {str(e)}")
    finally:
        db.close()