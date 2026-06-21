import re
from pathlib import Path

import sympy
from rank_bm25 import BM25Okapi

from ..schemas import EvidenceRecord, Query
from .common import bounded_score, build_vocabulary, fuzzy_tokenize, load_records, tokenize


COMPUTE_PATTERN = re.compile(
    r"\b(solve|calculate|compute|differentiate|derivative|diff|integrate|integral|"
    r"factor|expand|simplify|evaluate|eval)\b|=",
    re.IGNORECASE,
)
ALLOWED_FUNCTIONS = {
    "sin": sympy.sin,
    "cos": sympy.cos,
    "tan": sympy.tan,
    "log": sympy.log,
    "exp": sympy.exp,
    "sqrt": sympy.sqrt,
    "pi": sympy.pi,
    "e": sympy.E,
}
WORD_PATTERN = re.compile(r"[A-Za-z_]+")


class ExpressionError(ValueError):
    pass


class GreenEngine:
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
        if query.intent == "compute" or COMPUTE_PATTERN.search(query.text):
            return self._compute(query.text)
        return self._retrieve(query, top_n)

    def _retrieve(self, query: Query, top_n: int) -> EvidenceRecord:
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
            return self._failed("No matching mathematical data found.")

        best_index, raw_score = matches[0]
        score = bounded_score(raw_score)
        if score < self.minimum_score:
            return self._failed("No sufficiently relevant mathematical data found.")

        best = self.records[best_index]
        return EvidenceRecord(
            engine_type="green",
            status="success",
            output=str(best["content"]).strip(),
            top_passages=[str(self.records[index]["content"]).strip() for index, _ in matches],
            trace=[f"BM25 matched {len(matches)} mathematical records."],
            score=score,
            domain=str(best["domain"]),
            intent=str(best["intent"]),
            source=f"{self.knowledge_path.name}:{best_index + 1}",
        )

    def _compute(self, raw: str) -> EvidenceRecord:
        try:
            operation, expression, variable = self._extract_operation(raw)
            if operation == "solve":
                result = self._solve(expression, variable)
                output = f"Solutions for {variable}: {result}"
            else:
                parsed, symbol = self._parse_expression(expression, variable)
                if operation == "differentiate":
                    output = f"Derivative with respect to {symbol}: {sympy.diff(parsed, symbol)}"
                elif operation == "integrate":
                    output = f"Integral with respect to {symbol}: {sympy.integrate(parsed, symbol)} + C"
                elif operation == "factor":
                    output = f"Factored form: {sympy.factor(parsed)}"
                elif operation == "expand":
                    output = f"Expanded form: {sympy.expand(parsed)}"
                elif operation == "simplify":
                    output = f"Simplified expression: {sympy.simplify(parsed)}"
                else:
                    output = f"Numerical evaluation: {parsed.evalf()}"
        except (ExpressionError, TypeError, ValueError, sympy.SympifyError) as exc:
            return self._failed(f"I could not parse that mathematical expression: {exc}")

        return EvidenceRecord(
            engine_type="green",
            status="success",
            output=output,
            trace=[f"Executed symbolic operation: {operation}."],
            score=1.0,
            domain="mathematics",
            intent="compute",
            source="SymPy",
        )

    def _solve(self, expression: str, variable: str) -> list[sympy.Expr]:
        if "=" in expression:
            left_text, right_text = expression.split("=", 1)
            left, symbol = self._parse_expression(left_text, variable)
            right, _ = self._parse_expression(right_text, variable)
            return sympy.solve(sympy.Eq(left, right), symbol)
        parsed, symbol = self._parse_expression(expression, variable)
        return sympy.solve(parsed, symbol)

    def _parse_expression(
        self, expression: str, preferred_variable: str | None = None
    ) -> tuple[sympy.Expr, sympy.Symbol]:
        cleaned = expression.strip().replace("^", "**")
        if not cleaned:
            raise ExpressionError("the expression is empty")
        if not re.fullmatch(r"[A-Za-z0-9_+\-*/().\s]*", cleaned):
            raise ExpressionError("the expression contains unsupported characters")

        names = WORD_PATTERN.findall(cleaned)
        variable_names = sorted(
            {
                name
                for name in names
                if name.lower() not in ALLOWED_FUNCTIONS and len(name) == 1 and name.isalpha()
            }
        )
        unknown_names = [
            name
            for name in names
            if name.lower() not in ALLOWED_FUNCTIONS and name not in variable_names
        ]
        if unknown_names:
            raise ExpressionError(f"unsupported name '{unknown_names[0]}'")

        variable_name = preferred_variable or (variable_names[0] if variable_names else "x")
        symbols = {name: sympy.Symbol(name) for name in set(variable_names + [variable_name])}
        locals_map = {**ALLOWED_FUNCTIONS, **symbols}
        parsed = sympy.sympify(cleaned, locals=locals_map, evaluate=True)
        return parsed, symbols[variable_name]

    def _extract_operation(self, raw: str) -> tuple[str, str, str]:
        raw = re.sub(
            r"^(?:please\s+)?(?:could|can|would|will)\s+you\s+",
            "",
            raw.strip(),
            flags=re.IGNORECASE,
        )
        raw = re.sub(r"^please\s+", "", raw, flags=re.IGNORECASE)
        lowered = raw.lower().strip()
        operation = "evaluate"
        prefixes = {
            "differentiate": "differentiate",
            "derivative": "differentiate",
            "diff": "differentiate",
            "integrate": "integrate",
            "integral": "integrate",
            "factor": "factor",
            "expand": "expand",
            "simplify": "simplify",
            "solve": "solve",
            "calculate": "evaluate",
            "compute": "evaluate",
            "evaluate": "evaluate",
            "eval": "evaluate",
        }
        for prefix, candidate in prefixes.items():
            if lowered.startswith(prefix):
                operation = candidate
                raw = raw[len(prefix) :].strip()
                break
        if "=" in raw and operation == "evaluate":
            operation = "solve"

        variable_match = re.search(
            r"\s+(?:with respect to|w\.r\.t\.?|for|variable)\s+([a-z])\s*$",
            raw,
            re.IGNORECASE,
        )
        variable = variable_match.group(1).lower() if variable_match else "x"
        if variable_match:
            raw = raw[: variable_match.start()].strip()
        return operation, raw, variable

    def _failed(self, output: str) -> EvidenceRecord:
        return EvidenceRecord(
            engine_type="green",
            status="failed",
            output=output,
            source=self.knowledge_path.name,
        )
