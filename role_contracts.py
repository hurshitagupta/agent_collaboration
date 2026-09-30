from dataclasses import dataclass
from pathlib import Path
from typing import Dict

OUTPUT_DIR = Path("outputs")
OUTPUT_DIR.mkdir(exist_ok=True)

MAX_ROLE_CALLS = 3

@dataclass(frozen=True)
class RoleContract:
    name: str
    responsibility: str
    allowed_output: str

ROLE_CONTRACTS: Dict[str, RoleContract] = {
    "researcher": RoleContract(
        name="researcher",
        responsibility="Collect relevant facts for the question.",
        allowed_output="notes"),
    "critic": RoleContract(
        name="critic",
        responsibility="Review notes and identify missing evidence or limitations.",
        allowed_output="critique"),
    "writer": RoleContract(
        name="writer",
        responsibility="Create the final answer using approved notes and critique.",
        allowed_output="answer")}

def validate_question(question: str) -> str:
    if not isinstance(question, str):
        raise ValueError("Question must be a string.")

    question = question.strip()

    if not question:
        raise ValueError("Question cannot be empty.")

    if len(question) > 500:
        raise ValueError("Question exceeds the 500 character limit.")

    return question

def get_role_contract(role_name: str) -> RoleContract:
    if role_name not in ROLE_CONTRACTS:
        raise ValueError(f"Unknown role: {role_name}")

    return ROLE_CONTRACTS[role_name]

def execute_role(role_name: str, question: str, requested_output: str) -> dict:
    question = validate_question(question)
    contract = get_role_contract(role_name)

    if requested_output != contract.allowed_output:
        return {
            "status": "rejected",
            "role": role_name,
            "reason": (f"Role '{role_name}' may only produce '{contract.allowed_output}', not '{requested_output}'.")}

    if role_name == "researcher":
        content = f"Facts collected for: {question}"

    elif role_name == "critic":
        content = f"Critique prepared for: {question}"

    else:
        content = f"Final answer prepared for: {question}"

    return {
        "status": "completed",
        "role": role_name,
        "responsibility": contract.responsibility,
        "output_type": requested_output,
        "content": content
    }


def run_role_sequence(question: str) -> list[dict]:
    steps = [("researcher", "notes"), ("critic", "critique"), ("writer", "answer")]

    trace = []

    for step_number, (role, output_type) in enumerate(steps, start=1):
        if step_number > MAX_ROLE_CALLS:
            trace.append({"status": "stopped", "reason": "role_call_limit_reached"})
            break

        result = execute_role(role_name=role, question=question, requested_output=output_type)
        trace.append(result)

    return trace


def main() -> None:
    lines = []

    lines.append("=== HAPPY PATH ===")

    trace = run_role_sequence("What is agent memory?")

    for item in trace:
        lines.append(str(item))

    lines.append("\n=== REJECTION PATH ===")

    rejected = execute_role(role_name="researcher", question="What is agent memory?", requested_output="answer")

    lines.append(str(rejected))

    output = "\n".join(lines)

    print(output)

    output_file = OUTPUT_DIR / "role_contracts.txt"
    output_file.write_text(output, encoding="utf-8")

    print(f"\nSaved output to: {output_file}")


if __name__ == "__main__":
    main()