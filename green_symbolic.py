from __future__ import annotations

import re
import os
import sys
import yaml
import sympy
from typing import Optional
from rank_bm25 import BM25Okapi

# Allows direct script execution to import schemas
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from pipeline.schemas import Query, EvidenceRecord

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
                engine="green",
                content=f"Solutions for {var}: {sol}",
                score=1.0,
                source="SymPy Equation Solver",
                domain="mathematics",
                intent="compute"
            )
        except Exception as e:
            return EvidenceRecord(
                engine="green",
                content=f"Error solving equation: {str(e)}",
                score=0.0,
                source="SymPy Equation Solver",
                domain="mathematics",
                intent="compute"
            )

    def simplify_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            expr, _ = self._parse_expr(expr_str)
            res = sympy.simplify(expr)
            return EvidenceRecord(
                engine="green",
                content=f"Simplified expression: {res}",
                score=1.0,
                source="SymPy Simplifier",
                domain="mathematics",
                intent="compute"
            )
        except Exception as e:
            return EvidenceRecord(
                engine="green",
                content=f"Error simplifying expression: {str(e)}",
                score=0.0,
                source="SymPy Simplifier",
                domain="mathematics",
                intent="compute"
            )

    def differentiate(self, expr_str: str, var_str: Optional[str] = None) -> EvidenceRecord:
        try:
            expr, var_e = self._parse_expr(expr_str)
            var = self._get_var(var_str) if var_str else var_e
            res = sympy.diff(expr, var)
            return EvidenceRecord(
                engine="green",
                content=f"Derivative w.r.t {var}: {res}",
                score=1.0,
                source="SymPy Calculus Module",
                domain="mathematics",
                intent="compute"
            )
        except Exception as e:
            return EvidenceRecord(
                engine="green",
                content=f"Error performing differentiation: {str(e)}",
                score=0.0,
                source="SymPy Calculus Module",
                domain="mathematics",
                intent="compute"
            )

    def integrate_expr(self, expr_str: str, var_str: Optional[str] = None) -> EvidenceRecord:
        try:
            expr, var_e = self._parse_expr(expr_str)
            var = self._get_var(var_str) if var_str else var_e
            res = sympy.integrate(expr, var)
            return EvidenceRecord(
                engine="green",
                content=f"Integral w.r.t {var}: {res} + C",
                score=1.0,
                source="SymPy Calculus Module",
                domain="mathematics",
                intent="compute"
            )
        except Exception as e:
            return EvidenceRecord(
                engine="green",
                content=f"Error performing integration: {str(e)}",
                score=0.0,
                source="SymPy Calculus Module",
                domain="mathematics",
                intent="compute"
            )

    def factor_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            expr, _ = self._parse_expr(expr_str)
            res = sympy.factor(expr)
            return EvidenceRecord(
                engine="green",
                content=f"Factored form: {res}",
                score=1.0,
                source="SymPy Algebra Module",
                domain="mathematics",
                intent="compute"
            )
        except Exception as e:
            return EvidenceRecord(
                engine="green",
                content=f"Error factoring expression: {str(e)}",
                score=0.0,
                source="SymPy Algebra Module",
                domain="mathematics",
                intent="compute"
            )

    def expand_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            expr, _ = self._parse_expr(expr_str)
            res = sympy.expand(expr)
            return EvidenceRecord(
                engine="green",
                content=f"Expanded form: {res}",
                score=1.0,
                source="SymPy Algebra Module",
                domain="mathematics",
                intent="compute"
            )
        except Exception as e:
            return EvidenceRecord(
                engine="green",
                content=f"Error expanding expression: {str(e)}",
                score=0.0,
                source="SymPy Algebra Module",
                domain="mathematics",
                intent="compute"
            )

    def evaluate_expr(self, expr_str: str) -> EvidenceRecord:
        try:
            # Handle float evaluation for mathematical constants and operations
            cleaned = expr_str.replace("pi", "sympy.pi").replace("sqrt", "sympy.sqrt")
            expr, _ = self._parse_expr(expr_str)
            res = expr.evalf()
            return EvidenceRecord(
                engine="green",
                content=f"Numerical evaluation: {res}",
                score=1.0,
                source="SymPy Evaluator",
                domain="mathematics",
                intent="compute"
            )
        except Exception as e:
            return EvidenceRecord(
                engine="green",
                content=f"Error evaluating expression: {str(e)}",
                score=0.0,
                source="SymPy Evaluator",
                domain="mathematics",
                intent="compute"
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
    def __init__(self, knowledge_path: str):
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

    def run(self, query: Query) -> list[EvidenceRecord]:
        intent = _detect_intent(query.raw)
        records = []

        # Route 1: Computational Logic Execution
        if intent == "compute":
            compute_records = self._handle_compute(query.raw)
            records.extend(compute_records)

        # Route 2: Information Retrieval (Used for conceptual queries or computation backups)
        if self.bm25:
            top_items = self.bm25.get_top_n(query.tokens, self.kb_data, n=2)
            for item in top_items:
                # Calculate confidence relative to text query mapping
                records.append(EvidenceRecord(
                    engine="green",
                    content=item.get("content", ""),
                    score=0.85,
                    source=f"KB Node ({item.get('keyword', 'generic')})",
                    domain=item.get("domain", "mathematics"),
                    intent=item.get("intent", intent)
                ))

        return records

    def _handle_compute(self, raw: str) -> list[EvidenceRecord]:
        r = raw.lower()

        if re.search(r"\bdiff(erentiate)?\b|derivative\b|d/d[a-z]", r):
            expr, var = _extract_expression(raw)
            return [self.solver.differentiate(expr, var)]

        if re.search(r"\bintegrat|integral\b", r):
            expr, var = _extract_expression(raw)
            return [self.solver.integrate_expr(expr, var)]

        if re.search(r"\bfactor\b", r):
            expr, _ = _extract_expression(raw)
            return [self.solver.factor_expr(expr)]

        if re.search(r"\bexpand\b", r):
            expr, _ = _extract_expression(raw)
            return [self.solver.expand_expr(expr)]

        if re.search(r"\bsimplif", r):
            expr, _ = _extract_expression(raw)
            return [self.solver.simplify_expr(expr)]

        if re.search(r"\bsolve\b|=\s*0|=\s*[0-9]", r):
            expr, var = _extract_expression(raw)
            return [self.solver.solve_equation(expr, var)]

        if re.search(r"\beval(uate)?\b|pi|sqrt|sin|cos|tan|log|exp", r):
            expr, _ = _extract_expression(raw)
            return [self.solver.evaluate_expr(expr)]

        # Fallback evaluation catch-all
        expr, var = _extract_expression(raw)
        return [self.solver.solve_equation(expr, var)]