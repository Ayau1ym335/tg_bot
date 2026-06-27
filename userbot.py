import asyncio
import logging
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest
from google import genai
from config import Config

# Логирование
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.FileHandler("userbot.log", encoding="utf-8"),
        logging.StreamHandler()
    ]
)
log = logging.getLogger(__name__)

cfg = Config.load()

# Инициализация Telegram
client = TelegramClient(
    "userbot_session",
    cfg["api_id"],
    cfg["api_hash"]
)

# Инициализация Gemini ИИ
ai_client = genai.Client(api_key=cfg["gemini_api_key"])

async def check_post_with_ai(text: str) -> str | None:
    """Отправляет текст поста в ИИ и возвращает вердикт."""
    if not text or len(text) < 30: # Пропускаем совсем короткие посты без смысла
        return None
        
    prompt = f"""Ты — умный фильтр для Telegram-канала.
Твоя задача — найти стартап-мероприятия, хакатоны, гранты, конкурсы или олимпиады, оплачиваемые программы заграницей, летние школы, научные проекты и исследования, которые подходят для школьника (15 лет). 
Приоритет: онлайн-форматы, мероприятия в Казахстане, а также проекты в сфере IT, робототехники, C++ и медицины.

Текст поста:
{text}

Ответь СТРОГО в таком формате:
Если подходит: "ДА | [Кратко в 1 предложение: что это, дедлайн, призы]"
Если не подходит (спам, новости, курсы для взрослых, нет призов): "НЕТ"
"""
    try:
        # Используем асинхронный вызов (.aio), чтобы не блокировать Telegram-бота
        response = await ai_client.aio.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt
        )
        result = response.text.strip()
        
        if result.upper().startswith("ДА"):
            return result[4:].strip() # Возвращаем только саму выжимку без слова "ДА | "
        return None
        
    except Exception as e:
        log.error(f"Ошибка при запросе к Gemini API: {e}")
        return None


async def notify(event, ai_summary: str, channel_title: str):
    """Пересылает пост + подпись с выводами ИИ."""
    dest = cfg["destination"]

    # Форвардим пост
    await client.forward_messages(dest, event.message)

    # Добавляем информационную подпись от ИИ
    caption = (
        f"📌 Канал: **{channel_title}**\n"
        f"🤖 **ИИ:** {ai_summary}\n"
        f"🕐 {datetime.now().strftime('%d.%m.%Y %H:%M')}"
    )
    await client.send_message(dest, caption)
    log.info(f"[{channel_title}] Найдено подходящее: {ai_summary[:50]}...")


@client.on(events.NewMessage(chats=cfg["channels"]))
async def on_new_post(event):
    """Обработчик новых сообщений."""
    try:
        text = event.message.message or ""
        ai_summary = await check_post_with_ai(text)
        
        if ai_summary:
            channel = await event.get_chat()
            channel_title = getattr(channel, "title", str(channel.id))
            await notify(event, ai_summary, channel_title)
            
    except Exception as e:
        log.error(f"Ошибка при обработке сообщения: {e}")


async def search_history():
    """Поиск по истории при старте (если включено в config)."""
    if not cfg.get("search_history_on_start"):
        return

    limit = cfg.get("history_limit", 100)
    log.info(f"Поиск по истории (последние {limit} постов на канал)...")
    dest = cfg["destination"]

    for channel_name in cfg["channels"]:
        try:
            channel = await client.get_entity(channel_name)
            history = await client(GetHistoryRequest(
                peer=channel,
                limit=limit,
                offset_date=None,
                offset_id=0,
                max_id=0,
                min_id=0,
                add_offset=0,
                hash=0
            ))

            found = 0
            for msg in reversed(history.messages):
                text = getattr(msg, "message", "") or ""
                ai_summary = await check_post_with_ai(text)
                
                if ai_summary:
                    await client.forward_messages(dest, msg)
                    await client.send_message(
                        dest,
                        f"📌 История | **{channel.title}**\n🤖 {ai_summary}"
                    )
                    found += 1
                
                await asyncio.sleep(1) # Обязательная пауза, чтобы не упереться в лимиты API

            log.info(f"[{channel.title}] Найдено в истории с помощью ИИ: {found}")
        except Exception as e:
            log.error(f"Ошибка при поиске истории в {channel_name}: {e}")


async def main():
    log.info("Запуск AI-userbot...")
    await client.start(phone=cfg["phone"])

    me = await client.get_me()
    log.info(f"Авторизован как: {me.first_name} (@{me.username})")

    await search_history()

    log.info(f"Мониторинг {len(cfg['channels'])} каналов через Gemini AI...")
    log.info("Ожидание новых постов...")

    await client.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())