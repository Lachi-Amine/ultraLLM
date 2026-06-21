import asyncio

from app.config import GREEN_DATA_PATH, RED_DATA_PATH, YELLOW_DATA_PATH
from app.engines import GreenEngine, RedEngine, YellowEngine
from app.services.ollama import PUBLIC_IDENTITY
from app.services.orchestrator import ChatOrchestrator


class FakeLlm:
    def __init__(self, response: str):
        self.response = response
        self.calls = 0

    async def answer(self, question, history, evidence):
        self.calls += 1
        return self.response


def build_orchestrator(llm) -> ChatOrchestrator:
    return ChatOrchestrator(
        green=GreenEngine(GREEN_DATA_PATH),
        yellow=YellowEngine(YELLOW_DATA_PATH),
        red=RedEngine(RED_DATA_PATH),
        llm=llm,
    )


def test_general_no_match_uses_local_model() -> None:
    llm = FakeLlm("Mathematics is the study of quantities, patterns, and structures.")
    orchestrator = build_orchestrator(llm)

    result = asyncio.run(orchestrator.chat("What is math?"))

    assert result.message.content.startswith("Mathematics is")
    assert result.warnings == ["local_model_answer"]
    assert llm.calls == 1


def test_calculations_never_pass_through_language_model() -> None:
    llm = FakeLlm("Incorrect rewritten answer")
    orchestrator = build_orchestrator(llm)

    result = asyncio.run(orchestrator.chat("could you calculate 4+4"))

    assert "8.00000000000000" in result.message.content
    assert llm.calls == 0


def test_known_retrieval_answer_does_not_use_language_model() -> None:
    llm = FakeLlm("Unnecessary rewritten answer")
    orchestrator = build_orchestrator(llm)

    result = asyncio.run(orchestrator.chat("What is temperature?"))

    assert "average kinetic energy" in result.message.content.lower()
    assert llm.calls == 0


def test_identity_questions_always_use_ultrallm_apma_identity() -> None:
    llm = FakeLlm("I am Qwen.")
    orchestrator = build_orchestrator(llm)

    questions = [
        "Who are you?",
        "Who created you?",
        "What model are you?",
        "Are you Qwen?",
        "Are you based on Qwen?",
        "You are Qwen.",
        "Do you use Qwen?",
    ]

    for question in questions:
        result = asyncio.run(orchestrator.chat(question))
        assert result.message.content == PUBLIC_IDENTITY

    assert llm.calls == 0
