import sqlite3
from datetime import datetime, timedelta, timezone

from app.modules.seal_note.policy import is_revealed, note_edit_allowed, note_visible
from app.modules.seal_note.projection import project_rows, project_wish
from app.modules.seal_note.reveal import apply_reveal, reveal_needed

NOW = datetime(2026, 1, 1, 12, 0, tzinfo=timezone.utc)
TS = NOW.isoformat()
SECRET = "床底下还有一份"


def row(**kw):
    base = {
        "id": 1, "title": "惊喜盒子", "note": SECRET, "status": "open",
        "claimer": None, "claimed_at": None, "expires_at": None,
        "data_quality": "clean", "seal_note": 1, "note_revealed_at": None,
    }
    base.update(kw)
    return base


# ---------- 封存策略 policy ----------

def test_reveal_only_after_fulfill_or_write():
    for status in ("open", "claimed", "released"):
        assert is_revealed(True, status, None) is False
    assert is_revealed(True, "fulfilled", None) is True   # 状态兜底真源
    assert is_revealed(True, "open", TS) is True          # 揭晓已落库
    assert is_revealed(False, "open", None) is False      # 未封存无所谓揭晓


def test_visibility_matrix():
    # 未封存:任何状态恒可见(与改造前一致)
    for status in ("open", "claimed", "released", "fulfilled"):
        assert note_visible(False, status, None) is True
    # 封存:核销前一律不可见——含 claimed,认领人无特权(拍板口径)
    for status in ("open", "claimed", "released"):
        assert note_visible(True, status, None) is False
    assert note_visible(True, "fulfilled", None) is True
    assert note_visible(True, "claimed", TS) is True  # 已落库揭晓即放行


def test_edit_policy_matrix():
    assert note_edit_allowed(True, "open")["ok"] is True
    assert note_edit_allowed(True, "released")["ok"] is True
    # 拍板:已认领未核销禁止改写封存附言
    r = note_edit_allowed(True, "claimed")
    assert r["ok"] is False and r["reason"] == "sealed_locked"
    # 已核销成为最终历史,封存与否都不可改
    assert note_edit_allowed(True, "fulfilled")["reason"] == "fulfilled_immutable"
    assert note_edit_allowed(False, "fulfilled")["reason"] == "fulfilled_immutable"
    # 未封存不受封存锁约束
    assert note_edit_allowed(False, "claimed")["ok"] is True


# ---------- 可见性投影 projection ----------

def test_unsealed_passthrough_byte_identical():
    w = project_wish(row(seal_note=0, note="羊毛", status="claimed"))
    assert w["note"] == "羊毛"
    assert w["seal_note"] is False and w["note_revealed"] is False


def test_sealed_masked_on_all_pre_fulfill_states():
    for status in ("open", "claimed", "released"):
        w = project_wish(row(status=status))
        assert w["note"] == "" and w["note_revealed"] is False and w["seal_note"] is True


def test_fulfilled_reveals_full_text():
    w = project_wish(row(status="fulfilled", note_revealed_at=TS))
    assert w["note"] == SECRET and w["note_revealed"] is True


def test_fulfilled_without_reveal_row_still_reveals():
    # 揭晓写库漏写也不许卡在封存态:禁止「详情已揭而已完成仍封」的镜像故障
    w = project_wish(row(status="fulfilled", note_revealed_at=None))
    assert w["note"] == SECRET and w["note_revealed"] is True


def test_three_paths_pin_same_projection():
    # 墙卡/公开详情/我的认领/已完成共用 project_wish:同一行出仓结果必然一致
    sealed_open = row(status="open")
    sealed_done = row(status="fulfilled", note_revealed_at=TS)
    for r in (sealed_open, sealed_done):
        single = project_wish(r)
        assert project_rows([r])[0] == single          # 列表路径 == 详情路径
        again = project_wish(dict(r))
        assert again == single                          # 纯函数,无路径差异
    assert single["note"] == SECRET                     # 已完成页与详情同揭全文


# ---------- 揭晓写库 reveal ----------

def _conn():
    c = sqlite3.connect(":memory:")
    c.row_factory = sqlite3.Row
    c.execute("CREATE TABLE wishes(id INTEGER PRIMARY KEY, seal_note INTEGER NOT NULL DEFAULT 0,"
              " note_revealed_at TEXT)")
    return c


def test_reveal_needed_only_for_sealed_unrevealed():
    assert reveal_needed(True, None) is True
    assert reveal_needed(True, TS) is False
    assert reveal_needed(False, None) is False


def test_apply_reveal_writes_once_and_keeps_first_timestamp():
    c = _conn()
    c.execute("INSERT INTO wishes(id, seal_note) VALUES (1, 1)")
    wish = {"id": 1, "seal_note": 1, "note_revealed_at": None}
    assert apply_reveal(c, wish, NOW) is True
    got = c.execute("SELECT note_revealed_at FROM wishes WHERE id=1").fetchone()
    assert got["note_revealed_at"] == TS
    # 二次核销不覆盖首揭时间
    later = NOW + timedelta(hours=1)
    wish2 = {"id": 1, "seal_note": 1, "note_revealed_at": TS}
    assert apply_reveal(c, wish2, later) is False
    got = c.execute("SELECT note_revealed_at FROM wishes WHERE id=1").fetchone()
    assert got["note_revealed_at"] == TS


def test_apply_reveal_noop_for_unsealed():
    c = _conn()
    c.execute("INSERT INTO wishes(id, seal_note) VALUES (1, 0)")
    wish = {"id": 1, "seal_note": 0, "note_revealed_at": None}
    assert apply_reveal(c, wish, NOW) is False
    got = c.execute("SELECT note_revealed_at FROM wishes WHERE id=1").fetchone()
    assert got["note_revealed_at"] is None
