# handlers/admin_tour_handler.py

from telebot import types
from database.models import CompanyTour, User_info
from database.session import SessionLocal
from datetime import datetime

def register_admin_tour_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data == "add_tour")
    def request_tour_title(call):
        msg = bot.send_message(call.message.chat.id, "Введите название экскурсии:")
        bot.register_next_step_handler(msg, request_tour_description)

    def request_tour_description(message):
        title = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введите описание экскурсии:")
        bot.register_next_step_handler(msg, request_tour_time, title)

    def request_tour_time(message, title):
        description = message.text.strip()
        msg = bot.send_message(message.chat.id, "Введите дату и время (в формате 01.08.2025 10:00):")
        bot.register_next_step_handler(msg, request_tour_place, title, description)

    def request_tour_place(message, title, description):
        try:
            time = datetime.strptime(message.text.strip(), "%d.%m.%Y %H:%M")
        except ValueError:
            bot.send_message(message.chat.id, "❌ Неверный формат даты. Попробуйте снова.")
            return

        msg = bot.send_message(message.chat.id, "Введите место сбора:")
        bot.register_next_step_handler(msg, save_tour, title, description, time)

    def save_tour(message, title, description, time):
        place = message.text.strip()
        db = SessionLocal()
        new_tour = CompanyTour(
            title=title,
            description=description,
            meeting_time=time,
            meeting_place=place
        )
        db.add(new_tour)
        db.commit()
        db.refresh(new_tour)
        bot.send_message(message.chat.id, "✅ Экскурсия успешно добавлена")

        # Рассылка всем сотрудникам
        users = db.query(User_info).all()
        for user in users:
            try:
                bot.send_message(
                    user.auth_token,
                    f"📢 Новая экскурсия: {title}\n"
                    f"📅 {time.strftime('%d.%m.%Y %H:%M')}\n"
                    f"📍 {place}\n\n"
                    f"Нажмите, чтобы записаться"
                )
            except:
                continue