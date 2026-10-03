from app.modules.seal_note.policy import (
    can_edit_note,
    is_sealed,
    note_hidden,
    seal_flag,
)


def test_is_sealed_normalizes_values():
    assert is_sealed(1) is True
    assert is_sealed(True) is True
    assert is_sealed(0) is False
    assert is_sealed(False) is False
    assert is_sealed(None) is False


def test_seal_flag_values():
    assert seal_flag(True) == 1
    assert seal_flag(False) == 0


def test_sealed_note_hidden_before_fulfill():
    for status in ("open", "claimed", "released"):
        assert note_hidden(1, status) is True


def test_sealed_note_visible_when_fulfilled():
    assert note_hidden(True, "fulfilled") is False


def test_unsealed_note_visible_in_every_status():
    for status in ("open", "claimed", "released", "fulfilled"):
        assert note_hidden(False, status) is False
        assert note_hidden(None, status) is False


def test_can_edit_note_open_and_released():
    assert can_edit_note("open") == {"ok": True, "reason": ""}
    assert can_edit_note("released") == {"ok": True, "reason": ""}


def test_can_edit_note_blocked_when_claimed():
    r = can_edit_note("claimed")
    assert r["ok"] is False and r["reason"] == "note_locked_claimed"


def test_can_edit_note_blocked_when_fulfilled():
    r = can_edit_note("fulfilled")
    assert r["ok"] is False and r["reason"] == "note_locked_fulfilled"
