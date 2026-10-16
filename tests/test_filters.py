from datetime import datetime
from app.analytics.contracts import MapStat, StatFilter


def test_date_and_map_filter_contract_is_explicit():
    filters = StatFilter(start=datetime(2026, 1, 1), end=datetime(2026, 2, 1), map_name="Mirage")
    assert filters.map_name == "Mirage"
    assert filters.start < filters.end
