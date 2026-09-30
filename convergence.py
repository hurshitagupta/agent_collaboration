import os
import time
from dataclasses import dataclass, asdict
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
MAX_ROUNDS = 3

@dataclass
class CollaborationState:
    question: str
    answer: str
    critique: str = ""
    round_number: int = 0
    status: str = "in_progress"

def validate_text(value: str, field_name: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field_name} must be a string.")

    value = value.strip()

    if not value:
        raise ValueError(f"{field_name} cannot be empty.")

    if len(value) > 5000:
        raise ValueError(f"{field_name} exceeds the 5000 character limit.")

    return value


def call_model(prompt: str) -> str:
    if not MODEL_NAME or not BASE_URL or not API_KEY:
        raise RuntimeError("MODEL_NAME, BASE_URL and API_KEY must be configured.")

    client = OpenAI(api_key=API_KEY, base_url=BASE_URL, timeout=TIMEOUT_SECONDS)

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,messages=[{"role": "user", "content": prompt}])

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise ValueError("Model returned empty content.")

            return content.strip()

        except Exception as exc:
            last_error = exc

            if attempt == MAX_RETRIES:
                break

            time.sleep(0.5 * attempt)

    raise RuntimeError(f"Model call failed after {MAX_RETRIES} attempts: {last_error}")


def create_critique(question: str, answer: str) -> str:
    question = validate_text(question, "Question")
    answer = validate_text(answer, "Answer")

    prompt = f"""You are the critic in a collaborative AI workflow.

Question: {question}
Current answer: {answer}

Check these acceptance criteria:
1. The answer directly addresses the question.
2. The answer contains relevant evidence or explanation.
3. The answer includes at least one limitation where appropriate.
4. The answer is clear and concise.

If all criteria are satisfied, return exactly:

ACCEPT

Otherwise return:
REVISE: followed by concise feedback explaining what should change."""

    return call_model(prompt)


def revise_answer(question: str, answer: str, critique: str) -> str:
    validate_text(question, "Question")
    validate_text(answer, "Answer")
    validate_text(critique, "Critique")

    prompt = f"""You are the writer in a collaborative AI workflow.

Question:{question}

Current answer:{answer}

Critic feedback:{critique}

Revise the answer using the feedback. Return only the revised answer."""

    return call_model(prompt)


def has_converged(critique: str) -> bool:
    return critique.strip().upper() == "ACCEPT"

def converge(question: str, initial_answer: str, max_rounds: int = MAX_ROUNDS) -> tuple[CollaborationState, list[dict]]:

    question = validate_text(question, "Question")
    initial_answer = validate_text(initial_answer, "Answer")

    if max_rounds < 1 or max_rounds > MAX_ROUNDS:
        raise ValueError(f"max_rounds must be between 1 and {MAX_ROUNDS}.")

    state = CollaborationState(question=question, answer=initial_answer)

    trace = []

    for round_number in range(1, max_rounds + 1):
        state.round_number = round_number

        critique = create_critique(question=state.question, answer=state.answer)
        state.critique = critique

        trace.append({"round": round_number, "role": "critic", "critique": critique})

        if has_converged(critique):
            state.status = "converged"

            trace.append(
                {"round": round_number, "decision": "accepted"})

            return state, trace

        revised_answer = revise_answer(question=state.question, answer=state.answer, critique=critique)

        state.answer = revised_answer

        trace.append({"round": round_number, "role": "writer", "revised_answer": revised_answer})

    state.status = "needs_human_review"

    trace.append(
        {"decision": "needs_human_review", "reason": "maximum_review_rounds_reached"})

    return state, trace


def main() -> None:
    lines = []

    question = "What is memory in an AI agent?"
    initial_answer = "Memory lets an AI agent store information from previous interactions."

    lines.append("=== CONVERGENCE RUN ===")

    state, trace = converge( question=question, initial_answer=initial_answer)

    for item in trace:
        lines.append(str(item))

    lines.append("\n=== FINAL STATE ===")
    lines.append(str(asdict(state)))

    output = "\n".join(lines)

    print(output)

    output_file = OUTPUT_DIR / "convergence.txt"
    output_file.write_text(output, encoding="utf-8")

    print(f"\nSaved output to: {output_file}")


if __name__ == "__main__":
    main()