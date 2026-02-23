import json
import subprocess
from pathlib import Path

from src.summariser.prompt_templates import (
    INDIVIDUAL_SUMMARY_TEMPLATE,
    PAIRING_TEMPLATE,
    SENTENCE_CLUSTER_TEMPLATE,
    PARAGRAPH_CLUSTER_TEMPLATE,
)


class Summariser:
    """
    Summariser class to generate summaries using an Ollama LLM.

    Supported methods:
      1. individual
      2. pairing
      3. sentence_clustering
      4. paragraph_clustering

    Entity handling is delegated entirely to the prompt templates.
    """

    def __init__(self, model="qwen3:8b"):
        self.model = model

    # ------------------------------------------------------------------
    # Core summarisation entrypoint
    # ------------------------------------------------------------------

    def summarize(self, data, method, entities=None):
        """
        Generate summary using selected method.

        Args:
            data: Input data
            method: summarisation method
            entities: list of entities (passed to template via payload)

        Returns:
            Generated summary
        """

        # ------------------------
        # Individual summarisation
        # ------------------------

        if method == "individual":

            template = INDIVIDUAL_SUMMARY_TEMPLATE

            if isinstance(data, list):

                summaries = []

                for i, text in enumerate(data):

                    print(f"[Summariser] Summarizing individual document {i+1}/{len(data)}")

                    payload = {
                        "entities": entities,
                        "data": text
                    } if entities else text

                    prompt = (
                        template
                        + "\n\nData:\n"
                        + json.dumps(payload, indent=2, ensure_ascii=False)
                        + "\n\nSummary:"
                    )

                    summaries.append(self.call_llm(prompt))

                return summaries

            else:

                payload = {
                    "entities": entities,
                    "data": data
                } if entities else data

                prompt = (
                    template
                    + "\n\nData:\n"
                    + json.dumps(payload, indent=2, ensure_ascii=False)
                    + "\n\nSummary:"
                )

                return self.call_llm(prompt)

        # ------------------------
        # Select template
        # ------------------------

        if method == "pairing":

            template = PAIRING_TEMPLATE

        elif method == "sentence_clustering":

            template = SENTENCE_CLUSTER_TEMPLATE

        elif method == "paragraph_clustering":

            template = PARAGRAPH_CLUSTER_TEMPLATE

        else:

            raise ValueError(f"Unknown summarization method: {method}")

        # ------------------------
        # Prepare payload
        # ------------------------

        payload = {
            "entities": entities,
            "data": data
        } if entities else data

        prompt = (
            template
            + "\n\nData:\n"
            + json.dumps(payload, indent=2, ensure_ascii=False)
        )

        return self.call_llm(prompt)

    # ------------------------------------------------------------------
    # Ollama call
    # ------------------------------------------------------------------

    def call_llm(self, prompt):

        result = subprocess.run(
            ["ollama", "run", self.model, "--hidethinking"],
            input=prompt.encode("utf-8"),
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )

        output = result.stdout.decode("utf-8").strip()

        if result.returncode != 0:
            print("Ollama stderr:", result.stderr.decode("utf-8"))

        return output

    # ------------------------------------------------------------------
    # Ablation wrapper
    # ------------------------------------------------------------------

    def run_for_ablation(self, mode, method, input_file, results_dir, entities=None):

        print(f"[Summariser] Summarizing {method} results for mode={mode}")

        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        summary = self.summarize(
            data=data,
            method=method,
            entities=entities
        )

        output_file = Path(results_dir) / f"summary_{method}.txt"

        with open(output_file, "w", encoding="utf-8") as f:

            if isinstance(summary, list):

                f.write("\n\n".join(summary))

            else:

                f.write(summary)

        print(f"[Summariser] Saved {method} summary to {output_file}")
