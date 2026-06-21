import re
from pathlib import Path
from typing import Any

import yaml
from rapidfuzz import fuzz, process


TOKEN_PATTERN = re.compile(r"[a-zA-Z0-9]+")
STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "for",
    "from",
    "hello",
    "hi",
    "how",
    "in",
    "is",
    "it",
    "of",
    "on",
    "or",
    "that",
    "the",
    "there",
    "this",
    "to",
    "what",
    "with",
}


def tokenize(text: str) -> list[str]:
    return [token for token in TOKEN_PATTERN.findall(text.lower()) if token not in STOPWORDS]


def build_vocabulary(keyword_groups: list[list[str]]) -> tuple[str, ...]:
    return tuple(sorted({token for group in keyword_groups for token in group if len(token) >= 3}))


def fuzzy_tokenize(
    text: str,
    vocabulary: tuple[str, ...],
    score_cutoff: float = 78.0,
) -> list[str]:
    corrected: list[str] = []
    for token in tokenize(text):
        if token in vocabulary or len(token) < 4:
            corrected.append(token)
            continue

        match = process.extractOne(
            token,
            vocabulary,
            scorer=fuzz.ratio,
            score_cutoff=score_cutoff,
        )
        if (
            match
            and token[0] == match[0][0]
            and abs(len(token) - len(match[0])) <= 2
        ):
            corrected.append(match[0])
        else:
            corrected.append(token)
    return corrected


def load_records(path: Path) -> list[dict[str, Any]]:
    if not path.exists():
        raise FileNotFoundError(f"Knowledge base not found: {path}")

    with path.open("r", encoding="utf-8") as handle:
        records = yaml.safe_load(handle)

    if not isinstance(records, list):
        raise ValueError(f"Knowledge base must contain a YAML list: {path}")

    required = {"domain", "intent", "epistemic", "keyword", "content"}
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise ValueError(f"Record {index} in {path} is not a mapping")
        missing = required.difference(record)
        if missing:
            raise ValueError(f"Record {index} in {path} is missing: {sorted(missing)}")

    return records


def bounded_score(raw_score: float, scale: float = 3.0) -> float:
    if raw_score <= 0:
        return 0.0
    return min(raw_score / (raw_score + scale), 1.0)
