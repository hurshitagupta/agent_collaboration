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


@dataclass
class Artifact:
    artifact_id: str
    created_by: str
    assigned_to: str
    content: str
    status: str = "created"


def validate_question(question: str) -> str:
    if not isinstance(question, str):
        raise ValueError("Question must be a string.")

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if len(question) > 500:
        raise ValueError("Question exceeds the 500 character limit.")

    return question


def call_model(prompt: str) -> str:
    if not MODEL_NAME or not BASE_URL or not API_KEY:
        raise RuntimeError("MODEL_NAME, BASE_URL and API_KEY must be configured.")

    client = OpenAI(
        api_key=API_KEY,
        base_url=BASE_URL,
        timeout=TIMEOUT_SECONDS,
    )

    last_error = None

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[{"role": "user", "content": prompt}])

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


def create_research_artifact(question: str) -> Artifact:
    question = validate_question(question)

    prompt = f"""You are the Researcher in a collaborative AI workflow.
Your responsibility is to collect concise and relevant information.
Question: {question}

Return:
- important facts
- useful context
- one limitation

Do not write the final answer."""

    content = call_model(prompt)

    return Artifact(
        artifact_id="artifact-001",
        created_by="researcher",
        assigned_to="critic",
        content=content,
        status="ready_for_handoff",
    )


def handoff_artifact(artifact: Artifact, sender: str, receiver: str) -> dict:

    if not isinstance(artifact, Artifact):
        return {"status": "rejected", "reason": "Invalid artifact type."}

    if sender != artifact.created_by:
        return {
            "status": "rejected",
            "reason": f"Sender '{sender}' does not own artifact '{artifact.artifact_id}'."
        }

    if receiver != artifact.assigned_to:
        return {
            "status": "rejected",
            "reason": f"Artifact must be handed to '{artifact.assigned_to}', not '{receiver}'."
        }

    if not artifact.content.strip():
        return {"status": "rejected", "reason": "Artifact content cannot be empty."}

    artifact.status = "handed_off"

    return {
        "status": "completed",
        "artifact_id": artifact.artifact_id,
        "from": sender,
        "to": receiver,
        "artifact": asdict(artifact)
    }


def main():
    lines = []

    question = "What is memory in an AI agent?"

    lines.append("=== HAPPY PATH ===")

    artifact = create_research_artifact(question)

    lines.append("Researcher created artifact:")
    lines.append(str(asdict(artifact)))

    result = handoff_artifact(artifact=artifact, sender="researcher", receiver="critic")

    lines.append("\nHandoff result:")
    lines.append(str(result))

    lines.append("\n=== REJECTION PATH ===")

    rejected = handoff_artifact(artifact=artifact, sender="writer", receiver="critic")
    lines.append(str(rejected))
    output = "\n".join(lines)

    print(output)

    output_file = OUTPUT_DIR / "artifact_handoff.txt"
    output_file.write_text(output, encoding="utf-8")

    print(f"\nSaved output to: {output_file}")

if __name__ == "__main__":
    main()