import asyncio
import re

from ..engines import GreenEngine, RedEngine, YellowEngine
from ..schemas import (
    ChatMessage,
    ChatResponse,
    EvidenceRecord,
    Query,
    SourceRecord,
)
from .conversations import ConversationStore
from .ollama import OllamaClient, PUBLIC_IDENTITY


GREETING_PATTERN = re.compile(r"^(hi|hello|hey|good morning|good afternoon|good evening)[!. ]*$", re.I)
THANKS_PATTERN = re.compile(r"^(thanks|thank you|thx)[!. ]*$", re.I)
HOW_ARE_YOU_PATTERN = re.compile(
    r"^(how are you|how(?:'|’)s it going|how do you feel|are you okay)[?!. ]*$",
    re.I,
)
IDENTITY_PATTERN = re.compile(
    r"\b("
    r"who are you|what are you|tell me about yourself|"
    r"what(?:'s| is) your name|"
    r"who (?:made|built|created|developed|trained) you|"
    r"who is your (?:creator|developer|maker)|"
    r"what (?:team|company|organization) (?:made|built|created|developed) you|"
    r"what model are you|what model do you use|"
    r"what llm are you|"
    r"what(?:'s| is) your (?:model|underlying model|base model)|"
    r"which (?:model|llm) (?:are you|do you use|powers you)|"
    r"(?:is your model|do you use) (?:qwen|chatgpt|gpt|claude|gemini)|"
    r"are you (?:qwen|chatgpt|gpt|claude|gemini)|"
    r"(?:you are|you're) (?:qwen|chatgpt|gpt|claude|gemini)|"
    r"are you (?:based on|powered by|built on) [a-z0-9 ._-]+"
    r")\b",
    re.I,
)
CAPABILITIES_PATTERN = re.compile(
    r"^(what can you do|how can you help|help)[?!. ]*$",
    re.I,
)
FOLLOW_UP_PATTERN = re.compile(
    r"\b(that|it|this|those|them|previous|earlier|more|further)\b", re.I
)
MATH_TOPIC_PATTERN = re.compile(
    r"\b(algebra|calculus|derivative|equation|function|geometry|integral|limit|"
    r"matrix|polynomial|prime|sequence|series|theorem|trigonometry)\b",
    re.I,
)
SOCIAL_TOPIC_PATTERN = re.compile(
    r"\b(authority|citizenship|culture|democracy|education|equality|equity|ethics|"
    r"freedom|gender|government|identity|justice|law|policy|power|religion|rights|"
    r"society|sociology|state|values)\b",
    re.I,
)


