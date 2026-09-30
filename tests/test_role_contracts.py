import pytest

from role_contracts import execute_role, get_role_contract, run_role_sequence,  validate_question


def test_researcher_follows_role_contract():
    result = execute_role(role_name="researcher", question="What is agent memory?", requested_output="notes")

    assert result["status"] == "completed"
    assert result["role"] == "researcher"
    assert result["output_type"] == "notes"
    assert "Facts collected" in result["content"]


def test_role_cannot_write_outside_contract():
    result = execute_role(role_name="researcher", question="What is agent memory?", requested_output="answer")

    assert result["status"] == "rejected"
    assert result["role"] == "researcher"
    assert "may only produce" in result["reason"]

def test_unknown_role_is_rejected():
    with pytest.raises(ValueError, match="Unknown role"):
        get_role_contract("planner")

def test_empty_question_is_rejected():
    with pytest.raises(ValueError, match="cannot be empty"):
        validate_question("   ")

def test_role_sequence_completes():
    trace = run_role_sequence("Explain collaboration.")

    assert len(trace) == 3
    assert trace[0]["role"] == "researcher"
    assert trace[1]["role"] == "critic"
    assert trace[2]["role"] == "writer"

    assert all(item["status"] == "completed" for item in trace)
    