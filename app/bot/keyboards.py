from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def main_menu() -> InlineKeyboardMarkup:
    rows = [
        [("👤 Игроки", "players"), ("👥 Команды", "teams")],
        [("⚖️ Сравнить игроков", "compare"), ("🗺 Карты и стороны", "maps")],
        [("🏆 Матчи и турниры", "matches"), ("ℹ️ Ограничения данных", "sources")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=[[InlineKeyboardButton(text=text, callback_data=data) for text, data in row] for row in rows])
