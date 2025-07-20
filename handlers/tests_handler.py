from telebot import types
from database.content_session import ContentSessionLocal
from database.models import Test, UserTestProgress

def show_tests_menu(bot, message, user_id):
    db = ContentSessionLocal()
    tests = db.query(Test).all()
    markup = types.InlineKeyboardMarkup(row_width=1)
    
    # Проверяем прогресс пользователя
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
    db.close()
    
    bot.send_message(
        message.chat.id,
        "📝 Доступные тесты. Нажмите на тест для прохождения:",
        reply_markup=markup
    )

def add_test(section, title, url):
    db = ContentSessionLocal()
    new_test = Test(section=section, title=title, url=url)
    db.add(new_test)
    db.commit()
    db.close()