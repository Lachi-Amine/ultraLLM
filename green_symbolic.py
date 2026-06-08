from __future__ import annotations

import re
import os
import sys
import yaml
import sympy
from typing import Optional, List
from dataclasses import dataclass, field
from rank_bm25 import BM25Okapi

# Allows direct script execution to import schemas
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Shared Schemas Alignment (Aligned with Red & Yellow Engines)
try:
    from pipeline.schemas import Query, EvidenceRecord
except ImportError:
    @dataclass
    class Query:
        text: str  # The original search sentence from the user
        tokens: List[str] = field(default_factory=list)  # Words split from the sentence


    @dataclass
    class EvidenceRecord:
        engine_type: str  # Always "Green" for this engine
        status: str  # "success" or "failed"
        output: str  # The best matching answer found
        top_passages: List[str]  # A list of top matching answers
        trace: List[str]  # Step-by-step logs for debugging (:debug command)
        score: float = 0.0  # Search or computation confidence score


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-zA-Z0-9]+", text.lower())


# ─────────────────────────────────────────────
# Symbolic Computation Module
# ─────────────────────────────────────────────
class SymbolicSolver:
    """
    Wraps SymPy to provide:
      • solve_equation(expr_str, var)  — Solves equations (supports expression=0 or explicit '=')
      • simplify_expr(expr_str)        — Simplifies mathematical expressions
      • differentiate(expr_str, var)   — Symbolically differentiates an expression
      • integrate_expr(expr_str, var)  — Symbolically integrates an expression
      • factor_expr(expr_str)          — Factors expressions
      • expand_expr(expr_str)          — Expands expressions
      • evaluate_expr(expr_str)        — Evaluates numerical values (e.g., sqrt(2), pi)
    """

    def __init__(self):
        self.vars = {}

    def _get_var(self, name: str) -> sympy.Symbol:
        if name not in self.vars:
            self.vars[name] = sympy.symbols(name)
        return self.vars[name]

    def _parse_expr(self, expr_str: str) -> tuple[any, sympy.Symbol]:
        """Parses string into SymPy expression, extracts or defaults a variable."""
        cleaned = expr_str.replace("^", "**")
        # Extract possible variables (letters a-z, excluding common math functions)
        tokens = re.findall(r"\b[a-z]\b", cleaned.lower())
        ignore = {"e", "i", "d"}
        valid_vars = [t for t in tokens if t not in ignore]
        var_name = valid_vars[0] if valid_vars else "x"
        var = self._get_var(var_name)

        try:
            expr = sympy.sympify(cleaned, locals={var_name: var})
            return expr, var
        except Exception:
            # Fallback parsing if sympify fails directly
            return sympy.sympify("0"), var

    def solve_equation(self, expr_str: str, var_str: Optional[str] = None) -> EvidenceRecord:
        try:
            if "=" in expr_str:
                lhs_str, rhs_str = expr_str.split("=", 1)
                lhs, var_l = self._parse_expr(lhs_str)
                rhs, _ = self._parse_expr(rhs_str)
                eq = sympy.Eq(lhs, rhs)
                var = self._get_var(var_str) if var_str else var_l
                sol = sympy.solve(eq, var)
            else:
                expr, var_e = self._parse_expr(expr_str)
                var = self._get_var(var_str) if var_str else var_e
                sol = sympy.solve(expr, var)

            return EvidenceRecord(
                engine_type="Green",
                status="success",
                output=f"Solutions for {var}: {sol}",
                top_passages=[],
                trace=["Executed solve_equation via SymPy Solver"],
                score=1.0
            )
        except Exception as e:
            return EvidenceRecord(
                engine_type="Green",
                status="failed",
                output=f"Error solving equation: {str(e)}",
                top_passages=[],
                trace=[f"Error occurred in solve_equation: {str(e)}"],
                score=0.0
            )

    def simplify_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            expr, _ = self._parse_expr(expr_str)
            res = sympy.simplify(expr)
            return EvidenceRecord(
                engine_type="Green",
                status="success",
                output=f"Simplified expression: {res}",
                top_passages=[],
                trace=["Executed simplify_expr via SymPy Solver"],
                score=1.0
            )
        except Exception as e:
            return EvidenceRecord(
                engine_type="Green",
                status="failed",
                output=f"Error simplifying expression: {str(e)}",
                top_passages=[],
                trace=[f"Error occurred in simplify_expr: {str(e)}"],
                score=0.0
            )

    def differentiate(self, expr_str: str, var_str: Optional[str] = None) -> EvidenceRecord:
        try:
            expr, var_e = self._parse_expr(expr_str)
            var = self._get_var(var_str) if var_str else var_e
            res = sympy.diff(expr, var)
            return EvidenceRecord(
                engine_type="Green",
                status="success",
                output=f"Derivative w.r.t {var}: {res}",
                top_passages=[],
                trace=["Executed differentiate via SymPy Solver"],
                score=1.0
            )
        except Exception as e:
            return EvidenceRecord(
                engine_type="Green",
                status="failed",
                output=f"Error performing differentiation: {str(e)}",
                top_passages=[],
                trace=[f"Error occurred in differentiate: {str(e)}"],
                score=0.0
            )

    def integrate_expr(self, expr_str: str, var_str: Optional[str] = None) -> EvidenceRecord:
        try:
            expr, var_e = self._parse_expr(expr_str)
            var = self._get_var(var_str) if var_str else var_e
            res = sympy.integrate(expr, var)
            return EvidenceRecord(
                engine_type="Green",
                status="success",
                output=f"Integral w.r.t {var}: {res} + C",
                top_passages=[],
                trace=["Executed integrate_expr via SymPy Solver"],
                score=1.0
            )
        except Exception as e:
            return EvidenceRecord(
                engine_type="Green",
                status="failed",
                output=f"Error performing integration: {str(e)}",
                top_passages=[],
                trace=[f"Error occurred in integrate_expr: {str(e)}"],
                score=0.0
            )

    def factor_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            expr, _ = self._parse_expr(expr_str)
            res = sympy.factor(expr)
            return EvidenceRecord(
                engine_type="Green",
                status="success",
                output=f"Factored form: {res}",
                top_passages=[],
                trace=["Executed factor_expr via SymPy Solver"],
                score=1.0
            )
        except Exception as e:
            return EvidenceRecord(
                engine_type="Green",
                status="failed",
                output=f"Error factoring expression: {str(e)}",
                top_passages=[],
                trace=[f"Error occurred in factor_expr: {str(e)}"],
                score=0.0
            )

    def expand_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            expr, _ = self._parse_expr(expr_str)
            res = sympy.expand(expr)
            return EvidenceRecord(
                engine_type="Green",
                status="success",
                output=f"Expanded form: {res}",
                top_passages=[],
                trace=["Executed expand_expr via SymPy Solver"],
                score=1.0
            )
        except Exception as e:
            return EvidenceRecord(
                engine_type="Green",
                status="failed",
                output=f"Error expanding expression: {str(e)}",
                top_passages=[],
                trace=[f"Error occurred in expand_expr: {str(e)}"],
                score=0.0
            )

    def evaluate_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            # Handle float evaluation for mathematical constants and operations
            cleaned = expr_str.replace("pi", "sympy.pi").replace("sqrt", "sympy.sqrt")
            expr, _ = self._parse_expr(expr_str)
            res = expr.evalf()
            return EvidenceRecord(
                engine_type="Green",
                status="success",
                output=f"Numerical evaluation: {res}",
                top_passages=[],
                trace=["Executed evaluate_expr via SymPy Solver"],
                score=1.0
            )
        except Exception as e:
            return EvidenceRecord(
                engine_type="Green",
                status="failed",
                output=f"Error evaluating expression: {str(e)}",
                top_passages=[],
                trace=[f"Error occurred in evaluate_expr: {str(e)}"],
                score=0.0
            )


