from ingestion.bronze_market_value import parse_market_value


def test_parse_market_value_millions():
    assert parse_market_value("€50M") == 50.0


def test_parse_market_value_thousands():
    assert parse_market_value("€500k") == 0.5


def test_parse_market_value_empty():
    assert parse_market_value("-") == 0.0


def test_parse_market_value_none():
    assert parse_market_value("") == 0.0
