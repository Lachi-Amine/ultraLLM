import os
import yaml
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from rank_bm25 import BM25Okapi


# 1. Core Data Structures

@dataclass
class Query:
    text: str  # The original search sentence from the user
    tokens: List[str] = field(default_factory=list)  # Words split from the sentence


@dataclass
class EvidenceRecord:
    engine_type: str  # Always "Yellow" for this engine
    status: str  # "success" or "failed"
    output: str  # The best matching answer found
    top_passages: List[str]  # A list of top matching answers
    trace: List[str]  # Step-by-step logs for debugging (:debug command)
    score: float = 0.0  # The highest search score from BM25



# 2. Implementation

class YellowEngine:
    def __init__(self, knowledge_base_dir: str = "knowledge/empirical"):

        self.knowledge_base_dir = knowledge_base_dir
        self.empirical_knowledge = []  # This will store all our YAML data items
        self.bm25 = None  # This will hold the search index later

        self.load_knowledge_base()
        self.initialize_bm25_index()

    def load_knowledge_base(self):
        """
        Scan the folder and read all the YAML data files.
        """
        # Check if the directory exists, if not, create it so it won't crash
        if not os.path.exists(self.knowledge_base_dir):
            os.makedirs(self.knowledge_base_dir, exist_ok=True)
            return

        for filename in os.listdir(self.knowledge_base_dir):
            # We only care about .yaml or .yml files
            if filename.endswith(".yaml") or filename.endswith(".yml"):
                file_path = os.path.join(self.knowledge_base_dir, filename)

                try:
                    # Open and read the YAML file
                    with open(file_path, "r", encoding="utf-8") as f:
                        data = yaml.safe_load(f)
                        # Check if the data inside is a list
                        if isinstance(data, list):
                            # Add all items into our main knowledge list
                            for item in data:
                                self.empirical_knowledge.append(item)
                except Exception as e:
                    print("[Warning] Cannot open file " + filename + ": " + str(e))

        print("[System Check] Successfully loaded " + str(len(self.empirical_knowledge)) + " records from database.")

    def initialize_bm25_index(self):
        """
        Create the BM25 search index using keywords and content.
        """
        # If there is no data, we cannot build the index
        if len(self.empirical_knowledge) == 0:
            return

        tokenized_corpus = []  # This will hold lists of words for each record

        # Process each entry one by one
        for entry in self.empirical_knowledge:
            keywords = entry.get("keyword", "")
            content = entry.get("content", "")

            # Combine keywords and content to make search more accurate
            combined_text = keywords + " " + content
            # Convert everything to lowercase
            combined_text = combined_text.lower()
            # Split the string by spaces into a list of words
            words_list = combined_text.split()

            tokenized_corpus.append(words_list)

        self.bm25 = BM25Okapi(tokenized_corpus)

    def evaluate(self, query: Query, top_n: int = 2) -> EvidenceRecord:
        """
        Search the database using the user's query and return the result.
        """
        # Create a list to record our steps for the CLI :debug command
        trace_log = []
        trace_log.append("Initializing Yellow Engine retrieval pipeline.")
        trace_log.append("Received query text: '" + query.text + "'")

        # Safety check: if index is not ready, return a failed record
        if self.bm25 is None or len(self.empirical_knowledge) == 0:
            trace_log.append("Error: Database is empty or index is not ready.")
            return EvidenceRecord(
                engine_type="Yellow",
                status="failed",
                output="Yellow Engine database is empty.",
                top_passages=[],
                trace=trace_log,
                score=0.0
            )

        try:
            # Step 1: Prepare the search tokens (lowercase them)
            query_tokens = []
            if len(query.tokens) > 0:
                for t in query.tokens:
                    query_tokens.append(t.lower())
                trace_log.append("Using tokens from upstream: " + str(query_tokens))
            else:
                local_words = query.text.lower().split()
                for w in local_words:
                    query_tokens.append(w)
                trace_log.append("No upstream tokens. Local split results: " + str(query_tokens))

            # Step 2: Calculate BM25 scores for all documents
            doc_scores = self.bm25.get_scores(query_tokens)

            # Step 3: Find the best matches
            # Create pairs of (index, score) so we don't lose the original position
            score_pairs = []
            for i in range(len(doc_scores)):
                score_pairs.append((i, doc_scores[i]))

            # Sort the pairs by score in descending order (highest score first)
            score_pairs.sort(key=lambda item: item[1], reverse=True)

            # Filter out the items that have a score of 0 (meaning no match at all)
            valid_pairs = []
            for pair in score_pairs:
                if pair[1] > 0:
                    valid_pairs.append(pair)

            # Take only the top_n items from the valid pairs
            final_pairs = valid_pairs[:top_n]

            # Step 4: If nothing matches, return a failed record
            if len(final_pairs) == 0:
                trace_log.append("BM25 finished. Found 0 matching items.")
                return EvidenceRecord(
                    engine_type="Yellow",
                    status="failed",
                    output="No matching empirical data found.",
                    top_passages=[],
                    trace=trace_log,
                    score=0.0
                )

            # Step 5: Gather data from the best matches
            top_passages = []
            for rank_index in range(len(final_pairs)):
                current_pair = final_pairs[rank_index]
                doc_id = current_pair[0]
                doc_score = current_pair[1]

                matched_entry = self.empirical_knowledge[doc_id]
                content_string = matched_entry.get("content", "").strip()
                top_passages.append(content_string)

                # Add nice log info for the user
                log_msg = "Matched Rank " + str(rank_index + 1) + " (Domain: " + str(
                    matched_entry.get("domain")) + ", Intent: " + str(
                    matched_entry.get("intent")) + ") with score: " + str(round(doc_score, 4))
                trace_log.append(log_msg)

            # Get the best entry (Rank 1 item)
            best_doc_id = final_pairs[0][0]
            highest_score = final_pairs[0][1]
            best_entry = self.empirical_knowledge[best_doc_id]
            best_explanation = best_entry.get("content", "").strip()

            trace_log.append("Package created successfully. Sending to fusion layer.")

            # Return the complete record
            return EvidenceRecord(
                engine_type="Yellow",
                status="success",
                output=best_explanation,
                top_passages=top_passages,
                trace=trace_log,
                score=float(highest_score)
            )

        except Exception as e:
            trace_log.append("Fatal error occurred: " + str(e))
            return EvidenceRecord(
                engine_type="Yellow",
                status="failed",
                output="An exception happened inside the engine.",
                top_passages=[],
                trace=trace_log,
                score=0.0
            )



