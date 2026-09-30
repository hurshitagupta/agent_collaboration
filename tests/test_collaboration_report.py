import pytest
import collaboration_report
from collaboration_report import calculate_metrics, generate_collaboration_report, validate_trace

def test_collaboration_report_success(monkeypatch):
    def fake_model_call(prompt):
        return (
            "Research and critique roles collaborated across two rounds. "
            "The first round requested a limitation, the writer revised the answer, and the second round was accepted. "
            "Human review was not required."
        )

    monkeypatch.setattr(collaboration_report, "call_model", fake_model_call)

    trace = [{"round": 1, "role": "critic", "critique": "REVISE: Add a limitation."},
        {"round": 1, "role": "writer", "revised_answer": "Updated answer."},
        {"round": 2, "role": "critic", "critique": "ACCEPT"},
        {"round": 2, "decision": "accepted"}]

    result = generate_collaboration_report(trace)

    assert result["status"] == "completed"
    assert result["metrics"]["review_rounds"] == 2
    assert result["metrics"]["final_decision"] == "accepted"
    assert result["report"]

def test_metrics_are_calculated_correctly():
    trace = [{"round": 1, "role": "critic"},
        {"round": 1, "role": "writer"},
        {"round": 2, "role": "critic"},
        {"decision": "accepted"}]

    metrics = calculate_metrics(trace)

    assert metrics["total_trace_events"] == 4
    assert metrics["review_rounds"] == 2
    assert metrics["roles"] == ["critic", "writer"]
    assert metrics["final_decision"] == "accepted"
    assert metrics["human_review_required"] is False

def test_human_review_is_detected():
    trace = [
        {"round": 1, "role": "critic"},
        {"decision": "needs_human_review"}]
    
    metrics = calculate_metrics(trace)

    assert metrics["human_review_required"] is True
    assert metrics["final_decision"] == "needs_human_review"

def test_empty_trace_is_rejected():
    with pytest.raises(ValueError, match="Trace cannot be empty"):
        validate_trace([])

def test_invalid_trace_item_is_rejected():
    with pytest.raises(ValueError, match="Each trace item must be a dictionary"):
        validate_trace([{"round": 1}, "invalid item"])