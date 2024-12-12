from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from config import BOT_TOKEN

# Создаем клавиатуру с кнопкой
keyboard = ReplyKeyboardMarkup([['Получить приветствие']], resize_keyboard=True)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет!",
        reply_markup=keyboard
    )

async def hello(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик нажатия на кнопку"""
    if update.message.text == "Получить приветствие":
        await update.message.reply_text("Привет!", reply_markup=keyboard)

if __name__ == '__main__':
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT, hello))
    application.run_polling() 