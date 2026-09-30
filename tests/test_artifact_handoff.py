from artifact_handoff import Artifact, create_research_artifact, handoff_artifact

def test_researcher_creates_artifact(monkeypatch):
    def fake_model_call(prompt):
        return (
            "Facts: Agent memory stores useful information. "
            "Context: It can support future decisions. "
            "Limitation: Stored information may become outdated."
        )

    monkeypatch.setattr("artifact_handoff.call_model", fake_model_call)

    artifact = create_research_artifact("What is memory in an AI agent?")

    assert artifact.created_by == "researcher"
    assert artifact.assigned_to == "critic"
    assert artifact.status == "ready_for_handoff"
    assert artifact.content


def test_artifact_handoff_success():
    artifact = Artifact(
        artifact_id="artifact-001",
        created_by="researcher",
        assigned_to="critic",
        content="Collected research facts.",
        status="ready_for_handoff")

    result = handoff_artifact( artifact, sender="researcher", receiver="critic")
    assert result["status"] == "completed"
    assert result["from"] == "researcher"
    assert result["to"] == "critic"
    assert artifact.status == "handed_off"


def test_wrong_sender_is_rejected():
    artifact = Artifact(
        artifact_id="artifact-001",
        created_by="researcher",
        assigned_to="critic",
        content="Collected research facts.",
        status="ready_for_handoff"
    )

    result = handoff_artifact(artifact,  sender="writer", receiver="critic")

    assert result["status"] == "rejected"
    assert "does not own artifact" in result["reason"]


def test_wrong_receiver_is_rejected():
    artifact = Artifact(
        artifact_id="artifact-001",
        created_by="researcher",
        assigned_to="critic",
        content="Collected research facts.",
        status="ready_for_handoff",
    )

    result = handoff_artifact(artifact, sender="researcher", receiver="writer")

    assert result["status"] == "rejected"
    assert "must be handed to" in result["reason"]


def test_empty_artifact_is_rejected():
    artifact = Artifact(
        artifact_id="artifact-001",
        created_by="researcher",
        assigned_to="critic",
        content="",
        status="ready_for_handoff")

    result = handoff_artifact(artifact, sender="researcher", receiver="critic")

    assert result["status"] == "rejected"
    assert "cannot be empty" in result["reason"]