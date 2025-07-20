from telebot import types
from database.session import SessionLocal
from database.content_session import ContentSessionLocal
import os
from database.models import Content, ContentFile
from sqlalchemy import or_, and_
from datetime import datetime
from database.models import UserTestProgress  # Импорт модели прогресса
from database.content_session import ContentSessionLocal  # Импорт сессии БД

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
    @bot.callback_query_handler(func=lambda call: call.data.startswith("test_start:"))
    def handle_test_start(call):
        test_id = int(call.data.split(":")[1])
        db = ContentSessionLocal()
        
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
        
    @bot.callback_query_handler(func=lambda call: True)
    def handle_callback(call):     
        # --- Подменю "Информация для сотрудников" ---
        # --- Главное меню ---
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
        
        elif call.data == "training_section:training_tests":
            from handlers.tests_handler import show_tests_menu
            show_tests_menu(bot, call.message, call.from_user.id)

        elif call.data == "edit_section:training_tests":
            from handlers.tests_handler import show_edit_tests_menu
            show_edit_tests_menu(bot, call.message, call.from_user.id)
    
        elif call.data == "training_search":
            bot.send_message(call.message.chat.id, "Введите начало названия материала для поиска:")
            bot.register_next_step_handler(call.message, handle_training_search_input)
            
        elif call.data.startswith("training_section:"):
            section = call.data.split(":", 1)[1]
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