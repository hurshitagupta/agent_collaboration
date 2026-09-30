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
    content: str

@dataclass
class CritiqueArtifact:
    artifact_id: str
    source_artifact_id: str
    created_by: str
    critique: str
    status: str = "completed"

def validate_artifact(artifact: Artifact) -> None:
    if not isinstance(artifact, Artifact):
        raise ValueError("Input must be an Artifact.")

    if not artifact.artifact_id.strip():
        raise ValueError("Artifact ID cannot be empty.")

    if not artifact.created_by.strip():
        raise ValueError("Artifact creator cannot be empty.")

    if not artifact.content.strip():
        raise ValueError("Artifact content cannot be empty.")

    if len(artifact.content) > 5000:
        raise ValueError("Artifact content exceeds the 5000 character limit.")

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
                messages=[{"role": "system", "content": "You are a critic in a collaborative AI workflow. Review artifacts carefully and provide concise, actionable feedback."},
                        {"role": "user", "content": prompt}])

            content = response.choices[0].message.content

            if not content or not content.strip():
                raise ValueError("Model returned empty critique.")

            return content.strip()

        except Exception as exc:
            last_error = exc

            if attempt == MAX_RETRIES:
                break

            time.sleep(0.5 * attempt)

    raise RuntimeError(f"Critique model call failed after {MAX_RETRIES} attempts: {last_error}")

def critique_artifact(artifact: Artifact) -> CritiqueArtifact:
    validate_artifact(artifact)

    if artifact.created_by != "researcher":
        raise ValueError("Critic only accepts artifacts created by the researcher.")

    prompt = f""" Review the following research artifact.

Artifact ID: {artifact.artifact_id}
Research content: {artifact.content}

Evaluate it using these criteria:
1. Is the information relevant?
2. Is important evidence or context missing?
3. Is there at least one limitation?
4. What should be improved before writing the final answer?

Return a concise critique.
Do not write the final answer. """

    critique = call_model(prompt)

    return CritiqueArtifact(
        artifact_id=f"critique-{artifact.artifact_id}",
        source_artifact_id=artifact.artifact_id,
        created_by="critic",
        critique=critique,
    )


def main() -> None:
    lines = []

    lines.append("=== HAPPY PATH ===")

    research_artifact = Artifact(
        artifact_id="artifact-001",
        created_by="researcher",
        content=("AI agent memory stores information from previous interactions or tasks. It can help the agent reuse useful context and make better future decisions. A limitation is that stored information can become outdated."))

    critique = critique_artifact(research_artifact)

    lines.append("Research artifact:")
    lines.append(str(asdict(research_artifact)))

    lines.append("\nCritique artifact:")
    lines.append(str(asdict(critique)))

    lines.append("\n=== REJECTION PATH ===")

    invalid_artifact = Artifact(
        artifact_id="artifact-002",
        created_by="writer",
        content="Some content created by the wrong role."
    )

    try:
        critique_artifact(invalid_artifact)
    except ValueError as exc:
        lines.append(str({"status": "rejected", "reason": str(exc)}))

    output = "\n".join(lines)

    print(output)

    output_file = OUTPUT_DIR / "critique.txt"
    output_file.write_text(output, encoding="utf-8")

    print(f"\nSaved output to: {output_file}")

if __name__ == "__main__":
    main()