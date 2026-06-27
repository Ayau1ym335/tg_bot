import json
import sys
from pathlib import Path
import os

class Config:
    CONFIG_PATH = Path(__file__).parent / "config.json"
    REQUIRED_FIELDS = ["api_id", "api_hash", "phone", "channels", "gemini_api_key"]

    @classmethod
    def load(cls) -> dict:
        cfg = {}

        # 1. Проверяем, запущены ли мы на хостинге (ищем переменную API_ID в памяти сервера)
        if "API_ID" in os.environ:
            try:
                cfg["api_id"] = int(os.environ.get("API_ID", 0))
                cfg["api_hash"] = os.environ.get("API_HASH")
                cfg["phone"] = os.environ.get("PHONE")
                cfg["gemini_api_key"] = os.environ.get("GEMINI_API_KEY")
                
                # Списки каналов и ключевых слов в облаке передаются в виде строк через запятую
                channels_raw = os.environ.get("CHANNELS", "")
                cfg["channels"] = [c.strip() for c in channels_raw.split(",") if c.strip()]
                
                keywords_raw = os.environ.get("KEYWORDS", "")
                cfg["keywords"] = [k.strip() for k in keywords_raw.split(",") if k.strip()]
                
                # Опциональные поля
                cfg["destination"] = os.environ.get("DESTINATION", "me")
                cfg["search_history_on_start"] = os.environ.get("SEARCH_HISTORY_ON_START", "False").lower() in ("true", "1")
                cfg["history_limit"] = int(os.environ.get("HISTORY_LIMIT", 100))
            except Exception as e:
                print(f" Ошибка чтения переменных окружения на сервере: {e}")
                sys.exit(1)

        # 2. Если мы на домашнем компьютере, берем всё из config.json, как обычно
        else:
            if not cls.CONFIG_PATH.exists():
                print(f"❌ Файл config.json не найден. Скопируйте config.example.json → config.json и заполните.")
                sys.exit(1)

            with open(cls.CONFIG_PATH, encoding="utf-8") as f:
                cfg = json.load(f)

        # Универсальная валидация для обоих случаев
        for field in cls.REQUIRED_FIELDS:
            if not cfg.get(field):
                print(f"❌ Ошибка: Поле '{field}' не настроено!")
                sys.exit(1)

        if cfg["api_id"] == 0 or cfg["api_id"] == "YOUR_API_ID":
            print("❌ Укажите корректный api_id")
            sys.exit(1)

        if not cfg["channels"]:
            print("❌ Список channels пустой.")
            sys.exit(1)

        # На всякий случай проверяем keywords, если они нужны в коде
        cfg.setdefault("keywords", [])
        cfg.setdefault("destination", "me")
        cfg.setdefault("search_history_on_start", False)
        cfg.setdefault("history_limit", 100)

        return cfg