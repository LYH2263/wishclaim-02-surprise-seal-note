import pytest

from app.modules.seal_note.projection import project_wish, project_wishes

COLUMNS = ("id", "title", "note", "status", "claimer", "claimed_at", "expires_at",
           "seal_note", "data_quality")


def wish(status="open", seal=1, note="悄悄话"):
    return {
        "id": 1, "title": "神秘礼物", "note": note, "status": status,
        "claimer": "bob" if status == "claimed" else None,
        "claimed_at": None, "expires_at": None,
        "seal_note": seal, "data_quality": "clean",
    }


def test_redacts_sealed_open():
    out = project_wish(wish("open"))
    assert out["note"] == ""
    assert out["note_sealed"] is True and out["seal_note"] is True
    assert out["title"] == "神秘礼物" and out["status"] == "open"


def test_redacts_sealed_claimed():
    out = project_wish(wish("claimed"))
    assert out["note"] == "" and out["note_sealed"] is True
    assert out["claimer"] == "bob"


def test_redacts_sealed_released():
    out = project_wish(wish("released"))
    assert out["note"] == "" and out["note_sealed"] is True


def test_reveals_sealed_fulfilled():
    out = project_wish(wish("fulfilled"))
    assert out["note"] == "悄悄话"
    assert out["note_sealed"] is True and out["seal_note"] is True


@pytest.mark.parametrize("status", ["open", "claimed", "released", "fulfilled"])
def test_unsealed_passthrough_every_status(status):
    out = project_wish(wish(status, seal=0, note="明文附言"))
    assert out["note"] == "明文附言"
    assert out["note_sealed"] is False and out["seal_note"] is False


def test_projection_preserves_other_fields():
    out = project_wish(wish("claimed"))
    for col in COLUMNS:
        assert col in out
    assert out["id"] == 1 and out["data_quality"] == "clean"


def test_project_wishes_maps_list_and_empty():
    assert project_wishes([]) == []
    outs = project_wishes([wish("open"), wish("fulfilled")])
    assert outs[0]["note"] == "" and outs[1]["note"] == "悄悄话"
