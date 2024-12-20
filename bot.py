import os

# Получаем конфигурацию из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH')

from telegram import Update, InputMediaPhoto
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
from telethon import TelegramClient, events
import logging
import asyncio
import re
from typing import Optional, Set, List, Dict
from storage import UserSettingsStorage
import base64

# Настраиваем логирование
logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

application: Optional[Application] = None
client: Optional[TelegramClient] = None

# Структуры данных для хранения настроек пользователей
storage = UserSettingsStorage()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    try:
        user_id = update.effective_chat.id
        logger.info(f"Пользователь {user_id} запустил бота")
        
        # Получаем настройки пользователя из хранилища
        settings = storage.get_user_settings(user_id)

        welcome_text = (
            "Привет! Я бот для мониторинга Telegram каналов.\n\n"
            "Давайте настроим каналы для отслеживания.\n"
            "Отправьте список каналов через пробел, используя @ в начале.\n"
            "Например: @channel1 @channel2"
        )
        
        await update.message.reply_text(welcome_text)
        context.user_data['awaiting_input'] = 'channels'
        
    except Exception as e:
        logger.error(f"Ошибка в обработчике start: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def channels_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список отслеживаемых каналов"""
    user_id = update.effective_chat.id
    if user_id not in storage.get_all_settings() or not storage.get_all_settings()[user_id]['channels']:
        await update.message.reply_text("Список каналов пуст")
    else:
        channels = '\n'.join(storage.get_all_settings()[user_id]['channels'])
        await update.message.reply_text(f"Отслеживаемые каналы:\n{channels}")

async def channels_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменить список каналов"""
    await update.message.reply_text(
        "Отправьте новый список каналов через пробел, используя @ в начале.\n"
        "Например: @channel1 @channel2"
    )
    context.user_data['awaiting_input'] = 'channels'

async def keywords_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Показать список ключевых слов"""
    user_id = update.effective_chat.id
    if user_id not in storage.get_all_settings() or not storage.get_all_settings()[user_id]['keywords']:
        await update.message.reply_text("Список ключевых слов пуст")
    else:
        keywords = '\n'.join(f'"{kw}"' for kw in storage.get_all_settings()[user_id]['keywords'])
        await update.message.reply_text(f"Ключевые слова для поиска:\n{keywords}")

async def keywords_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Изменить список ключевых слов"""
    await update.message.reply_text(
        "Отправьте ключевые слова в кавычках через пробел.\n"
        'Например: "data analyst" "python developer"'
    )
    context.user_data['awaiting_input'] = 'keywords'

async def stop(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Остановить мониторинг"""
    user_id = update.effective_chat.id
    if user_id in storage.get_all_settings():
        settings = storage.get_all_settings()[user_id]
        settings['active'] = False
        storage.update_user_settings(user_id, settings)
        await update.message.reply_text("Мониторинг остановлен")
    else:
        await update.message.reply_text("Бот не был запущен")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений"""
    try:
        user_id = update.effective_chat.id
        awaiting = context.user_data.get('awaiting_input')
        
        if awaiting == 'channels':
            # Обработка списка каналов
            channels = {
                channel.strip() 
                for channel in update.message.text.split() 
                if channel.startswith('@')
            }
            if channels:
                settings = storage.get_user_settings(user_id)
                settings['channels'] = channels
                storage.update_user_settings(user_id, settings)
                await update.message.reply_text(
                    "Каналы сохранены!\n\n"
                    "Теперь отправьте ключевые слова в кавычках через пробел.\n"
                    'Например: "data analyst" "python developer"'
                )
                context.user_data['awaiting_input'] = 'keywords'
            else:
                await update.message.reply_text(
                    "Пожалуйста, укажите каналы, начиная с @\n"
                    "Например: @channel1 @channel2"
                )
                
        elif awaiting == 'keywords':
            # Обработка ключевых слов
            pattern = r'"([^"]+)"'
            keywords = set(re.findall(pattern, update.message.text))
            if keywords:
                settings = storage.get_user_settings(user_id)
                settings['keywords'] = keywords
                settings['active'] = True
                storage.update_user_settings(user_id, settings)
                await update.message.reply_text(
                    "Настройка завершена! Бот начал мониторинг.\n\n"
                    "Используйте следующие команды для управления:\n"
                    "/channels_list - показать список каналов\n"
                    "/channels_edit - изменить каналы\n"
                    "/keywords_list - показать ключевые слова\n"
                    "/keywords_edit - изменить ключевые слова\n"
                    "/stop - остановить мониторинг"
                )
                context.user_data.pop('awaiting_input', None)
            else:
                await update.message.reply_text(
                    'Пожалуйста, укажите ключевые слова в кавычках.\n'
                    'Например: "data analyst" "python developer"'
                )
    except Exception as e:
        logger.error(f"Ошибка в обработчике текста: {e}")
        await update.message.reply_text("Произошла ошибка. Пожалуйста, попробуйте позже.")

async def forward_formatted_message(message, chat_id):
    """Форматирование и отправка сообщения пользователю"""
    try:
        # Форматируем заголовок сообщения
        channel_info = f"Канал: {message.chat.title} (@{message.chat.username})"
        message_link = f"https://t.me/{message.chat.username}/{message.id}"
        header = f"{channel_info}\n{message_link}\n\n"
        
        # Получаем текст сообщения
        message_text = ""
        if hasattr(message, 'text') and message.text:
            message_text = message.text
        elif hasattr(message, 'caption') and message.caption:
            message_text = message.caption
            
        full_text = header + message_text

        # Если это альбом (карусель)
        if hasattr(message, 'grouped_id') and message.grouped_id:
            # Создаем временную директорию
            temp_dir = 'temp_photos'
            if not os.path.exists(temp_dir):
                os.makedirs(temp_dir)
            
            temp_files = []
            media_group = []
            
            try:
                # Сначала сохраняем текущее фото
                if hasattr(message, 'media') and message.media:
                    temp_path = os.path.join(temp_dir, f"photo_main.jpg")
                    await message.download_media(temp_path)
                    temp_files.append(temp_path)
                
                # Ищем остальные фото в том же альбоме
                messages = await client.get_messages(
                    message.chat_id,
                    limit=10,
                    min_id=message.id-10,
                    max_id=message.id+10
                )
                
                for msg in messages:
                    if (hasattr(msg, 'grouped_id') and 
                        msg.grouped_id == message.grouped_id and 
                        msg.id != message.id and 
                        hasattr(msg, 'media') and msg.media):
                        temp_path = os.path.join(temp_dir, f"photo_{msg.id}.jpg")
                        await msg.download_media(temp_path)
                        temp_files.append(temp_path)
                
                # Создаем медиа группу
                for i, file_path in enumerate(temp_files):
                    with open(file_path, 'rb') as photo_file:
                        if i == 0:
                            media_group.append(
                                InputMediaPhoto(
                                    photo_file.read(),
                                    caption=full_text
                                )
                            )
                        else:
                            media_group.append(InputMediaPhoto(photo_file.read()))
                
                if media_group:
                    await application.bot.send_media_group(
                        chat_id=chat_id,
                        media=media_group
                    )
            finally:
                # Очищаем временные файлы
                for file_path in temp_files:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                    os.rmdir(temp_dir)
        
        # Если одиночное сообщение с фото
        elif hasattr(message, 'media') and message.media:
            temp_path = 'temp_single.jpg'
            await message.download_media(temp_path)
            
            try:
                with open(temp_path, 'rb') as photo_file:
                    await application.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo_file.read(),
                        caption=full_text
                    )
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Если просто текст
        else:
            await application.bot.send_message(
                chat_id=chat_id,
                text=full_text,
                disable_web_page_preview=True
            )
            
    except Exception as e:
        logger.error(f"Ошибка в forward_formatted_message: {e}")
        raise e

async def forward_message_to_subscribers(message):
    """Пересылка сообщения подписчикам"""
    global application, client
    try:
        if application is None:
            logger.error("Application не инициализирован")
            return
            
        # Проверяем, что у сообщения есть чат и юзернейм
        if not hasattr(message, 'chat') or not message.chat or not hasattr(message.chat, 'username'):
            logger.info("Пропускаем сообщение без информации о канале")
            return
            
        # Проверяем каждого пользователя
        for user_id, settings in storage.get_all_settings().items():
            if not settings['active']:
                continue
                
            # Проверяем, что сообщение из отслеживаемого канала
            channel_username = f"@{message.chat.username}"
            if channel_username not in settings['channels']:
                continue
                
            # Проверяем наличие ключевых слов
            message_text = ""
            if hasattr(message, 'text') and message.text:
                message_text = message.text
            elif hasattr(message, 'caption') and message.caption:
                message_text = message.caption
                
            if not message_text:
                logger.info("Пропускаем сообщение без текста")
                continue
                
            if not any(kw.lower() in message_text.lower() for kw in settings['keywords']):
                continue
                
            try:
                # Форматируем сообщение и отправляем
                await forward_formatted_message(message, user_id)
                logger.info(f"Сообщение успешно отправлено пользователю {user_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки сообщения пользователю {user_id}: {e}")
                
    except Exception as e:
        logger.error(f"Ошибка в forward_message_to_subscribers: {e}")

async def main():
    """Запуск бота"""
    global application, client
    
    try:
        # Инициализация Telethon клиента
        logger.info("Инициализация Telethon клиента...")
        session_data = os.environ.get('TELETHON_SESSION')
        if session_data:
            # Декодируем и сохраняем сессию во временный файл
            session_file = 'bot_session.session'
            with open(session_file, 'wb') as f:
                f.write(base64.b64decode(session_data))
            
            client = TelegramClient(session_file, API_ID, API_HASH)
        else:
            raise ValueError("Отсутствует TELETHON_SESSION")
        
        # Добавляем обработчик событий Telethon
        @client.on(events.NewMessage)
        async def handle_new_message(event):
            if event.message:
                await forward_message_to_subscribers(event.message)

        # Инициализация PTB
        application = Application.builder().token(BOT_TOKEN).build()
        
        # Добавляем обработчики команд
        application.add_handler(CommandHandler("start", start))
        application.add_handler(CommandHandler("channels_list", channels_list))
        application.add_handler(CommandHandler("channels_edit", channels_edit))
        application.add_handler(CommandHandler("keywords_list", keywords_list))
        application.add_handler(CommandHandler("keywords_edit", keywords_edit))
        application.add_handler(CommandHandler("stop", stop))
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
        
        # Запускаем оба клиента
        await client.start()
        await application.initialize()
        await application.start()
        
        # Запускаем polling
        await application.updater.start_polling()
        await asyncio.Event().wait()
        
    except Exception as e:
        logger.error(f"Критическая ошибка: {e}")
        raise e
    finally:
        if application:
            await application.stop()
        if client:
            await client.disconnect()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"Неожиданная ошибка: {e}")