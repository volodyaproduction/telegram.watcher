import json
import os
from typing import Dict, Set
import logging

logger = logging.getLogger(__name__)

class UserSettingsStorage:
    def __init__(self, filename: str = 'user_settings.json'):
        self.filename = filename
        self.settings: Dict[int, Dict] = {}
        self.load_settings()
    
    def load_settings(self) -> None:
        """Загрузка настроек из файла"""
        try:
            if os.path.exists(self.filename):
                with open(self.filename, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    # Конвертируем строковые ключи обратно в int
                    self.settings = {
                        int(user_id): {
                            'channels': set(channels),
                            'keywords': set(keywords),
                            'active': active
                        }
                        for user_id, settings in data.items()
                        for channels, keywords, active in [(
                            settings['channels'],
                            settings['keywords'],
                            settings['active']
                        )]
                    }
                logger.info(f"Загружены настройки для {len(self.settings)} пользователей")
            else:
                logger.info("Файл настроек не найден, создаем новый")
                self.settings = {}
        except Exception as e:
            logger.error(f"Ошибка при загрузке настроек: {e}")
            self.settings = {}
    
    def save_settings(self) -> None:
        """Сохранение настроек в файл"""
        try:
            # Конвертируем множества в списки для JSON
            data = {
                str(user_id): {
                    'channels': list(settings['channels']),
                    'keywords': list(settings['keywords']),
                    'active': settings['active']
                }
                for user_id, settings in self.settings.items()
            }
            with open(self.filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"Сохранены настройки для {len(self.settings)} пользователей")
        except Exception as e:
            logger.error(f"Ошибка при сохранении настроек: {e}")
    
    def get_user_settings(self, user_id: int) -> Dict:
        """Получение настроек пользователя"""
        if user_id not in self.settings:
            self.settings[user_id] = {
                'channels': set(),
                'keywords': set(),
                'active': False
            }
            self.save_settings()
        return self.settings[user_id]
    
    def update_user_settings(self, user_id: int, settings: Dict) -> None:
        """Обновление настроек пользователя"""
        self.settings[user_id] = settings
        self.save_settings()
    
    def get_all_settings(self) -> Dict[int, Dict]:
        """Получение настроек всех пользователей"""
        return self.settings 