class ChatOrchestrator:
    def __init__(
        self,
        green: GreenEngine,
        yellow: YellowEngine,
        red: RedEngine,
        llm: OllamaClient | None = None,
        conversations: ConversationStore | None = None,
    ) -> None:
        self.green = green
        self.yellow = yellow
        self.red = red
        self.llm = llm
        self.conversations = conversations or ConversationStore()

    @property
    def engine_counts(self) -> dict[str, int]:
        return {
            "green": self.green.record_count,
            "yellow": self.yellow.record_count,
            "red": self.red.record_count,
        }

    async def chat(self, message: str, conversation_id=None) -> ChatResponse:
        conversation = self.conversations.get_or_create(conversation_id)
        user_message = ChatMessage(role="user", content=message.strip())
        conversation.messages.append(user_message)

        direct = self._direct_reply(message)
        if direct:
            assistant = ChatMessage(role="assistant", content=direct)
            conversation.messages.append(assistant)
            return ChatResponse(conversation_id=conversation.id, message=assistant)

        query_text = self._contextualize(message, conversation.messages[:-1])
        query = Query(text=query_text, intent=self._detect_intent(message))
        records = await self._run_engines(query)
        successful = sorted(
            (record for record in records if record.status == "success"),
            key=lambda record: record.score,
            reverse=True,
        )

        if query.intent == "compute" and not successful:
            answer = records[0].output
            warnings = ["invalid_expression"]
        elif query.intent == "compute":
            answer, warnings = self._synthesize(message, successful)
        elif successful:
            answer, warnings = self._synthesize(message, successful)
        else:
            deterministic_answer, warnings = self._synthesize(message, successful)
            llm_answer = await self._ask_llm(
                message,
                conversation.messages[:-1],
                [],
            )
            if llm_answer:
                answer = llm_answer
                warnings = ["local_model_answer"] if not successful else []
            else:
                answer = deterministic_answer
        assistant = ChatMessage(role="assistant", content=answer)
        conversation.messages.append(assistant)
        sources = [
            SourceRecord(
                engine=record.engine_type,
                domain=record.domain,
                intent=record.intent,
                score=record.score,
                content=record.output,
                source=record.source,
            )
            for record in successful[:3]
        ]
        return ChatResponse(
            conversation_id=conversation.id,
            message=assistant,
            sources=sources,
            warnings=warnings,
        )

    async def _ask_llm(
        self,
        question: str,
        history: list[ChatMessage],
        evidence: list[EvidenceRecord],
    ) -> str | None:
        if self.llm is None:
            return None
        return await self.llm.answer(question, history, evidence)

    async def _run_engines(self, query: Query) -> list[EvidenceRecord]:
        if query.intent == "compute":
            return [await asyncio.to_thread(self.green.evaluate, query)]

        if query.intent != "compare" and MATH_TOPIC_PATTERN.search(query.text):
            return [await asyncio.to_thread(self.green.evaluate, query)]

        if query.intent != "compare" and SOCIAL_TOPIC_PATTERN.search(query.text):
            return [await asyncio.to_thread(self.red.evaluate, query)]

        tasks = [
            asyncio.to_thread(self.yellow.evaluate, query),
        ]
        if query.intent == "compare":
            tasks.append(asyncio.to_thread(self.red.evaluate, query))
            tasks.append(asyncio.to_thread(self.green.evaluate, query))
        results = await asyncio.gather(*tasks)
        return list(results)

    def _synthesize(
        self, original_message: str, records: list[EvidenceRecord]
    ) -> tuple[str, list[str]]:
        if not records:
            return (
                "I could not find a reliable answer in the local knowledge base. "
                "Try rephrasing the question or ask about mathematics, science, or social concepts.",
                ["no_reliable_evidence"],
            )

        best = records[0]
        if best.intent == "compute" or len(records) == 1:
            return best.output, []

        is_comparison = "compare" in original_message.lower() or "difference" in original_message.lower()
        distinct = []
        seen = set()
        for record in records:
            normalized = record.output.strip().lower()
            if normalized not in seen:
                seen.add(normalized)
                distinct.append(record)

        if is_comparison and len(distinct) > 1:
            parts = [f"{record.domain.title()}: {record.output}" for record in distinct[:2]]
            return "\n\n".join(parts), []

        answer = best.output
        supporting = next(
            (
                record
                for record in distinct[1:]
                if record.domain != best.domain and record.score >= 0.45
            ),
            None,
        )
        if supporting:
            answer = f"{answer}\n\nRelated perspective: {supporting.output}"
        return answer, []

    def _contextualize(self, message: str, history: list[ChatMessage]) -> str:
        if not history or not FOLLOW_UP_PATTERN.search(message):
            return message
        previous_user = next(
            (item.content for item in reversed(history) if item.role == "user"),
            "",
        )
        return f"{previous_user} {message}".strip()

    def _detect_intent(self, message: str) -> str:
        lowered = message.lower()
        if re.search(
            r"\b(solve|calculate|compute|differentiate|derivative|integrate|integral|"
            r"factor|expand|simplify|evaluate)\b|=",
            lowered,
        ):
            return "compute"
        if re.fullmatch(r"[0-9a-z_+\-*/^().\s]+", lowered) and (
            re.search(r"[+\-*/^]", lowered)
            or re.search(r"\b(sin|cos|tan|log|exp|sqrt|pi)\b", lowered)
        ):
            return "compute"
        if "compare" in lowered or "difference between" in lowered or " vs " in lowered:
            return "compare"
        if "why" in lowered or "analyze" in lowered:
            return "analyze"
        if "explain" in lowered or "how" in lowered:
            return "explain"
        return "define"

    def _direct_reply(self, message: str) -> str | None:
        stripped = message.strip()
        if GREETING_PATTERN.fullmatch(stripped):
            return (
                "Hello! Ask me about mathematics, science, social concepts, "
                "or give me a symbolic calculation to solve."
            )
        if THANKS_PATTERN.fullmatch(stripped):
            return "You’re welcome. What would you like to explore next?"
        if HOW_ARE_YOU_PATTERN.fullmatch(stripped):
            return "I’m doing well and ready to help. What would you like to ask?"
        if IDENTITY_PATTERN.search(stripped):
            return PUBLIC_IDENTITY
        if CAPABILITIES_PATTERN.fullmatch(stripped):
            return (
                "I can answer questions from the local knowledge base, explain "
                "mathematics and science concepts, discuss social concepts, and "
                "solve symbolic calculations."
            )
        return None
