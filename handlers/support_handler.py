from telebot import types

def show_support(bot, message):
    markup = types.InlineKeyboardMarkup(row_width=1)

    buttons = [
        types.InlineKeyboardButton("Связаться с HR", callback_data="contact_hr"),
        types.InlineKeyboardButton("Проблемы с ботом?", callback_data="help_bot"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_to_main")
    ]

    markup.add(*buttons)

    bot.send_message(
        message.chat.id,
        "📞 Поддержка:\n"
        "Если у вас возникли трудности — вы можете обратиться за помощью.",
        reply_markup=markup
    )