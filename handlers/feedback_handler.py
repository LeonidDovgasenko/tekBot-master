from telebot import types

def ask_feedback(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    buttons = [
        types.InlineKeyboardButton("Оставить отзыв", callback_data="give_feedback"),
        types.InlineKeyboardButton("Пройти опрос", callback_data="take_quiz"),
        types.InlineKeyboardButton("Посмотреть результаты", callback_data="view_results"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")
    ]

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "💬 Обратная связь:\n"
        "Вы можете оставить отзыв, пройти опрос или посмотреть результаты.",
        reply_markup=markup
    )