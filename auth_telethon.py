from telethon import TelegramClient
import os
import asyncio

# Получаем данные из переменных окружения
API_ID = int(os.environ.get('API_ID', 0))
API_HASH = os.environ.get('API_HASH')

if not API_ID or not API_HASH:
    print("Ошибка: Не установлены переменные окружения API_ID и/или API_HASH")
    print("Установите их командой:")
    print('heroku config:set API_ID="ваш_api_id" API_HASH="ваш_api_hash" -a telegram-listener')
    exit(1)

async def auth():
    print("Начинаем процесс авторизации...")
    
    # Создаем клиент и сохраняем сессию в файл
    client = TelegramClient('bot_session', API_ID, API_HASH)
    
    try:
        print("Подключаемся к Telegram...")
        await client.start()
        
        # Проверяем авторизацию
        if await client.is_user_authorized():
            print("\nАвторизация успешна!")
            print("Файл сессии создан: bot_session.session")
            print("Теперь вы можете использовать бота")
        else:
            print("Ошибка авторизации")
            
    except Exception as e:
        print(f"Произошла ошибка: {str(e)}")
    finally:
        await client.disconnect()

if __name__ == "__main__":
    asyncio.run(auth()) 