# ─────────────────────────────────────────────
# Rule-based Intent Identification
# ─────────────────────────────────────────────
def _detect_intent(raw: str) -> str:
    r = raw.lower()
    compute_keywords = [
        "solve", "diff", "integrate", "factor", "expand", "simplify", "eval",
        "derivative", "integral", "d/d", "sqrt", "sin", "cos", "tan", "log"
    ]
    if any(k in r for k in compute_keywords) or "=" in r:
        return "compute"
    if "define" in r or "what is" in r or "definition" in r:
        return "define"
    if "explain" in r or "how" in r or "why" in r:
        return "explain"
    if "compare" in r or "difference between" in r or "vs" in r:
        return "compare"
    if "predict" in r or "forecast" in r or "what happens" in r:
        return "predict"
    return "define"  # Default fallback intent


def _extract_expression(raw: str) -> tuple[str, Optional[str]]:
    """Extracts raw equation/formula part by removing operational prefixes."""
    r = raw.strip()
    prefixes = [
        r"^solve\s+", r"^simplify\s+", r"^differentiate\s+", r"^diff\s+",
        r"^integrate\s+", r"^factor\s+", r"^expand\s+", r"^evaluate\s+", r"^eval\s+"
    ]
    for p in prefixes:
        r = re.sub(p, "", r, flags=re.IGNORECASE)

    # Optional variable tracking if stated as "w.r.t x" or "for x"
    var = None
    var_match = re.search(r"\s+(?:w\.r\.t|for|variable)\s+([a-z])", r, re.IGNORECASE)
    if var_match:
        var = var_match.group(1)
        r = r[:var_match.start()].strip()

    return r, var


