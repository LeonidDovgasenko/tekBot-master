# handlers/analytics_handler.py
from telebot import types
from database.session import SessionLocal
from database.models import (  # Добавляем все необходимые модели
    User, 
    Feedback, 
    Reminder, 
    UserTestProgress, 
    Content,
    Test,  # Добавляем импорт Test
    ContentFile  # Добавляем импорт ContentFile
)
from datetime import datetime, timedelta
import pandas as pd
from io import BytesIO

def generate_reminders_report():
    """Сгенерировать отчет по напоминаниям"""
    db = SessionLocal()
    try:
        total_reminders = db.query(Reminder).count()
        active_reminders = db.query(Reminder).filter(Reminder.is_active == True).count()
        missed_reminders = db.query(Reminder).filter(
            Reminder.next_send < datetime.now(),
            Reminder.is_active == True
        ).count()
        
        report = (
            "⏰ ОТЧЕТ ПО НАПОМИНАНИЯМ\n\n"
            f"• Всего напоминаний: {total_reminders}\n"
            f"• Активных напоминаний: {active_reminders}\n"
            f"• Пропущенных напоминаний: {missed_reminders}\n"
        )
        
        reminders_data = []
        reminders = db.query(Reminder).all()
        for r in reminders:
            reminders_data.append({
                "ID": r.id,
                "Текст": r.text[:50] + "..." if len(r.text) > 50 else r.text,
                "Статус": "Активно" if r.is_active else "Неактивно",
                "Следующая отправка": r.next_send.strftime('%Y-%m-%d %H:%M') if r.next_send else "N/A",
                "Интервал": r.interval or "Однократно"
            })
        
        return report, reminders_data
    finally:
        db.close()

def generate_tests_report():
    """Сгенерировать отчет по тестам"""
    db = SessionLocal()
    try:
        from database.models import Test 
        total_tests = db.query(Test).count()
        completed_tests = db.query(UserTestProgress).filter(
            UserTestProgress.completed == True
        ).count()
        
        report = (
            "📝 ОТЧЕТ ПО ТЕСТАМ\n\n"
            f"• Всего тестов: {total_tests}\n"
            f"• Всего пройдено тестов: {completed_tests}\n"
        )
        
        tests_data = []
        tests = db.query(Test).all()
        for test in tests:
            completed_count = db.query(UserTestProgress).filter(
                UserTestProgress.test_id == test.id,
                UserTestProgress.completed == True
            ).count()
            
            tests_data.append({
                "ID": test.id,
                "Название": test.title,
                "Ссылка": test.url,
                "Пройдено раз": completed_count
            })
        
        return report, tests_data
    finally:
        db.close()

def generate_content_report():
    """Сгенерировать отчет по материалам"""
    from database.content_session import ContentSessionLocal
    db = ContentSessionLocal()
    try:
        from database.models import Content, ContentFile

        total_content = db.query(Content).count()
        total_files   = db.query(ContentFile).count()
        
        report = (
            "📚 ОТЧЕТ ПО МАТЕРИАЛАМ\n\n"
            f"• Всего разделов: {total_content}\n"
            f"• Всего файлов: {total_files}\n"
        )
        
        content_data = []
        sections = db.query(Content).all()
        for section in sections:
            files_count = len(section.files)
            content_data.append({
                "Раздел": section.section,
                "Название": section.title,
                "Файлов": files_count
            })
        
        return report, content_data
    finally:
        db.close()
        
def show_analytics_menu(bot, message):
    """Показать меню аналитики"""
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    buttons = [
        types.InlineKeyboardButton("👥 Отчет по пользователям", callback_data="report:users"),
        types.InlineKeyboardButton("💬 Отчет по отзывам", callback_data="report:feedback"),
        types.InlineKeyboardButton("⏰ Отчет по напоминаниям", callback_data="report:reminders"),
        types.InlineKeyboardButton("📊 Отчет по тестам", callback_data="report:tests"),
        types.InlineKeyboardButton("📚 Отчет по материалам", callback_data="report:content"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="training")
    ]
    
    markup.add(*buttons)
    
    bot.send_message(
        message.chat.id,
        "📊 Выберите тип отчета:",
        reply_markup=markup
    )

def generate_users_report():
    """Сгенерировать отчет по пользователям"""
    db = SessionLocal()
    try:
        # Основная статистика
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.last_activity >= datetime.now() - timedelta(days=7)).count()
        
        # Статистика по активности
        new_users_today = db.query(User).filter(User.created_at >= datetime.now() - timedelta(days=1)).count()
        
        # Формирование отчета
        report = (
            "👥 ОТЧЕТ ПО ПОЛЬЗОВАТЕЛЯМ\n\n"
            f"• Всего пользователей: {total_users}\n"
            f"• Активных за последнюю неделю: {active_users}\n"
            f"• Новых пользователей за сегодня: {new_users_today}\n"
        )
        
        # Дополнительные данные для Excel
        users_data = []
        users = db.query(User).all()
        for user in users:
            info = user.user_info  # связанный User_info
            users_data.append({
                "ID": user.id,
                "Имя": info.full_name if info else "N/A",
                "Email": info.mail if info else "N/A",
                "Дата регистрации": user.created_at.strftime('%Y-%m-%d'),
                "Последняя активность": user.last_activity.strftime('%Y-%m-%d %H:%M') if user.last_activity else "N/A"
            })
        
        return report, users_data
    finally:
        db.close()

def generate_feedback_report():
    """Сгенерировать отчет по отзывам"""
    db = SessionLocal()
    try:
        # Основная статистика
        total_feedbacks = db.query(Feedback).count()
        last_week_feedbacks = db.query(Feedback).filter(
            Feedback.created_at >= datetime.now() - timedelta(weeks=1)
        ).count()
        
        # Формирование отчета
        report = (
            "💬 ОТЧЕТ ПО ОТЗЫВАМ\n\n"
            f"• Всего отзывов: {total_feedbacks}\n"
            f"• Отзывов за последнюю неделю: {last_week_feedbacks}\n"
        )
        
        # Дополнительные данные для Excel
        feedbacks_data = []
        feedbacks = db.query(Feedback).order_by(Feedback.created_at.desc()).limit(50).all()
        for fb in feedbacks:
            feedbacks_data.append({
                "ID": fb.id,
                "Пользователь": fb.full_name,
                "Дата": fb.created_at.strftime('%Y-%m-%d %H:%M'),
                "Текст": fb.feedback_text[:100] + "..." if len(fb.feedback_text) > 100 else fb.feedback_text
            })
        
        return report, feedbacks_data
    finally:
        db.close()

# Аналогичные функции для других отчетов:
# generate_reminders_report()
# generate_tests_report()
# generate_content_report()

def create_excel_file(data, filename):
    """Создать Excel файл из данных"""
    df = pd.DataFrame(data)
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Данные')
    output.seek(0)
    return output, filename