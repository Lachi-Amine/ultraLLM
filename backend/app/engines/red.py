from pathlib import Path

from rank_bm25 import BM25Okapi

from ..schemas import EvidenceRecord, Query
from .common import bounded_score, build_vocabulary, fuzzy_tokenize, load_records, tokenize


TEMPLATES = {
    "define": "{content}",
    "explain": "{content}",
    "analyze": "Interpretive analysis: {content}",
    "compare": "Interpretive comparison: {content}",
    "compute": "Interpretation of the result: {content}",
    "predict": "Interpretive prediction: {content}",
}


class RedEngine:
    def __init__(self, knowledge_path: Path, minimum_score: float = 0.35):
        self.knowledge_path = knowledge_path
        self.minimum_score = minimum_score
        self.records = load_records(knowledge_path)
        self._keywords = [tokenize(str(record["keyword"])) for record in self.records]
        self._vocabulary = build_vocabulary(self._keywords)
        self._corpus = [
            tokenize(f"{record['keyword']} {record['content']}") for record in self.records
        ]
        self._index = BM25Okapi(self._corpus)

    @property
    def record_count(self) -> int:
        return len(self.records)

    def evaluate(self, query: Query, top_n: int = 3) -> EvidenceRecord:
        query_tokens = fuzzy_tokenize(query.text, self._vocabulary)
        if not query_tokens:
            return self._failed("The query does not contain searchable terms.")

        raw_scores = self._index.get_scores(query_tokens)
        ranked = sorted(enumerate(raw_scores), key=lambda item: item[1], reverse=True)
        matches = [
            (index, float(score))
            for index, score in ranked
            if score > 0 and set(query_tokens).intersection(self._keywords[index])
        ]
        intent_matches = [
            match
            for match in matches
            if str(self.records[match[0]]["intent"]).lower() == query.intent.lower()
        ]
        matches = (intent_matches or matches)[:top_n]

        if not matches:
            return self._failed("No matching interpretive data found.")

        best_index, best_raw_score = matches[0]
        score = bounded_score(best_raw_score)
        if score < self.minimum_score:
            return self._failed("No sufficiently relevant interpretive data found.")

        best = self.records[best_index]
        intent = str(best["intent"]).lower()
        content = str(best["content"]).strip()
        output = TEMPLATES.get(intent, "{content}").format(content=content)
        passages = [str(self.records[index]["content"]).strip() for index, _ in matches]
        return EvidenceRecord(
            engine_type="red",
            status="success",
            output=output,
            top_passages=passages,
            trace=[f"BM25 matched {len(matches)} interpretive records."],
            score=score,
            domain=str(best["domain"]),
            intent=intent,
            source=f"{self.knowledge_path.name}:{best_index + 1}",
        )

    def _failed(self, output: str) -> EvidenceRecord:
        return EvidenceRecord(
            engine_type="red",
            status="failed",
            output=output,
            source=self.knowledge_path.name,
        )
