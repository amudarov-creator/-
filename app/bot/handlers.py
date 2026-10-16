from datetime import datetime, timedelta, timezone
from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message
from app.analytics.contracts import StatFilter
from app.analytics.service import find_players, player_stats, report
from app.bot.keyboards import main_menu
from app.core.config import get_settings
from app.database.session import SessionLocal
from app.tasks.sync import run as run_sync

router = Router()


class Search(StatesGroup):
    player_name = State()


@router.message(CommandStart())
async def start(message: Message) -> None:
    await message.answer("CS2 Analytics — воспроизводимая статистика из разрешённых источников.", reply_markup=main_menu())


@router.callback_query(F.data == "players")
async def players(callback: CallbackQuery, state: FSMContext) -> None:
    await state.set_state(Search.player_name)
    await callback.message.answer("Введите ник игрока. Я покажу совпадения из загруженных данных.")
    await callback.answer()


@router.message(Search.player_name)
async def lookup_player(message: Message, state: FSMContext) -> None:
    async with SessionLocal() as session:
        found = await find_players(session, message.text or "")
    if not found:
        await message.answer("Игрок не найден. Сначала импортируйте данные лицензированного источника.")
    else:
        await state.update_data(player_id=found[0].id)
        await message.answer("Найдено: " + ", ".join(f"{p.nickname} (id {p.id})" for p in found) + "\nИспользован первый результат. Напишите: 10, 20, 50 или 90d.")
        await state.set_state(None)


@router.message(Command("player"))
async def player_command(message: Message) -> None:
    args = (message.text or "").split(maxsplit=1)
    if len(args) != 2 or not args[1].isdigit():
        await message.answer("Использование: /player <id>. ID выдаётся поиском игрока.")
        return
    async with SessionLocal() as session:
        stats = await player_stats(session, int(args[1]), StatFilter(start=datetime.now(timezone.utc) - timedelta(days=365)))
    if not stats:
        await message.answer("Для игрока пока нет статистики по картам.")
        return
    lines = [f"{x.name}: {x.value:.2f}" if x.value is not None else f"{x.name}: нет данных" for x in report(stats)]
    await message.answer("\n".join([f"Карт: {len(stats)}", *lines, "\nМетрики рассчитаны на стороне бота; рейтинг маркируется как рейтинг источника."]))


@router.callback_query(F.data == "sources")
async def source_limitations(callback: CallbackQuery) -> None:
    await callback.message.answer("HLTV не используется для автоматического сбора: его условия запрещают web scraping. Подключайте лицензированный PandaScore/GRID; раундовые функции зависят от оплаченного плана и полноты фида.")
    await callback.answer()


@router.callback_query(F.data.in_({"teams", "compare", "maps", "matches"}))
async def unavailable(callback: CallbackQuery) -> None:
    await callback.message.answer("Раздел подготовлен в меню, но в этой версии MVP включены только функции, обеспеченные сохранёнными данными: поиск и карточка игрока. Остальные появятся после нормализованного импорта карт и составов.")
    await callback.answer()


def _is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id in get_settings().admins)


@router.message(Command("health"))
async def health(message: Message) -> None:
    if not _is_admin(message): return
    await message.answer("ok")


@router.message(Command("refresh"))
async def refresh(message: Message) -> None:
    if not _is_admin(message):
        return
    await message.answer("Запускаю ограниченное обновление из разрешённого источника.")
    try:
        count = await run_sync()
        await message.answer(f"Обновление завершено. Обработано записей: {count}.")
    except Exception:
        await message.answer("Обновление не завершилось. Подробности сохранены в журнале ingestion_runs.")
