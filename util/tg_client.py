from pathlib import Path

from telethon import TelegramClient


def newTelegramClient(config: dict, session_name: str):
    telegram_config: dict = config["TELEGRAM"]
    session_folder_path = Path(telegram_config.get("session_folder", "./"))

    other_config = {}
    proxy_config = config.get("PROXY")
    if proxy_config is not None:
        other_config["proxy"] = (
            proxy_config["protocol"],
            proxy_config["host"],
            proxy_config["port"],
        )

    return TelegramClient(
        session_folder_path/f"{session_name}.session",
        telegram_config["api_id"],
        telegram_config["api_hash"],
        **other_config
    )