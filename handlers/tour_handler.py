# handlers/tour_handler.py

from telebot import types
from database.models import TourRegistration, CompanyTour, User_info, Admin
from database.session import SessionLocal
from datetime import datetime

def register_tour_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("register_tour:"))
    def handle_register_tour(call):
        tour_id = int(call.data.split(":")[1])
        user_token = str(call.from_user.id)

        db = SessionLocal()
        tour = db.query(CompanyTour).get(tour_id)
        user_info = db.query(User_info).filter(User_info.auth_token == user_token).first()

        if not tour:
            bot.answer_callback_query(call.id, "Экскурсия не найдена")
            return

        if len(tour.registrations) >= tour.max_participants:
            bot.answer_callback_query(call.id, "Мест больше нет")
            return

        existing = db.query(TourRegistration).filter(
            TourRegistration.tour_id == tour_id,
            TourRegistration.user_auth_token == user_token
        ).first()

        if existing:
            bot.answer_callback_query(call.id, "Вы уже записаны")
            return

        registration = TourRegistration(
            tour_id=tour_id,
            user_auth_token=user_token
        )
        db.add(registration)
        db.commit()
        bot.answer_callback_query(call.id, "Вы записались!")

        bot.send_message(
            call.message.chat.id,
            f"✅ Вы записаны на '{tour.title}' в {tour.meeting_time.strftime('%d.%m.%Y %H:%M')}"
        )

        # Уведомление админу
        admins = db.query(Admin).all()
        for admin in admins:
            bot.send_message(
                admin.auth_token,
                f"🔔 Новая запись на экскурсию:\n"
                f"👤 {user_info.full_name}\n"
                f"🏛 {tour.title}\n"
                f"🕒 {tour.meeting_time.strftime('%d.%m.%Y %H:%M')}"
            )