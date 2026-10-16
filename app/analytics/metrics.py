"""Pure, versioned metric functions. None means insufficient source data, never zero-fill."""
from math import sqrt
from statistics import mean, pstdev
from .contracts import MapStat, MetricResult


def _available(stats: list[MapStat], field: str) -> list[float]:
    return [float(getattr(s, field)) for s in stats if getattr(s, field) is not None]


def sample_warning(maps: int, minimum: int = 20) -> str | None:
    if maps < 5: return "Крайне мало данных: менее 5 карт. Ранжирование недоступно."
    if maps < 10: return "Очень ограниченная выборка: 5–9 карт."
    if maps < minimum: return f"Предварительное наблюдение: меньше порога {minimum} карт."
    return None


def kd(stats: list[MapStat]) -> MetricResult:
    kills, deaths = _available(stats, "kills"), _available(stats, "deaths")
    if not kills or not deaths or sum(deaths) == 0:
        return MetricResult("K/D", None, len(stats), "Недостаточно данных о смертях.", "Σ kills / Σ deaths")
    return MetricResult("K/D", sum(kills) / sum(deaths), len(stats), sample_warning(len(stats)), "Σ kills / Σ deaths")


def adr(stats: list[MapStat]) -> MetricResult:
    valid = [(s.damage, s.rounds_played) for s in stats if s.damage is not None and s.rounds_played]
    rounds = sum(r for _, r in valid)
    value = sum(d for d, _ in valid) / rounds if rounds else None
    return MetricResult("ADR", value, len(valid), sample_warning(len(valid)), "Σ нанесённого урона / Σ сыгранных раундов")


def average(stats: list[MapStat], field: str, label: str) -> MetricResult:
    values = _available(stats, field)
    return MetricResult(label, mean(values) if values else None, len(values), sample_warning(len(values)), f"mean({field}) по картам")


def stability_index(stats: list[MapStat]) -> MetricResult:
    values = _available(stats, "rating")
    if len(values) < 2 or mean(values) == 0:
        return MetricResult("Индекс стабильности", None, len(values), "Нужны минимум две карты с рейтингом.", "max(0, 100 × (1 − σ/mean))")
    value = max(0.0, 100 * (1 - pstdev(values) / mean(values)))
    return MetricResult("Индекс стабильности", value, len(values), sample_warning(len(values)), "max(0, 100 × (1 − σ рейтинга / mean рейтинга))")


def form_change(stats: list[MapStat]) -> MetricResult:
    values = _available(stats, "rating")
    if len(values) < 4:
        return MetricResult("Изменение формы", None, len(values), "Нужны минимум четыре карты.", "mean(вторая половина) − mean(первая половина)")
    half = len(values) // 2
    return MetricResult("Изменение формы", mean(values[half:]) - mean(values[:half]), len(values), sample_warning(len(values)), "mean(вторая половина) − mean(первая половина)")


def comparison_delta(left: list[MapStat], right: list[MapStat], field: str = "rating") -> MetricResult:
    a, b = _available(left, field), _available(right, field)
    if not a or not b:
        return MetricResult(f"Δ {field}", None, min(len(a), len(b)), "Нет сопоставимых значений.", f"mean({field} A) − mean({field} B)")
    n = min(len(a), len(b))
    return MetricResult(f"Δ {field}", mean(a) - mean(b), n, sample_warning(n), f"mean({field} A) − mean({field} B)")