# 3. Local Test Bench (Interactive REPL Mode)
if __name__ == "__main__":
    target_folder = "knowledge/empirical"

    print("--- Starting Yellow Engine Test ---")
    print("Scanning folder path: " + target_folder)

    test_engine = YellowEngine(knowledge_base_dir=target_folder)

    # Check if we actually loaded the data successfully
    if len(test_engine.empirical_knowledge) == 0:
        print("[Error] No data loaded! Did you put Yellow.yaml in the right folder?")
    else:
        print("\n===================================================")
        print("Successfully loaded " + str(len(test_engine.empirical_knowledge)) + " records.")
        print("Entering Interactive CLI Mode (REPL Test).")
        print("Type 'quit' or 'exit' to stop the test.")
        print("===================================================")

        # Start an infinite loop to let you type questions live
        while True:
            print("\n---------------------------------------------------")
            user_input = input("Enter your scientific question: ")

            # Check if the user wants to leave the test loop
            if user_input.lower() == "quit" or user_input.lower() == "exit":
                print("Exiting interactive test. Goodbye!")
                break

            # If the user typed nothing, skip and ask again
            if user_input.strip() == "":
                continue

            # Create a query object
            # Since we don't have the upstream feature tokenizer attached yet,
            # we pass an empty list to tokens, and our engine will split it locally.
            sample_query = Query(text=user_input, tokens=[])

            # Run the search engine evaluate function
            output_record = test_engine.evaluate(sample_query, top_n=3)

            # Print out the formatted report for your manual verification
            print("\n================== RESULT REPORT ==================")
            print("Status: " + output_record.status)
            print("Top Score: " + str(round(output_record.score, 4)))
            print("\n[Output - Empirical Explanation]:\n" + output_record.output)
            print("\n[Output - Top Passages]:\n" + str(output_record.top_passages))
            print("\n[CLI Trace Logs - (:debug / :why)]:")
            for line in output_record.trace:
                print("  -> " + line)
            print("===================================================")
