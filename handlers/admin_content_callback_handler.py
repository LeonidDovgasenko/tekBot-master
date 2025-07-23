from telebot import types
from services.content_service import update_content, add_file_to_content, delete_content_file, get_content_files
import os
from services.sections import SECTIONS
from database.models import Test, UserTestProgress, Admin, User_info
from database.models import CompanyTour
from database.content_session import ContentSessionLocal
from database.session import SessionLocal
from sqlalchemy import func
from datetime import datetime

def is_admin(user_id):
    """Проверяет, является ли пользователь администратором"""
    db = SessionLocal()
    admin = db.query(Admin).filter(Admin.auth_token == str(user_id)).first()
    db.close()
    return admin is not None

def register_admin_content_callback_handlers(bot):
    @bot.callback_query_handler(func=lambda call: call.data.startswith("edit_section:"))
    def start_edit_section(call):
        _, section, back_path = call.data.split(":")
        info = SECTIONS.get(section)

        if not info:
            bot.answer_callback_query(call.id, "Раздел не найден")
            return

        markup = types.InlineKeyboardMarkup()
        buttons = [
            types.InlineKeyboardButton("✏️ Изменить заголовок", callback_data=f"change_title:{section}"),
            types.InlineKeyboardButton("✏️ Изменить текст", callback_data=f"change_text:{section}"),
        ]
        if info.get("allow_file"):
            buttons.append(types.InlineKeyboardButton("📎 Добавить файл", callback_data=f"add_file:{section}"))
            buttons.append(types.InlineKeyboardButton("🗂 Просмотреть файлы", callback_data=f"view_files:{section}"))

        buttons.append(types.InlineKeyboardButton("⬅ Назад", callback_data=back_path))
        markup.add(*buttons)

        bot.send_message(
            chat_id=call.message.chat.id,
            text=f"Выберите действие для «{info['title']}»",
            reply_markup=markup
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("view_files:"))
    def show_files_list(call):
        section = call.data.split(":", 1)[1]
        files = get_content_files(section)

        info = SECTIONS[section]
        markup = types.InlineKeyboardMarkup()

        if not files:
            bot.send_message(call.message.chat.id, "Файлы не найдены")
            return

        for file in files:
            btn = types.InlineKeyboardButton(f"🗑 {os.path.basename(file.file_path)}", callback_data=f"delete_file:{file.id}")
            markup.add(btn)

        markup.add(types.InlineKeyboardButton("⬅ Назад", callback_data=f"edit_section:{section}"))
        bot.send_message(call.message.chat.id, f"📎 Файлы в разделе «{info['title']}»:", reply_markup=markup)

    # --- Изменить заголовок ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("change_title:"))
    def request_new_title(call):
        section = call.data.split(":", 1)[1]
        info = SECTIONS[section]
        msg = bot.send_message(call.message.chat.id, f"Введите новый заголовок для «{info['title']}»")
        bot.register_next_step_handler(msg, process_title, section, info)

    def process_title(message, section, info):
        title = message.text.strip()
        update_content(section=section, title=title)
        bot.send_message(message.chat.id, "✅ Заголовок обновлён")

    # --- Изменить текст ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("change_text:"))
    def request_new_text(call):
        section = call.data.split(":", 1)[1]
        msg = bot.send_message(call.message.chat.id, "Введите новый текст:")
        bot.register_next_step_handler(msg, process_text, section)

    def process_text(message, section):
        text = message.text.strip()
        update_content(section=section, text=text)
        bot.send_message(message.chat.id, "✅ Текст обновлён")

    # --- Добавить файл ---
    @bot.callback_query_handler(func=lambda call: call.data.startswith("add_file:"))
    def request_new_file(call):
        section = call.data.split(":", 1)[1]
        info = SECTIONS[section]
        msg = bot.send_message(call.message.chat.id, f"Загрузите файл для «{info['title']}»")
        bot.register_next_step_handler(msg, process_file, section)

    def process_file(message, section):
        try:
            # Проверяем размер файла перед обработкой
            if message.document:
                if message.document.file_size > 50 * 1024 * 1024:  # 50 МБ
                    bot.send_message(message.chat.id, "❌ Файл слишком большой (макс. 50 МБ)")
                    return
                file_info = bot.get_file(message.document.file_id)
                file_name = message.document.file_name
            elif message.video:
                if message.video.file_size > 50 * 1024 * 1024:
                    bot.send_message(message.chat.id, "❌ Видео слишком большое (макс. 50 МБ). Сожмите видео перед отправкой.")
                    return
                file_info = bot.get_file(message.video.file_id)
                file_name = f"video_{message.video.file_unique_id}.mp4"
            else:
                bot.send_message(message.chat.id, "❌ Пожалуйста, отправьте файл (документ или видео)")
                return

            # Создаем папку и сохраняем файл
            os.makedirs(f"data/{section}", exist_ok=True)
            file_path = f"data/{section}/{file_name}"
            
            # Скачиваем файл по частям для больших файлов
            with open(file_path, 'wb') as f:
                downloaded = 0
                chunk_size = 1024 * 1024  # 1 МБ
                while downloaded < file_info.file_size:
                    chunk = bot.download_file(file_info.file_path, offset=downloaded, length=chunk_size)
                    f.write(chunk)
                    downloaded += len(chunk)

            add_file_to_content(section=section, file_path=file_path)
            bot.send_message(message.chat.id, f"✅ Файл {file_name} успешно сохранен ({file_info.file_size//1024} KB)")

        except Exception as e:
            print(f"Ошибка обработки файла: {e}")
            bot.send_message(message.chat.id, f"❌ Ошибка: {str(e)}")
        
    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_file:"))
    def delete_file(call):
        file_id = int(call.data.split(":", 1)[1])
        deleted = delete_content_file(file_id)
        if deleted:
            bot.send_message(call.message.chat.id, "✅ Файл успешно удалён")
        else:
            bot.send_message(call.message.chat.id, "❌ Ошибка при удалении файла")
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("add_test:"))
    def request_new_test(call):
        section = call.data.split(":", 1)[1]
        msg = bot.send_message(call.message.chat.id, "Введите название теста:")
        bot.register_next_step_handler(msg, process_test_title, section)

    def process_test_title(message, section):
        bot.send_message(message.chat.id, "Теперь отправьте ссылку на тест (Google Forms и т.д.):")
        bot.register_next_step_handler(message, process_test_url, section, message.text)

    def process_test_url(message, section, title):
        if not message.text.startswith("http"):
            bot.send_message(message.chat.id, "❌ Некорректная ссылка")
            return
        
        from handlers.tests_handler import add_test
        add_test(section, title, message.text)
        bot.send_message(message.chat.id, "✅ Тест успешно добавлен!")

    @bot.message_handler(commands=['test_stats'])
    def show_test_stats(message):
        if not is_admin(message.from_user.id):
            return
            
        db = ContentSessionLocal()
        stats = db.query(
            Test.title,
            func.count(UserTestProgress.id).filter(UserTestProgress.completed == True)
        ).join(UserTestProgress).group_by(Test.title).all()
        
        response = "📊 Статистика прохождения тестов:\n\n"
        for title, count in stats:
            response += f"{title}: {count} прохождений\n"
            
        bot.send_message(message.chat.id, response)
        db.close()
    @bot.callback_query_handler(func=lambda call: call.data == "edit_section:training_tests")
    def handle_edit_tests(call):
        bot.send_message(call.message.chat.id, "📝 Введите название теста:")
        bot.register_next_step_handler(call.message, get_test_title)

    def get_test_title(message):
        title = message.text
        bot.send_message(message.chat.id, "🔗 Введите ссылку на тест:")
        bot.register_next_step_handler(message, lambda msg: save_test(msg, title))

    def save_test(message, title):
        url = message.text
        from database.models import Test
        from database.content_session import ContentSessionLocal

        db = ContentSessionLocal()
        test = Test(section="training_tests", title=title, url=url)
        db.add(test)
        db.commit()
        db.close()

        bot.send_message(message.chat.id, "✅ Тест добавлен!")
