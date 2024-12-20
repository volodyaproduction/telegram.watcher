import os

# Получаем значения из переменных окружения
BOT_TOKEN = os.environ.get('BOT_TOKEN')
API_ID = os.environ.get('API_ID')
API_HASH = os.environ.get('API_HASH')

# Проверка наличия необходимых переменных
if not all([BOT_TOKEN, API_ID, API_HASH]):
    raise ValueError(
        "Отсутствуют необходимые переменные окружения. "
        "Убедитесь, что установлены BOT_TOKEN, API_ID и API_HASH"
    )

# Конвертируем API_ID в int, так как Heroku хранит все как строки
API_ID = int(API_ID)