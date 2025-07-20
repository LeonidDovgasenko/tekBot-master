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

# Если у вас нет admin_content_handler, закомментируйте или удалите эту строку
# from handlers.admin_content_handler import register_admin_content_callback_handlers

load_dotenv()
API_TOKEN = os.getenv('API_TOKEN')
print(f"TOKEN: {API_TOKEN}")

bot = telebot.TeleBot(API_TOKEN)

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
    scheduler_thread.start()
    
    print("Бот запущен и готов к работе!")
    bot.infinity_polling()