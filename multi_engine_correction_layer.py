from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Union


# 1. Correction Layer Internal Data Structures

@dataclass
class QueryView:
    text: str
    tokens: List[str] = field(default_factory=list)
    intent: str = "general"
    domain: str = "unknown"


@dataclass
class CorrectedEvidenceRecord:
    engine_type: str
    status: str
    output: str
    corrected_output: str
    top_passages: List[str]
    trace: List[str]
    score: float = 0.0
    raw_score: float = 0.0
    domain: str = "unknown"
    intent: str = "general"
    source: str = "unknown"
    correction_notes: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# 2. Multi-Engine Correction Layer

class CorrectionLayer:
    """
    Correction Layer for the current Green / Yellow / Red engine code.

    This implementation does not require the three engines to share the same
    EvidenceRecord interface. Instead, it reads the fields that currently exist:

      Green:
        engine, content, score, source, domain, intent

      Yellow / Red:
        engine_type, status, output, top_passages, trace, score

    The layer converts them into CorrectedEvidenceRecord objects, normalizes
    score, detects weak evidence, applies engine-specific correction rules, and
    returns a ranked list for the fusion layer.
    """

    def __init__(self, min_score: float = 0.1):
        self.min_score = min_score

    def evaluate(
        self,
        query: Any,
        raw_records: Union[Any, List[Any]],
    ) -> List[CorrectedEvidenceRecord]:
        query_view = self._normalize_query(query)

        if raw_records is None:
            return []

        if not isinstance(raw_records, list):
            raw_records = [raw_records]

        corrected_records = []

        for raw_record in raw_records:
            corrected = self._normalize_record(raw_record)
            corrected.trace.append("Correction Layer received evidence from " + corrected.engine_type + " Engine.")

            self._normalize_score(corrected)
            self._apply_quality_checks(corrected)
            self._apply_engine_specific_rules(query_view, corrected)
            self._apply_intent_rules(query_view, corrected)
            self._polish_output(corrected)
            self._finalize_status(corrected)

            corrected.trace.append("Correction Layer pipeline execution finished.")
            corrected_records.append(corrected)

        corrected_records = self._detect_cross_engine_conflicts(corrected_records)
        corrected_records.sort(key=lambda item: item.score, reverse=True)
        return corrected_records

    # 3. Query and Evidence Adapters

    def _normalize_query(self, query: Any) -> QueryView:
        if isinstance(query, str):
            return QueryView(text=query, tokens=self._simple_tokenize(query))

        text = self._read_field(query, ["text", "raw", "query"], "")
        tokens = self._read_field(query, ["tokens"], [])
        intent = self._read_field(query, ["intent"], "general")
        domain = self._read_field(query, ["domain"], "unknown")

        if not tokens and text:
            tokens = self._simple_tokenize(text)

        return QueryView(
            text=str(text),
            tokens=list(tokens),
            intent=str(intent).lower(),
            domain=str(domain).lower(),
        )

    def _normalize_record(self, record: Any) -> CorrectedEvidenceRecord:
        engine_type = self._read_field(record, ["engine_type", "engine", "epistemic"], "unknown")
        engine_type = str(engine_type).strip()
        engine_type = engine_type[:1].upper() + engine_type[1:].lower() if engine_type else "Unknown"

        status = self._read_field(record, ["status"], "success")
        output = self._read_field(record, ["output", "content"], "")
        score = float(self._read_field(record, ["score"], 0.0) or 0.0)
        top_passages = self._read_field(record, ["top_passages"], [])
        trace = self._read_field(record, ["trace"], [])
        domain = self._read_field(record, ["domain"], "unknown")
        intent = self._read_field(record, ["intent"], "general")
        source = self._read_field(record, ["source"], engine_type + " Engine")

        if isinstance(top_passages, str):
            top_passages = [top_passages]
        if not isinstance(top_passages, list):
            top_passages = []

        if isinstance(trace, str):
            trace = [trace]
        if not isinstance(trace, list):
            trace = []

        return CorrectedEvidenceRecord(
            engine_type=engine_type,
            status=str(status).lower(),
            output=str(output),
            corrected_output=str(output),
            top_passages=top_passages,
            trace=trace,
            score=score,
            raw_score=score,
            domain=str(domain).lower(),
            intent=str(intent).lower(),
            source=str(source),
        )

    def _read_field(self, obj: Any, names: List[str], default: Any) -> Any:
        if isinstance(obj, dict):
            for name in names:
                if name in obj:
                    return obj[name]
            return default

        for name in names:
            if hasattr(obj, name):
                return getattr(obj, name)

        return default

    def _simple_tokenize(self, text: str) -> List[str]:
        cleaned = ""
        for ch in text.lower():
            cleaned += ch if ch.isalnum() else " "
        return [item for item in cleaned.split() if item]

    # 4. Correction Rules

    def _normalize_score(self, record: CorrectedEvidenceRecord):
        engine = record.engine_type.lower()
        raw_score = record.score

        if raw_score <= 0:
            record.score = 0.0
            record.correction_notes.append("Normalized non-positive raw score to 0.0.")
            return

        if engine == "red" and raw_score > 1:
            record.score = min(raw_score / 10.0, 1.0)
            record.correction_notes.append("Normalized Red matching score from 0-10 scale to 0-1 scale.")
            return

        if engine == "yellow" and raw_score > 1:
            record.score = raw_score / (raw_score + 1.0)
            record.correction_notes.append("Normalized Yellow BM25 score with score / (score + 1).")
            return

        record.score = min(raw_score, 1.0)
        record.correction_notes.append("Normalized score to bounded 0-1 range.")

    def _apply_quality_checks(self, record: CorrectedEvidenceRecord):
        text = record.output.lower().strip()

        if record.status not in ["success", "fallback"]:
            record.score *= 0.2
            record.warnings.append("engine_status_failed")
            record.correction_notes.append("Reduced score because source engine did not return success.")

        if not text:
            record.status = "failed"
            record.score = 0.0
            record.corrected_output = "No reliable evidence was produced by the source engine."
            record.warnings.append("empty_output")
            record.correction_notes.append("Marked evidence as failed because output is empty.")
            return

        weak_phrases = [
            "no matching empirical data found",
            "database is empty",
            "exception happened",
            "cannot open file",
            "error solving equation",
            "error simplifying expression",
            "error performing differentiation",
            "error performing integration",
            "error factoring expression",
            "error expanding expression",
            "error evaluating expression",
            "does not trigger specific",
            "general responsibility paradigm",
        ]

        for phrase in weak_phrases:
            if phrase in text:
                record.score *= 0.25
                record.warnings.append("weak_or_fallback_evidence")
                record.correction_notes.append("Reduced score because weak or fallback evidence was detected.")
                break

        if len(record.top_passages) == 0 and record.engine_type.lower() in ["yellow", "red"]:
            record.score *= 0.85
            record.warnings.append("no_top_passages")
            record.correction_notes.append("Reduced score slightly because no supporting passages were provided.")

    def _apply_engine_specific_rules(self, query: QueryView, record: CorrectedEvidenceRecord):
        engine = record.engine_type.lower()
        query_text = query.text.lower()
        query_intent = query.intent.lower()

        compute_keywords = [
            "solve", "calculate", "compute", "differentiate", "derivative",
            "integrate", "integral", "factor", "expand", "simplify", "=",
        ]
        analytical_keywords = ["why", "analyze", "compare", "policy", "society", "culture", "ethics"]

        is_compute_query = query_intent in ["compute", "calculate", "solve"] or any(
            word in query_text for word in compute_keywords
        )
        is_analytical_query = query_intent in ["analyze", "compare", "explain"] or any(
            word in query_text for word in analytical_keywords
        )

        if engine == "green":
            if is_compute_query:
                record.score *= 1.2
                record.correction_notes.append("Boosted Green evidence for computational query.")
            elif record.domain == "mathematics":
                record.score *= 1.05
                record.correction_notes.append("Slightly boosted Green mathematical evidence.")
            else:
                record.score *= 0.9
                record.warnings.append("green_non_compute_context")

        elif engine == "yellow":
            if is_compute_query:
                record.score *= 0.75
                record.warnings.append("yellow_compute_mismatch")
                record.correction_notes.append("Reduced Yellow evidence for computational query.")
            else:
                record.score *= 1.1
                record.correction_notes.append("Boosted Yellow evidence for empirical or definitional query.")

        elif engine == "red":
            if is_compute_query:
                record.score *= 0.5
                record.warnings.append("red_compute_mismatch")
                record.correction_notes.append("Reduced Red evidence for computational query.")
            elif is_analytical_query:
                record.score *= 1.15
                record.correction_notes.append("Boosted Red evidence for interpretive or analytical query.")

        record.score = max(0.0, min(record.score, 1.0))

    def _apply_intent_rules(self, query: QueryView, record: CorrectedEvidenceRecord):
        query_intent = query.intent.lower()
        record_intent = record.intent.lower()

        if query_intent == "general" or record_intent == "general":
            return

        if query_intent == record_intent:
            record.score *= 1.1
            record.correction_notes.append("Boosted score because query intent matches evidence intent.")
        else:
            record.score *= 0.9
            record.warnings.append("intent_mismatch")
            record.correction_notes.append("Reduced score because query intent differs from evidence intent.")

        record.score = max(0.0, min(record.score, 1.0))

    def _polish_output(self, record: CorrectedEvidenceRecord):
        text = record.corrected_output.strip()

        while "  " in text:
            text = text.replace("  ", " ")

        if text and text[-1] not in [".", "!", "?"]:
            text = text + "."

        if text:
            text = text[0].upper() + text[1:]

        record.corrected_output = text
        record.correction_notes.append("Polished output formatting for downstream fusion.")

    def _finalize_status(self, record: CorrectedEvidenceRecord):
        if record.score < self.min_score:
            record.status = "failed"
            record.warnings.append("below_minimum_score")
            record.correction_notes.append("Marked evidence as failed because corrected score is below threshold.")
        elif "weak_or_fallback_evidence" in record.warnings:
            record.status = "fallback"
        else:
            record.status = "success"

    def _detect_cross_engine_conflicts(
        self,
        records: List[CorrectedEvidenceRecord],
    ) -> List[CorrectedEvidenceRecord]:
        successful_records = [item for item in records if item.status == "success"]
        high_confidence = [item for item in successful_records if item.score >= 0.7]

        domains = set(item.domain for item in high_confidence if item.domain != "unknown")
        engines = set(item.engine_type.lower() for item in high_confidence)

        if len(high_confidence) >= 2 and len(domains) >= 2:
            for item in records:
                item.warnings.append("cross_domain_high_confidence")
                item.correction_notes.append(
                    "Detected high-confidence evidence from multiple domains; fusion layer should handle carefully."
                )

        if "green" in engines and "red" in engines:
            for item in records:
                item.warnings.append("green_red_cross_engine_mix")
                item.correction_notes.append(
                    "Detected both symbolic and interpretive evidence; fusion layer should preserve their roles."
                )

        return records