# ─────────────────────────────────────────────
# Core Engine Implementation
# ─────────────────────────────────────────────
class GreenEngine:
    def __init__(self, knowledge_path: str = "knowledge/symbolic"):
        self.knowledge_path = knowledge_path
        self.solver = SymbolicSolver()
        self.kb_data = []
        self.bm25 = None
        self._load_knowledge()

    def _load_knowledge(self):
        """Loads items from green.yaml and builds the local knowledge index."""
        if not os.path.exists(self.knowledge_path):
            print(f"[Warning] Knowledge base path not found: {self.knowledge_path}")
            return

        try:
            with open(self.knowledge_path, "r", encoding="utf-8") as f:
                self.kb_data = yaml.safe_load(f) or []
        except Exception as e:
            print(f"[Error] Failed to parse YAML knowledge base: {str(e)}")
            self.kb_data = []

        # Build corpus using keywords and content metadata
        corpus_tokens = []
        for item in self.kb_data:
            keywords = item.get("keyword", "")
            content = item.get("content", "")
            combined_text = f"{keywords} {content}"
            corpus_tokens.append(_tokenize(combined_text))

        if corpus_tokens:
            self.bm25 = BM25Okapi(corpus_tokens)

    def status(self) -> str:
        return f"GreenEngine active. KB size: {len(self.kb_data)} records mapped."

    def evaluate(self, query: Query, top_n: int = 2) -> EvidenceRecord:
        """
        Aligned Interface: Processes the user query and returns a single EvidenceRecord.
        """
        trace_log = []
        trace_log.append("Initializing Green Engine retrieval and symbolic pipeline.")
        trace_log.append(f"Received query text: '{query.text}'")

        # Aligned tokens mapping fallback
        query_tokens = query.tokens if query.tokens else _tokenize(query.text)

        intent = _detect_intent(query.text)

        # Route 1: Computational Logic Execution
        if intent == "compute":
            trace_log.append("Intent 'compute' detected. Diverting to Symbolic Solver.")
            compute_res = self._handle_compute(query.text)
            if compute_res and compute_res.status == "success":
                # Sync and pull potential top passages from local knowledge database
                top_passages_list = []
                if self.bm25:
                    top_items = self.bm25.get_top_n(query_tokens, self.kb_data, n=top_n)
                    for item in top_items:
                        summary_string = f"[{str(item.get('intent')).upper()}] Domain: {item.get('domain')} | Content: {item.get('content')}"
                        top_passages_list.append(summary_string)

                compute_res.top_passages = top_passages_list
                compute_res.trace = trace_log + [f"Symbolic result: {compute_res.output}"] + compute_res.trace
                return compute_res

        # Route 2: Information Retrieval (Default fallback or conceptual query mapping)
        if self.bm25 and len(self.kb_data) > 0:
            trace_log.append(f"Searching database with tokens: {query_tokens}")
            top_items = self.bm25.get_top_n(query_tokens, self.kb_data, n=top_n)

            top_passages_list = []
            for item in top_items:
                summary_string = f"[{str(item.get('intent')).upper()}] Domain: {item.get('domain')} | Content: {item.get('content')}"
                top_passages_list.append(summary_string)

            if top_items:
                best_item = top_items[0]
                trace_log.append(f"Top match locked in Domain: [{best_item.get('domain')}] via BM25 retrieval.")
                return EvidenceRecord(
                    engine_type="Green",
                    status="success",
                    output=best_item.get("content", "").strip(),
                    top_passages=top_passages_list,
                    trace=trace_log,
                    score=0.85
                )

        # Fallback if everything fails
        trace_log.append("No symbolic matches or knowledge records found.")
        return EvidenceRecord(
            engine_type="Green",
            status="failed",
            output="No matching symbolic data or mathematical result found.",
            top_passages=[],
            trace=trace_log,
            score=0.0
        )

    def _handle_compute(self, raw: str) -> EvidenceRecord:
        r = raw.lower()

        if re.search(r"\bdiff(erentiate)?\b|derivative\b|d/d[a-z]", r):
            expr, var = _extract_expression(raw)
            return self.solver.differentiate(expr, var)

        if re.search(r"\bintegrat|integral\b", r):
            expr, var = _extract_expression(raw)
            return self.solver.integrate_expr(expr, var)

        if re.search(r"\bfactor\b", r):
            expr, _ = _extract_expression(raw)
            return self.solver.factor_expr(expr)

        if re.search(r"\bexpand\b", r):
            expr, _ = _extract_expression(raw)
            return self.solver.expand_expr(expr)

        if re.search(r"\bsimplif", r):
            expr, _ = _extract_expression(raw)
            return self.solver.simplify_expr(expr)

        if re.search(r"\bsolve\b|=\s*0|=\s*[0-9]", r):
            expr, var = _extract_expression(raw)
            return self.solver.solve_equation(expr, var)

        if re.search(r"\beval(uate)?\b|pi|sqrt|sin|cos|tan|log|exp", r):
            expr, _ = _extract_expression(raw)
            return self.solver.evaluate_expr(expr)

        # Fallback evaluation catch-all
        expr, var = _extract_expression(raw)
        return self.solver.solve_equation(expr, var)