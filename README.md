# Topic 13 — Implement Collaboration

## Overview

This project implements a collaborative AI workflow using explicit role separation, artifact handoff, critique, convergence, and reporting.

The implementation covers all five assessment tasks:

1. Role Contracts
2. Artifact Handoff
3. Critique
4. Convergence
5. Collaboration Report

The project uses real LLM calls through OpenRouter for the collaboration tasks where language generation or evaluation is required.

---

## Project Structure

```text
collaboration/
│
├── role_contracts.py
├── artifact_handoff.py
├── critique.py
├── convergence.py
├── collaboration_report.py
│
├── tests/
│   ├── test_role_contracts.py
│   ├── test_artifact_handoff.py
│   ├── test_critique.py
│   ├── test_convergence.py
│   └── test_collaboration_report.py
│
├── outputs/
│   ├── role_contracts.txt
│   ├── artifact_handoff.txt
│   ├── critique.txt
│   ├── convergence.txt
│   └── collaboration_report.txt
│
├── README.md
├── requirements.txt
├── .env
└── .gitignore
```

---

## Setup

Create and activate a virtual environment.

### Windows

```bash
python -m venv .venv
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create a `.env` file:

```env
API_KEY=your_openrouter_api_key
MODEL_NAME=your_model_name
BASE_URL=https://openrouter.ai/api/v1
```

The API key is loaded from the environment and is not stored directly in the source code.

---

# Task 1 — Role Contracts

## Objective

Define clear responsibilities and output boundaries for each collaboration role.

The implementation contains three roles:

- `researcher` — produces notes
- `critic` — produces critique
- `writer` — produces the final answer

Each role has an explicit contract describing its responsibility and allowed output type.

A role is rejected if it attempts to produce an output outside its contract.

## Run

```bash
python role_contracts.py
```

Saved evidence:

```text
outputs/role_contracts.txt
```

## Test

```bash
pytest tests/test_role_contracts.py -v
```

The tests cover:

- valid role execution
- role boundary rejection
- unknown roles
- invalid input
- successful role sequence

---

# Task 2 — Artifact Handoff

## Objective

Demonstrate collaboration through explicit artifacts rather than hidden shared state.

The researcher uses an LLM to produce a research artifact containing:

- artifact ID
- creator
- assigned receiver
- generated content
- status

The artifact is then handed from the researcher to the critic.

The handoff validates ownership and receiver information before allowing the transfer.

## Run

```bash
python artifact_handoff.py
```

Saved evidence:

```text
outputs/artifact_handoff.txt
```

## Test

```bash
pytest tests/test_artifact_handoff.py -v
```

The tests cover:

- research artifact creation
- valid artifact handoff
- invalid sender
- invalid receiver
- empty artifact rejection

---

# Task 3 — Critique

## Objective

Allow the critic role to review a research artifact and produce structured feedback.

The researcher artifact is validated before being sent to the critic.

The critic uses an LLM to evaluate:

- relevance
- missing evidence
- missing context
- limitations
- required improvements

The result is stored in a separate critique artifact that references the original research artifact.

## Run

```bash
python critique.py
```

Saved evidence:

```text
outputs/critique.txt
```

## Test

```bash
pytest tests/test_critique.py -v
```

The tests cover:

- successful critique generation
- invalid artifact creator
- empty artifact content
- missing artifact ID
- artifact size limit

---

# Task 4 — Convergence

## Objective

Demonstrate an iterative collaboration loop between critic and writer until the answer satisfies defined acceptance criteria.

The workflow is:

```text
Initial Answer
      ↓
Critic Review
      ↓
Accepted?
   ↙      ↘
 Yes      No
  ↓        ↓
Done    Writer Revision
            ↓
        Next Round
```

The critic checks the answer using predefined acceptance criteria.

If the answer is not accepted, the writer uses the critique to revise it.

The collaboration is limited to a maximum of three review rounds.

If convergence is not reached within the allowed rounds, the workflow returns:

```text
needs_human_review
```

This prevents unlimited collaboration loops.

## Run

```bash
python convergence.py
```

Saved evidence:

```text
outputs/convergence.txt
```

## Test

```bash
pytest tests/test_convergence.py -v
```

The tests cover:

- immediate convergence
- convergence after revision
- maximum review rounds
- human-review fallback
- invalid round limits

---

# Task 5 — Collaboration Report

## Objective

Generate a final report from the collaboration trace.

The implementation first calculates measurable collaboration information including:

- total trace events
- number of review rounds
- roles involved
- final decision
- whether human review was required

The structured trace and metrics are then passed to the LLM to create a concise collaboration report.

## Run

```bash
python collaboration_report.py
```

Saved evidence:

```text
outputs/collaboration_report.txt
```

## Test

```bash
pytest tests/test_collaboration_report.py -v
```

The tests cover:

- successful report generation
- collaboration metrics
- human-review detection
- empty trace rejection
- invalid trace entries

---

# Guardrails

The implementation includes the following safety and robustness controls.

## Step / Round Limits

The convergence workflow uses:

```python
MAX_ROUNDS = 3
```

This prevents unlimited critique and revision cycles.

## Timeout

LLM calls use a configured timeout:

```python
TIMEOUT_SECONDS = 20
```

This prevents an external model request from hanging indefinitely.

## Retry

LLM operations use a capped retry mechanism:

```python
MAX_RETRIES = 2
```

Retries are limited so that model failures cannot cause an unlimited loop.

## Validation

Validation is applied to:

- user questions
- artifact content
- artifact IDs
- role ownership
- handoff receiver
- trace structure
- review-round limits
- model responses

Invalid inputs are rejected before continuing the workflow.

## Secret Hygiene

Credentials are loaded from `.env`:

```python
API_KEY = os.getenv("API_KEY")
```

No API keys are stored directly in the source files.

The `.env` file should be excluded through `.gitignore`.

---

# Testing

Run all automated tests with:

```bash
pytest tests/ -v
```

The tests use mocked model responses where required so that automated tests remain repeatable and do not depend on external API availability.

The main Python scripts use real OpenRouter LLM calls to generate runtime evidence.

---

# Evidence

Each task saves its observable output inside the `outputs/` directory:

```text
outputs/
├── role_contracts.txt
├── artifact_handoff.txt
├── critique.txt
├── convergence.txt
└── collaboration_report.txt
```