# 5. Local Test Bench

if __name__ == "__main__":
    class GreenLikeRecord:
        engine = "green"
        content = "Solutions for x: [-2, 2]"
        score = 1.0
        source = "SymPy Equation Solver"
        domain = "mathematics"
        intent = "compute"

    class YellowLikeRecord:
        engine_type = "Yellow"
        status = "success"
        output = "Velocity is the speed of an object in a particular direction, a vector quantity"
        top_passages = ["Velocity is the speed of an object in a particular direction, a vector quantity."]
        trace = ["Yellow Engine retrieval finished."]
        score = 2.4

    class RedLikeRecord:
        engine_type = "Red"
        status = "success"
        output = (
            "[Interpretive Framework: General Social Responsibility Paradigm]\n"
            "The current query does not trigger specific policy or conceptual keywords."
        )
        top_passages = []
        trace = ["No specific interpretive rules matched."]
        score = 1.0

    query = QueryView(
        text="solve x^2 = 4",
        tokens=["solve", "x", "2", "4"],
        intent="compute",
        domain="mathematics",
    )

    layer = CorrectionLayer()
    results = layer.evaluate(query, [GreenLikeRecord(), YellowLikeRecord(), RedLikeRecord()])

    print("================ MULTI-ENGINE CORRECTION REPORT ================")
    for item in results:
        print("\nEngine Type: " + item.engine_type)
        print("Status: " + item.status)
        print("Raw Score: " + str(round(item.raw_score, 4)))
        print("Corrected Score: " + str(round(item.score, 4)))
        print("Corrected Output: " + item.corrected_output)
        print("Warnings: " + str(item.warnings))
        print("Correction Notes:")
        for note in item.correction_notes:
            print("  -> " + note)
    print("===============================================================")
