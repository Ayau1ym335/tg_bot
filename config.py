"""
Загрузчик конфигурации из config.json с валидацией.
"""

import json
import sys
from pathlib import Path


class Config:
    CONFIG_PATH = Path(__file__).parent / "config.json"

    REQUIRED_FIELDS = ["api_id", "api_hash", "phone", "channels", "gemini_api_key"]

    @classmethod
    def load(cls) -> dict:
        if not cls.CONFIG_PATH.exists():
            print(f"❌ Файл config.json не найден. Скопируйте config.example.json → config.json и заполните.")
            sys.exit(1)

        with open(cls.CONFIG_PATH, encoding="utf-8") as f:
            cfg = json.load(f)

        # Валидация
        for field in cls.REQUIRED_FIELDS:
            if not cfg.get(field):
                print(f"❌ Поле '{field}' не заполнено в config.json")
                sys.exit(1)

        if cfg["api_id"] == 0 or cfg["api_id"] == "YOUR_API_ID":
            print("❌ Укажите api_id из my.telegram.org")
            sys.exit(1)

        if not cfg["channels"]:
            print("❌ Список channels пустой — добавьте каналы.")
            sys.exit(1)

        if not cfg["keywords"]:
            print("❌ Список keywords пустой — добавьте ключевые слова.")
            sys.exit(1)

        # Дефолты для опциональных полей
        cfg.setdefault("destination", "me")
        cfg.setdefault("search_history_on_start", False)
        cfg.setdefault("history_limit", 100)

        return cfg
