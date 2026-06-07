import os
import yaml
from typing import List, Dict, Any
from dataclasses import dataclass, field

# 1. Shared Schemas Alignment
try:
    from pipeline.schemas import Query, EvidenceRecord
except ImportError:
    @dataclass
    class Query:
        text: str  # The raw input string entered by the user
        tokens: List[str] = field(default_factory=list)  # Normalized word tokens from the pipeline router


    @dataclass
    class EvidenceRecord:
        engine_type: str  # Engine identifier, strictly locked to "Red"
        status: str       # Execution status ("success" or "failed")
        output: str       # Final interpretive response wrapped in structural academic templates
        top_passages: List[str]  # Internal candidates packed for Member 6 (Fusion Layer)
        trace: List[str]  # Detailed logs supporting global (:debug) and (:why) commands
        score: float = 0.0  # Highest matching confidence weight for fusion blending calculation

# 2. Structured Interpretive Templates

TEMPLATES = {
    "define": (
        "[Interpretive Framework: Conceptual Definition]\n"
        "From a critical socio-cultural perspective, the core concept is elucidated as follows:\n"
        "  -> {content}\n"
        "This institutional definition underscores how systemic paradigms and shared norms "
        "collectively construct contemporary societal meanings."
    ),
    "analyze": (
        "[Interpretive Framework: Structural & Policy Analysis]\n"
        "A rigorous macro-political interrogation reveals the following underlying structural dynamics:\n"
        "  -> {content}\n"
        "This perspective highlights the persistent friction between institutionalized power, "
        "individual agency, and structural constraints within the ecosystem."
    ),
    "compare": (
        "[Interpretive Framework: Comparative Perspective]\n"
        "Cross-examining these distinct socio-philosophical paradigms reveals critical conceptual boundaries:\n"
        "  -> {content}\n"
        "Such comparative assessment enables us to systematically map ideological and ethical divergences "
        "across changing institutional environments."
    ),
    "explain": (
        "[Interpretive Framework: Narrative Explanation]\n"
        "To contextually unpack and synthesize this phenomenon, the analytical narrative suggests:\n"
        "  -> {content}\n"
        "This explanatory paradigm contextualizes the event not as an isolated empirical variable, "
        "but as an embedded manifestation of systemic historical shifts."
    ),
    "compute": (
        "[Interpretive Framework: Evaluative & Metric Interpretation]\n"
        "Interpreting these quantitative performance indicators through a qualitative framework implies:\n"
        "  -> {content}\n"
        "In interpretive inquiry, quantitative metrics serve as critical diagnostic baselines "
        "to expose structural disparities and formulate equitable policy interventions."
    )
}

# 3. Red Engine Implementation (Interpretive Synthesis Pipeline)

