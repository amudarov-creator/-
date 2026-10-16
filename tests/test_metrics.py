from datetime import datetime
import pytest
from app.analytics.contracts import MapStat
from app.analytics.metrics import adr, comparison_delta, form_change, kd, stability_index


def stat(**kwargs):
    return MapStat(player_id=1, map_name="Mirage", played_at=datetime(2026, 1, 1), **kwargs)


def test_kd_uses_totals_not_average_of_ratios():
    result = kd([stat(kills=20, deaths=10), stat(kills=10, deaths=20)])
    assert result.value == pytest.approx(1.0)


def test_adr_uses_total_rounds():
    result = adr([stat(damage=1000, rounds_played=20), stat(damage=450, rounds_played=10)])
    assert result.value == pytest.approx(1450 / 30)


def test_zero_deaths_is_not_infinite_or_fake_value():
    assert kd([stat(kills=20, deaths=0)]).value is None


def test_stability_is_100_for_equal_ratings():
    assert stability_index([stat(rating=1.1), stat(rating=1.1)]).value == pytest.approx(100)


def test_form_change_compares_halves():
    assert form_change([stat(rating=1.0), stat(rating=1.0), stat(rating=1.2), stat(rating=1.2)]).value == pytest.approx(.2)


def test_comparison_keeps_insufficient_sample_warning():
    result = comparison_delta([stat(rating=1.2)], [stat(rating=1.0)])
    assert result.value == pytest.approx(.2)
    assert result.warning
