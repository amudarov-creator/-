from app.data_sources.normalizer import game_scores, map_name, stat_game_id, teams_from_match


def test_match_teams_preserve_provider_ids():
    teams = teams_from_match({"opponents": [{"opponent": {"id": 2, "name": "A", "slug": "a"}}]})
    assert teams[0].source_id == "2"
    assert teams[0].name == "A"


def test_game_score_payload_is_mapped_by_team_id():
    game = {"map": {"name": "Mirage"}, "results": [{"team_id": 2, "score": 13}, {"team_id": 3, "score": 8}]}
    assert map_name(game) == "Mirage"
    assert game_scores(game, {"2", "3"}) == {"2": 13, "3": 8}


def test_match_aggregate_without_game_is_not_map_stat():
    assert stat_game_id({"player": {"id": 1}}) is None
