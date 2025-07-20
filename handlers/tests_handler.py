from telebot import types
from database.session import SessionLocal
from database.models import Test, UserTestProgress, Admin
import traceback

def show_tests_menu(bot, message, user_id):
    try:
        print("Показать меню тестов вызвано")
        db = SessionLocal()
        tests = db.query(Test).all()
        
        if not tests:
            markup = types.InlineKeyboardMarkup()
            markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="training"))
            bot.send_message(message.chat.id, "📝 На данный момент тесты отсутствуют.", reply_markup=markup)
            return
            
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Проверка прогресса
        completed_tests = {progress.test_id for progress in 
                         db.query(UserTestProgress).filter(
                             UserTestProgress.user_id == user_id,
                             UserTestProgress.completed == True
                         )}
        
        for test in tests:
            emoji = "✅" if test.id in completed_tests else "📝"
            btn = types.InlineKeyboardButton(
                f"{emoji} {test.title}",
                url=test.url,
                callback_data=f"test_start:{test.id}"
            )
            markup.add(btn)
        
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="training"))
        
        bot.send_message(
            message.chat.id,
            "📝 Доступные тесты. Нажмите на тест для прохождения:",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in show_tests_menu: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, "⚠ Произошла ошибка при загрузке тестов")
    finally:
        db.close()

def show_edit_tests_menu(bot, message, user_id):
    try:
        print(f"Показать меню редактирования тестов для пользователя {user_id}")
        
        # Проверка прав администратора
        db_admin = SessionLocal()
        is_admin = db_admin.query(Admin).filter(Admin.auth_token == str(user_id)).first() is not None
        db_admin.close()
        
        if not is_admin:
            print(f"Пользователь {user_id} не является администратором")
            bot.send_message(message.chat.id, "⛔ У вас нет прав для редактирования тестов")
            return
        
        print("Пользователь является администратором")
        
        # Получение списка тестов
        db = SessionLocal()
        tests = db.query(Test).all()
        print(f"Найдено тестов: {len(tests)}")
        
        markup = types.InlineKeyboardMarkup(row_width=1)
        
        # Добавляем кнопки для каждого теста
        for test in tests:
            btn = types.InlineKeyboardButton(
                f"✏️ {test.title}",
                callback_data=f"edit_test:{test.id}"
            )
            markup.add(btn)
        
        # Кнопка добавления нового теста
        markup.add(types.InlineKeyboardButton("➕ Добавить новый тест", callback_data="add_new_test"))
        
        # Кнопка возврата
        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data="training"))
        
        # Отправка сообщения
        print("Отправка меню редактирования тестов")
        bot.send_message(
            message.chat.id,
            "✏️ Редактирование тестов:",
            reply_markup=markup
        )
    except Exception as e:
        print(f"Error in show_edit_tests_menu: {e}")
        traceback.print_exc()
        bot.send_message(message.chat.id, "⚠ Произошла ошибка при загрузке тестов")
    finally:
        if 'db' in locals() and db:
            db.close()

def add_test(section, title, url):
    db = SessionLocal()
    try:
        new_test = Test(section=section, title=title, url=url)
        db.add(new_test)
        db.commit()
        print(f"Добавлен новый тест: {title}")
    except Exception as e:
        db.rollback()
        print(f"Error adding test: {e}")
        traceback.print_exc()
        raise
    finally:
        db.close()