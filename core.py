# core.py
import os
from dotenv import load_dotenv
import telebot
import threading
import time
from datetime import datetime
from database.session import SessionLocal
from database.models import Reminder
from handlers.reminders_handler import (
    send_reminder_to_all, 
    calculate_next_send,
    save_reminder,
    request_reminder_schedule
)
from handlers.start_handler import register_start_handler
from handlers.menu_handler import register_menu_handlers
from handlers.analytics_handler import generate_users_report, generate_feedback_report, create_excel_file
from database.models import Admin

# Если у вас нет admin_content_handler, закомментируйте или удалите эту строку
# from handlers.admin_content_handler import register_admin_content_callback_handlers

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
print(f"TOKEN: {API_TOKEN}")

bot = telebot.TeleBot(API_TOKEN)

def send_scheduled_reports(bot_instance):
    """Ежедневная рассылка отчетов HR-отделу"""
    while True:
        try:
            now = datetime.now()
            # Проверяем, что сейчас 10:00 утра
            if now.hour == 10 and now.minute == 0:
                db = SessionLocal()
                try:
                    # Получаем всех администраторов HR
                    hr_admins = db.query(Admin).all()
                    
                    # Генерируем отчеты
                    users_report, users_data = generate_users_report()
                    feedback_report, feedback_data = generate_feedback_report()
                    
                    # Формируем сводное сообщение
                    summary = (
                        "📊 ЕЖЕДНЕВНЫЙ ОТЧЕТ\n\n"
                        f"{users_report}\n"
                        f"{feedback_report}"
                    )
                    
                    # Отправляем всем HR
                    for admin in hr_admins:
                        try:
                            # Отправляем текстовый отчет
                            bot_instance.send_message(admin.auth_token, summary)
                            
                            # Отправляем Excel с данными
                            excel_file, filename = create_excel_file(
                                users_data + feedback_data, 
                                f"report_{now.strftime('%Y%m%d')}.xlsx"
                            )
                            bot_instance.send_document(
                                admin.auth_token, 
                                excel_file, 
                                visible_file_name=filename
                            )
                        except Exception as e:
                            print(f"Не удалось отправить отчет админу {admin.auth_token}: {e}")
                finally:
                    db.close()
        except Exception as e:
            print(f"Ошибка в рассылке отчетов: {e}")
        
        # Проверяем каждую минуту
        time.sleep(60)
        
def reminder_scheduler(bot_instance):
    """Фоновая задача для отправки запланированных напоминаний"""
    while True:
        try:
            now = datetime.now()
            db = SessionLocal()
            
            reminders = db.query(Reminder).filter(
                Reminder.next_send <= now,
                Reminder.is_active == True
            ).all()
            
            for reminder in reminders:
                try:
                    send_reminder_to_all(bot_instance, reminder.text)
                    
                    if reminder.is_recurring:
                        reminder.next_send = calculate_next_send(reminder.interval)
                    else:
                        reminder.is_active = False
                    
                    db.commit()
                except Exception as e:
                    print(f"Error processing reminder {reminder.id}: {e}")
                    db.rollback()
            
            db.close()
        except Exception as e:
            print(f"Error in reminder scheduler: {e}")
        finally:
            time.sleep(60)

if __name__ == "__main__":
    # Регистрация обработчиков
    register_start_handler(bot)
    register_menu_handlers(bot)
    
    # Если у вас есть этот обработчик, раскомментируйте
    # register_admin_content_callback_handlers(bot)
    
    scheduler_thread = threading.Thread(
        target=reminder_scheduler, 
        args=(bot,),
        daemon=True
    )
    
    reports_thread = threading.Thread(
        target=send_scheduled_reports, 
        args=(bot,),
        daemon=True
    )
    reports_thread.start()
    scheduler_thread.start()
    print("Бот запущен и готов к работе!")
    bot.infinity_polling()