# CS2 Analytics Bot

Запускаемый MVP Telegram-бота аналитики CS2. Он не скрейпит HLTV и не генерирует фиктивные статистические данные. По умолчанию включён экспериментальный источник BO3.gg для матчей/команд/карт; PandaScore остаётся поддерживаемым лицензированным вариантом. Все записи хранят идентификатор источника.

## Быстрый запуск

1. Установите Docker Desktop и создайте `.env` из `.env.example`.
2. Заполните как минимум `TELEGRAM_BOT_TOKEN`; `PANDASCORE_TOKEN` нужен только для импорта лицензированных данных.
3. В каталоге проекта выполните:

```bash
docker compose up -d postgres redis
docker compose run --rm bot alembic upgrade head
docker compose up -d bot
```

4. Для разового безопасного импорта: `docker compose run --rm worker`.

Лимит одного запуска задаётся `PANDASCORE_SYNC_MAX_MATCHES` (по умолчанию 100). В работающем боте администратор может запустить такой же импорт командой `/refresh`.

Для BO3.gg задайте `DATA_SOURCE=bo3`; токен не нужен. Для PandaScore задайте `DATA_SOURCE=pandascore` и `PANDASCORE_TOKEN`. BO3-интеграция экспериментальная: endpoint и поля могут измениться без предупреждения. Для тестов локально: `pip install -e '.[dev]'` и `pytest`.

На хостингах без Docker, которые используют buildpack, укажите Build Command: `pip install -r requirements.txt`, а Start Command: `python -m app.main`. Файл `requirements.txt` содержит `greenlet`, необходимый async SQLAlchemy.

## Что работает сейчас

- `/start` и inline-меню;
- поиск игроков, уже загруженных в БД;
- `/player <id>`: отчёт за 12 месяцев по сохранённым картам, K/D, ADR, rating/KAST/impact, форма и стабильность;
- админский `/health` по Telegram ID из конфигурации;
- чистые тестируемые формулы и PostgreSQL миграция;
- авторизованный PandaScore-клиент и идемпотентный импорт завершённых матчей, турниров, карт и игроков;
- статистика игрока по карте импортируется только когда API возвращает явный `game_id`; агрегат матча не выдаётся за карту.

## Известные ограничения

Сравнение команд, графики, кеш Redis, фоновые очереди, экспорт, подписки и round/event функции пока **не реализованы**. Они не представлены как готовые кнопки: меню сообщает об ограничении. См. [DATA_SOURCES.md](DATA_SOURCES.md) и [ARCHITECTURE.md](ARCHITECTURE.md).
