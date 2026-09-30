import pytest

from critique import Artifact, critique_artifact, validate_artifact


def test_critique_success(monkeypatch):
    def fake_model_call(prompt):
        return "The research is relevant but should include a clearer example.The limitation is present. Add evidence before finalizing."

    monkeypatch.setattr("critique.call_model", fake_model_call)

    artifact = Artifact(
        artifact_id="artifact-001",
        created_by="researcher",
        content=("Agent memory stores useful information. A limitation is that information may become outdated."))

    result = critique_artifact(artifact)

    assert result.created_by == "critic"
    assert result.source_artifact_id == "artifact-001"
    assert result.status == "completed"
    assert result.critique

def test_wrong_role_is_rejected(monkeypatch):
    def fake_model_call(prompt):
        return "This should not be called."

    monkeypatch.setattr("critique.call_model", fake_model_call,)

    artifact = Artifact(
        artifact_id="artifact-002",
        created_by="writer",
        content="Some content."
    )

    with pytest.raises(ValueError, match="only accepts artifacts created by the researcher"):
        critique_artifact(artifact)


def test_empty_content_is_rejected():
    artifact = Artifact(
        artifact_id="artifact-003",
        created_by="researcher",
        content="")

    with pytest.raises(ValueError, match="content cannot be empty"):
        validate_artifact(artifact)


def test_empty_artifact_id_is_rejected():
    artifact = Artifact(
        artifact_id="",
        created_by="researcher",
        content="Valid content.")

    with pytest.raises(ValueError, match="Artifact ID cannot be empty"):
        validate_artifact(artifact)


def test_large_artifact_is_rejected():
    artifact = Artifact(
        artifact_id="artifact-004",
        created_by="researcher",
        content="a" * 5001)

    with pytest.raises(ValueError, match="exceeds the 5000 character limit"):
        validate_artifact(artifact)