class RedEngine:
    def __init__(self, knowledge_base_dir: str = "knowledge/interpretive"):
        self.knowledge_base_dir = knowledge_base_dir
        self.rules_db: List[Dict[str, Any]] = []
        self.load_knowledge_base()

    def _clean_and_tokenize(self, text: str) -> List[str]:
        """
        Sanitize input text into lowercase word tokens by stripping common punctuations.
        """
        punctuations = [",", ".", ";", '"', "?", "!", ":", "(", ")", "[", "]", "-", "_", "/"]
        cleaned_text = text.lower()
        for p in punctuations:
            cleaned_text = cleaned_text.replace(p, " ")
        return [word.strip() for word in cleaned_text.split() if word.strip()]

    def load_knowledge_base(self):

        if not os.path.exists(self.knowledge_base_dir):
            print(f"[Warning] Interpretive directory not found: {self.knowledge_base_dir}")
            return

        for filename in os.listdir(self.knowledge_base_dir):
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(self.knowledge_base_dir, filename)
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        if isinstance(data, list):
                            self.rules_db.extend(data)
                except Exception as e:
                    print(f"[Warning] Ingestion failed for file {filename}: {e}")

        print(f"[System Check] Red Synthesis Engine successfully loaded {len(self.rules_db)} interpretive frameworks.")

    def evaluate(self, query: Query, top_n: int = 3) -> EvidenceRecord:
        trace_log = []
        trace_log.append("Initializing Red Engine interpretive pipeline.")
        trace_log.append(f"Scanning data against {len(self.rules_db)} active perspective frameworks.")

        query_words = query.tokens if query.tokens else self._clean_and_tokenize(query.text)
        trace_log.append(f"Normalized query words for matching: {query_words}")

        matched_candidates = []

        for rule in self.rules_db:
            raw_keyword = rule.get("keyword", "")
            kw_words = self._clean_and_tokenize(str(raw_keyword))

            # Calculate symbolic intersection count
            matched_tokens_local = [kw for kw in kw_words if kw in query_words]
            match_count = len(matched_tokens_local)

            if match_count > 0:
                # Deterministic scoring formula based on matching density
                base_score = (float(match_count) / len(kw_words)) * 10.0
                matched_candidates.append({
                    "rule": rule,
                    "score": base_score,
                    "tokens": matched_tokens_local
                })

        # Rank matched frameworks by confidence score descending
        matched_candidates.sort(key=lambda x: x["score"], reverse=True)

        # Sync Interface: Populate top candidates list to prevent Fusion Layer crashes
        top_passages_list = []
        for item in matched_candidates[:top_n]:
            r = item["rule"]
            summary_string = f"[{str(r.get('intent')).upper()}] Domain: {r.get('domain')} | Content: {r.get('content')}"
            top_passages_list.append(summary_string)

        if len(matched_candidates) > 0:
            best_match = matched_candidates[0]
            best_rule = best_match["rule"]
            intent_type = str(best_rule.get("intent", "explain")).lower()
            raw_content = str(best_rule.get("content", "")).strip()
            final_score = best_match["score"]

            # Data Cleansing: Strip any hardcoded prefix like 'Compare:' to prevent duplicate text formatting
            display_content = raw_content
            prefixes_to_strip = ["compare:", "analyze:", "define:", "explain:", "compute:"]
            for prefix in prefixes_to_strip:
                if display_content.lower().startswith(prefix):
                    display_content = display_content[len(prefix):].strip()

            if display_content and display_content[0].islower():
                display_content = display_content[0].upper() + display_content[1:]

            chosen_template = TEMPLATES.get(intent_type, TEMPLATES["explain"])
            final_output = chosen_template.format(content=display_content)

            trace_log.append(f"Top match locked in Domain: [{best_rule.get('domain')}] with Intent: [{intent_type}].")
            trace_log.append(f"Calculated match score: {round(final_score, 4)} via tokens: {best_match['tokens']}")
            trace_log.append("Successfully synthesised raw knowledge into structured narrative perspective template.")
            status_str = "success"
        else:
            # Elegant Fallback Strategy when no domain-specific keyword constraints are triggered
            final_output = (
                "[Interpretive Framework: General Social Responsibility Paradigm]\n"
                "The current query does not trigger specific policy or conceptual keywords in our interpretive database.\n"
                "Applying baseline systemic perspective: Social and philosophical phenomena must be continually evaluated "
                "through lenses of ethical accountability, democratic equity, and public welfare."
            )
            final_score = 1.0
            status_str = "success"
            trace_log.append("No specific interpretive rules matched. Triggered general responsibility paradigm fallback.")

        trace_log.append("Red Engine pipeline execution finished.")

        return EvidenceRecord(
            engine_type="Red",
            status=status_str,
            output=final_output,
            top_passages=top_passages_list,
            trace=trace_log,
            score=final_score
        )

# 4. Local Interactive Test Bench
if __name__ == "__main__":
    target_path = "knowledge/interpretive"

    print("=== Starting Red Engine (Interpretive) Standalone Validation ===")
    test_engine = RedEngine(knowledge_base_dir=target_path)

    print("\n[REPL Mode Active] Type 'exit' or 'quit' to terminate.")
    while True:
        print("\n" + "-" * 55)
        user_in = input("Enter an interpretive/policy query: ")
        if user_in.lower() in ["exit", "quit"]:
            print("Shutting down engine sandbox. Goodbye!")
            break
        if not user_in.strip():
            continue

        test_query = Query(text=user_in)
        record = test_engine.evaluate(test_query, top_n=3)

        print("\n==================== RED ENGINE REPORT ====================")
        print(f"Engine Type: {record.engine_type} | Status: {record.status}")
        print(f"Matching Confidence Score: {round(record.score, 4)}")

        print("\n[Output - Structured Interpretive Response]:")
        print(record.output)

        print("\n[CLI Trace Logs - (:debug / :why)]:")
        for line in record.trace:
            print(f"  -> {line}")

        if record.top_passages:
            print("  -> [Interface Sync] Internal candidate passages prepared for Fusion Layer")
            for idx, passage in enumerate(record.top_passages, 1):
                print(f"     |-- Candidate {idx}: {passage}")
        print("===========================================================")