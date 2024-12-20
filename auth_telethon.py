from telethon import TelegramClient
from config import API_ID, API_HASH

async def auth():
    # Создаем клиент и сохраняем сессию в файл
    client = TelegramClient('bot_session', API_ID, API_HASH)
    await client.start()
    
    # Проверяем авторизацию
    if await client.is_user_authorized():
        print("Авторизация успешна! Файл сессии создан: bot_session.session")
    else:
        print("Ошибка авторизации")
    
    await client.disconnect()

if __name__ == "__main__":
    import asyncio
    asyncio.run(auth()) 