import os
import time
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

MODEL_NAME = os.getenv("MODEL_NAME")
BASE_URL = os.getenv("BASE_URL")
API_KEY = os.getenv("API_KEY")

MAX_RETRIES = 2
TIMEOUT_SECONDS = 20

def validate_trace(trace: list[dict]) -> None:
    if not isinstance(trace, list):
        raise ValueError("Trace must be a list.")

    if not trace:
        raise ValueError("Trace cannot be empty.")

    for item in trace:
        if not isinstance(item, dict):
            raise ValueError("Each trace item must be a dictionary.")

def call_model(prompt: str) -> str:
    if not MODEL_NAME or not BASE_URL or not API_KEY:
        raise RuntimeError("MODEL_NAME, BASE_URL and API_KEY must be configured.")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT_SECONDS)

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "You create concise collaboration reports from structured execution traces."},
                    {"role": "user", "content": prompt}]
                    )

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise ValueError("Model returned an empty report.")

            return content.strip()

        except Exception as exc:
            last_error = exc

            if attempt == MAX_RETRIES:
                break

            time.sleep(0.5 * attempt)

    raise RuntimeError(f"Report generation failed after {MAX_RETRIES} attempts: {last_error}")

def calculate_metrics(trace: list[dict]) -> dict:
    validate_trace(trace)

    rounds = set()
    roles = set()

    for item in trace:
        if "round" in item:
            rounds.add(item["round"])

        if "role" in item:
            roles.add(item["role"])

    final_decision = trace[-1].get("decision", "unknown")

    return {
        "total_trace_events": len(trace),
        "review_rounds": len(rounds),
        "roles": sorted(roles),
        "final_decision": final_decision,
        "human_review_required": (final_decision == "needs_human_review")
    }


def generate_collaboration_report(trace: list[dict]) -> dict:
    validate_trace(trace)
    metrics = calculate_metrics(trace)

    prompt = f"""Create a concise collaboration report from the following trace.

Trace: {trace}
Metrics: {metrics}

The report must include:
1. Roles involved
2. Number of review rounds
3. Main critique and revision activity
4. Final decision
5. Whether human review was required

Do not invent events that are not present in the trace."""

    report_text = call_model(prompt)
    return {"status": "completed", "metrics": metrics, "report": report_text}

def main() -> None:
    lines = []

    trace = [
        {"round": 1, "role": "critic", "critique": "REVISE: Add a limitation."},
        {"round": 1,"role": "writer","revised_answer": "Agent memory stores useful context, but stored information may become outdated."},
        {"round": 2, "role": "critic", "critique": "ACCEPT"},
        {"round": 2, "decision": "accepted"},
    ]

    lines.append("=== HAPPY PATH ===")

    result = generate_collaboration_report(trace)

    lines.append(str(result["metrics"]))
    lines.append("\nGenerated report:")
    lines.append(result["report"])

    lines.append("\n=== REJECTION PATH ===")

    try:
        generate_collaboration_report([])
    except ValueError as exc:
        lines.append(str({"status": "rejected", "reason": str(exc)}))

    output = "\n".join(lines)

    print(output)

    output_file = OUTPUT_DIR / "collaboration_report.txt"
    output_file.write_text(output, encoding="utf-8")

    print(f"\nSaved output to: {output_file}")

if __name__ == "__main__":
    main()