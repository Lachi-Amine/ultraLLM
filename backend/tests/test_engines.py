from app.config import GREEN_DATA_PATH, RED_DATA_PATH, YELLOW_DATA_PATH
from app.engines import GreenEngine, RedEngine, YellowEngine
from app.schemas import Query


def test_yellow_normalizes_punctuation() -> None:
    engine = YellowEngine(YELLOW_DATA_PATH)
    plain = engine.evaluate(Query(text="velocity"))
    punctuated = engine.evaluate(Query(text="velocity?"))

    assert plain.status == "success"
    assert punctuated.status == "success"


def test_yellow_fuzzy_matches_temperature_misspellings() -> None:
    engine = YellowEngine(YELLOW_DATA_PATH)

    for question in ("what is tempreture?", "what is tempurature"):
        result = engine.evaluate(Query(text=question, intent="define"))
        assert result.status == "success"
        assert "temperature" in result.output.lower()


def test_green_does_not_return_irrelevant_first_record() -> None:
    engine = GreenEngine(GREEN_DATA_PATH)
    result = engine.evaluate(Query(text="hello there"))

    assert result.status == "failed"


def test_red_normalizes_query_text() -> None:
    engine = RedEngine(RED_DATA_PATH)

    assert engine.evaluate(Query(text="Culture")).status == "success"
    assert engine.evaluate(Query(text="culture?")).status == "success"
