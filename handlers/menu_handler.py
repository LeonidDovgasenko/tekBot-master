from telebot import types
from database.session import SessionLocal
from database.content_session import ContentSessionLocal
import os
from database.models import Content, ContentFile
from sqlalchemy import or_, and_
from datetime import datetime
from database.models import UserTestProgress  # Импорт модели прогресса
from database.content_session import ContentSessionLocal  # Импорт сессии БД
from handlers.feedback_handler import request_feedback_text, show_feedbacks, ask_feedback
from handlers.reminders_handler import (
    save_reminder,
    request_reminder_schedule,
    show_reminders_menu,
    request_reminder_text,
    show_scheduled_reminders,
    request_reminder_to_delete
)
from handlers.analytics_handler import show_analytics_menu, generate_users_report, generate_feedback_report
from handlers.analytics_handler import (
    show_analytics_menu, 
    generate_users_report, 
    generate_feedback_report,
    generate_reminders_report,
    generate_tests_report,
    generate_content_report,
    create_excel_file  # Импортируем функцию создания Excel
)
from database.models import User  # Импортируем модель User


def register_menu_handlers(bot):
    def handle_training_search_input(message):
        query = message.text.strip().lower()
        if len(query) < 2:
            bot.send_message(message.chat.id, "🔍 Введите минимум 2 символа для поиска")
            return

        db = ContentSessionLocal()
        try:
            training_sections = [
                "training_materials_pdf",
                "training_materials_video", 
                "training_materials_presentation"
            ]

            # Ищем контент в обучающих разделах
            results = db.query(Content).filter(
                Content.section.in_(training_sections)
            ).all()

            found_files = False
            for content in results:
                for file in content.files:
                    # Получаем только имя файла (без пути)
                    file_name = os.path.basename(file.file_path).lower()
                    
                    # Проверяем совпадение с запросом
                    if query in file_name:
                        if os.path.exists(file.file_path):
                            try:
                                with open(file.file_path, 'rb') as f:
                                    bot.send_document(
                                        message.chat.id,
                                        f,
                                        visible_file_name=os.path.basename(file.file_path)
                                    )
                                    found_files = True
                            except Exception as e:
                                print(f"Ошибка отправки файла: {e}")
                        else:
                            print(f"Файл не существует: {file.file_path}")

            if not found_files:
                bot.send_message(message.chat.id, "❌ В обучающих материалах ничего не найдено")

        except Exception as e:
            print(f"Ошибка при поиске: {e}")
            bot.send_message(message.chat.id, "⚠ Ошибка при выполнении поиска")
        finally:
            db.close()
            
    @bot.callback_query_handler(func=lambda call: call.data == "analytics_menu")
    def handle_analytics_menu(call):
        show_analytics_menu(bot, call.message)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("report:"))
    def handle_report_request(call):
        report_type = call.data.split(":")[1]
        
        if report_type == "users":
            report, excel_data = generate_users_report()
            bot.send_message(call.message.chat.id, report)
            
            # Отправка Excel файла
            excel_file, filename = create_excel_file(excel_data, "users_report.xlsx")
            bot.send_document(call.message.chat.id, excel_file, visible_file_name=filename)
            
        elif report_type == "feedback":
            report, excel_data = generate_feedback_report()
            bot.send_message(call.message.chat.id, report)
            
            # Отправка Excel файла
            excel_file, filename = create_excel_file(excel_data, "feedback_report.xlsx")
            bot.send_document(call.message.chat.id, excel_file, visible_file_name=filename)
        
        elif report_type == "reminders":
            # генерируем и отправляем отчёт по напоминаниям
            report, data = generate_reminders_report()
            bot.send_message(call.message.chat.id, report)

            # создаём Excel и шлём файл
            excel_file, filename = create_excel_file(data, "reminders_report.xlsx")
            bot.send_document(call.message.chat.id, excel_file, visible_file_name=filename)
            
        elif report_type == "tests":
            report, excel_data = generate_tests_report()
            bot.send_message(call.message.chat.id, report)
            excel_file, filename = create_excel_file(excel_data, "tests_report.xlsx")
            bot.send_document(call.message.chat.id, excel_file, visible_file_name=filename)

        elif report_type == "content":
            report, excel_data = generate_content_report()
            bot.send_message(call.message.chat.id, report)
            excel_file, filename = create_excel_file(excel_data, "content_report.xlsx")
            bot.send_document(call.message.chat.id, excel_file, visible_file_name=filename)
            
    @bot.callback_query_handler(func=lambda call: call.data == "reminders")
    def handle_reminders(call):
        show_reminders_menu(bot, call.message)

    @bot.callback_query_handler(func=lambda call: call.data == "send_reminder")
    def handle_send_reminder(call):
        request_reminder_text(bot, call)

    @bot.callback_query_handler(func=lambda call: call.data == "configure_reminders")
    def handle_configure_reminders(call):
        show_scheduled_reminders(bot, call)

    @bot.callback_query_handler(func=lambda call: call.data == "delete_reminder_menu")
    def handle_delete_reminder_menu(call):
        request_reminder_to_delete(bot, call)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reminder_type:"))
    def handle_reminder_type(call):
        parts = call.data.split(":", 2)
        r_type = parts[1]
        text = parts[2]
        
        if r_type == "instant":
            # Сохраняем и отправляем немедленно
            if save_reminder(bot, text, is_instant=True):
                bot.send_message(call.message.chat.id, "✅ Напоминание отправлено всем пользователям!")
            else:
                bot.send_message(call.message.chat.id, "⚠️ Ошибка при отправке напоминания")
        else:
            # Запрашиваем интервал для повторяющихся напоминаний
            request_reminder_schedule(bot, call, text)

    @bot.callback_query_handler(func=lambda call: call.data.startswith("reminder_interval:"))
    def handle_reminder_interval(call):
        parts = call.data.split(":", 2)
        interval = parts[1]
        text = parts[2]
        
        # Сохраняем напоминание с интервалом
        if save_reminder(bot, text, interval=interval):
            bot.send_message(call.message.chat.id, f"✅ Повторяющееся напоминание настроено ({interval})!")
        else:
            bot.send_message(call.message.chat.id, "⚠️ Ошибка при настройке напоминания")
            
    @bot.callback_query_handler(func=lambda call: call.data == "give_feedback")
    def handle_give_feedback(call):
        request_feedback_text(bot, call)

    @bot.callback_query_handler(func=lambda call: call.data == "view_feedbacks")
    def handle_view_feedbacks(call):
        show_feedbacks(bot, call)

    @bot.callback_query_handler(func=lambda call: call.data == "take_quiz")
    def handle_take_quiz(call):
        bot.send_message(call.message.chat.id, "📝 Опрос находится в разработке")
        ask_feedback(bot, call.message)  # Вернуться в меню обратной связи
        
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_tests_section:"))
    def handle_edit_tests(call):
        print(f"Обработчик редактирования тестов вызван: {call.data}")
        from handlers.tests_handler import show_edit_tests_menu
        show_edit_tests_menu(bot, call.message, call.from_user.id)
        bot.answer_callback_query(call.id)  # Важно: подтверждаем обработку callback
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_test:"))
    def handle_edit_test(call):
        test_id = int(call.data.split(":")[1])
        #print(f"Редактирование теста ID: {test_id}")
        # Реализуйте логику редактирования теста
        bot.send_message(call.message.chat.id, f"Редактирование теста ID: {test_id}")

    @bot.callback_query_handler(func=lambda call: call.data == "add_new_test")
    def handle_add_new_test(call):
        #print("Добавление нового теста")
        # Реализуйте логику добавления нового теста
        bot.send_message(call.message.chat.id, "Добавление нового теста")
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith("test_start:"))
    def handle_test_start(call):
        from database.session import SessionLocal
        test_id = int(call.data.split(":")[1])
        db = SessionLocal()
        
        # Отмечаем тест как пройденный
        progress = db.query(UserTestProgress).filter(
            UserTestProgress.user_id == call.from_user.id,
            UserTestProgress.test_id == test_id
        ).first()
        
        if not progress:
            progress = UserTestProgress(
                user_id=call.from_user.id,
                test_id=test_id,
                completed=True,
                completed_at=datetime.now()
            )
            db.add(progress)
        elif not progress.completed:
            progress.completed = True
            progress.completed_at = datetime.now()
        
        db.commit()
        db.close()
        
        bot.answer_callback_query(call.id, "Тест отмечен как пройденный!")

    @bot.callback_query_handler(func=lambda call: call.data.startswith("register_tour:"))
    def handle_register_tour(call):
        from database.session import SessionLocal
        from database.models import TourRegistration, CompanyTour, User_info
        from datetime import datetime

        tour_id = int(call.data.split(":")[1])
        user_auth_token = str(call.from_user.id)

        db = SessionLocal()

        # Проверяем, зарегистрирован ли уже
        existing = db.query(TourRegistration).filter_by(
            tour_id=tour_id,
            user_auth_token=user_auth_token
        ).first()

        if existing:
            bot.answer_callback_query(call.id, "Вы уже зарегистрированы на эту экскурсию.")
            db.close()
            return

        # Проверяем наличие мест
        tour = db.query(CompanyTour).filter_by(id=tour_id).first()
        if not tour:
            bot.answer_callback_query(call.id, "Экскурсия не найдена.")
            db.close()
            return

        if len(tour.registrations) >= tour.max_participants:
            bot.answer_callback_query(call.id, "Мест больше нет 😢")
            db.close()
            return

        # Добавляем регистрацию
        registration = TourRegistration(
            tour_id=tour_id,
            user_auth_token=user_auth_token,
            registered_at=datetime.now()
        )
        db.add(registration)
        db.commit()
        db.close()

        bot.answer_callback_query(call.id, "Вы успешно записались на экскурсию! 🎉")
        
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):     
        # —————— Обновление last_activity ——————
        from datetime import datetime
        from database.models import User
        from database.session import SessionLocal

        db = SessionLocal()
        user = db.query(User).filter(User.auth_token == str(call.from_user.id)).first()
        if user:
            user.last_activity = datetime.now()
            db.commit()
        db.close()
        # ————————————————————————————————
        # --- Подменю "Информация для сотрудников" ---
        # --- Главное меню ---
        db = SessionLocal()
        try:
            user = db.query(User).filter(User.auth_token == str(call.from_user.id)).first()
            if user:
                user.last_activity = datetime.now()
                db.commit()
        except:
            pass
        finally:
            db.close()
        #print(f"Обработка callback: {call.data}")  # Добавьте эту строку
        if call.data == "info":
            from handlers.info_handler import show_info_menu
            show_info_menu(bot, call.message)
        elif call.data == "training":
            from handlers.emp_info_handler import show_employee_info_menu
            show_employee_info_menu(bot, call.message)
        elif call.data == "faq":
            from handlers.faq_handler import show_faq_menu
            show_faq_menu(bot, call.message)
        elif call.data == "feedback":
            from handlers.feedback_handler import ask_feedback
            ask_feedback(bot, call.message)
        elif call.data == "support":
            from handlers.support_handler import show_support
            show_support(bot, call.message)

        # --- Подменю "Информация о компании" ---
        elif call.data == "history":
            db = ContentSessionLocal()
            content = db.query(Content).filter(Content.section == "history").first()
            if content:
                bot.send_message(call.message.chat.id, f"📌 {content.title}\n\n{content.text}")
                for file in content.files:
                    if os.path.exists(file.file_path):
                        with open(file.file_path, "rb") as f:
                            bot.send_document(call.message.chat.id, f)
            else:
                bot.send_message(call.message.chat.id, "Информация пока недоступна.")
            db.close()
            
        elif call.data == "training_tests":
            from handlers.tests_handler import show_tests_menu
            show_tests_menu(bot, call.message, call.from_user.id)
    
        elif call.data == "values":
            db = ContentSessionLocal()
            content = db.query(Content).filter(Content.section == "values").first()
            if content:
                bot.send_message(call.message.chat.id, f"💎 {content.title}\n\n{content.text}")
                for file in content.files:
                    if os.path.exists(file.file_path):
                        with open(file.file_path, "rb") as f:
                            bot.send_document(call.message.chat.id, f)
            else:
                bot.send_message(call.message.chat.id, "Информация пока недоступна.")
            db.close()



        elif call.data == "training":
            from handlers.emp_info_handler import show_employee_info_menu
            show_employee_info_menu(bot, call.message)
            
        elif call.data == "training_materials":
            from handlers.training_materials import show_training_menu
            show_training_menu(bot, call.message)
            
        elif call.data == "training_categories":
            from handlers.training_materials import show_training_categories
            show_training_categories(bot, call)
    
        elif call.data == "training_search":
            bot.send_message(call.message.chat.id, "Введите начало названия материала для поиска:")
            bot.register_next_step_handler(call.message, handle_training_search_input)
            
        elif call.data.startswith("training_section:"):
            section = call.data.split(":", 1)[1]
            if section == "training_tests":
                from handlers.tests_handler import show_tests_menu
                show_tests_menu(bot, call.message, call.from_user.id)
            else:
                from handlers.training_materials import show_training_by_section
                show_training_by_section(bot, call, section)
            
        elif call.data == "company_tours":
            from handlers.emp_info_handler import show_company_tours
            show_company_tours(bot, call.message)


        elif call.data == "virtual_tour":
            from handlers.emp_info_handler import show_virtual_tour
            show_virtual_tour(bot, call.message)

        elif call.data == "org_structure":
            from handlers.emp_info_handler import show_organizational_structure
            show_organizational_structure(bot, call.message)

        elif call.data == "canteen":
            from handlers.emp_info_handler import show_canteen_info
            show_canteen_info(bot, call.message)

        elif call.data == "corporate_events":
            from handlers.emp_info_handler import show_corporate_events
            show_corporate_events(bot, call.message)

        elif call.data == "document_filling":
            from handlers.emp_info_handler import show_document_filling
            show_document_filling(bot, call.message)
            
                # FAQ обработчики


        elif call.data == "faq_list":
            from handlers.faq_handler import show_question_list
            show_question_list(bot, call)

        elif call.data.startswith("faq_show:"):
            from handlers.faq_handler import show_question_detail
            question_id = int(call.data.split(":")[1])
            show_question_detail(bot, call, question_id)

        elif call.data == "faq_ask":
            from handlers.faq_handler import ask_question
            ask_question(bot, call.message)

        elif call.data == "faq_admin":
            from handlers.faq_handler import show_unanswered_questions
            show_unanswered_questions(bot, call)

        elif call.data.startswith("faq_admin_detail:"):
            from handlers.faq_handler import show_question_admin_options
            question_id = int(call.data.split(":")[1])
            show_question_admin_options(bot, call, question_id)

        elif call.data.startswith("faq_answer:"):
            from handlers.faq_handler import request_answer
            question_id = int(call.data.split(":")[1])
            request_answer(bot, call, question_id)

        elif call.data.startswith("faq_delete:"):
            from handlers.faq_handler import confirm_delete_question
            question_id = int(call.data.split(":")[1])
            confirm_delete_question(bot, call, question_id)

        elif call.data.startswith("faq_delete_confirm:"):
            from handlers.faq_handler import delete_question_handler
            question_id = int(call.data.split(":")[1])
            delete_question_handler(bot, call, question_id)

        # --- Кнопка "Назад" ---
        elif call.data == "back_to_main":
            from handlers.start_handler import show_main_menu
            show_main_menu(bot, call.message)

        else:
            bot.answer_callback_query(call.id, "Функция пока не реализована")
