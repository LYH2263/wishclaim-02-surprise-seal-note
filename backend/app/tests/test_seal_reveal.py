import sqlite3

import pytest

from app import seed
from app.db import connect
from app.modules.seal_note import fulfill_reveal, edit_note, project_wish, project_wishes


@pytest.fixture()
def db(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    seed.init_db()
    return connect


def insert(c, title="愿望", status="open", note="悄悄话", seal=1, claimer=None):
    cur = c.execute(
        "INSERT INTO wishes(title,note,status,claimer,seal_note,data_quality)"
        " VALUES (?,?,?,?,?,?)",
        (title, note, status, claimer, seal, "clean"),
    )
    c.commit()
    return cur.lastrowid


def test_fulfill_reveal_flips_claimed_to_fulfilled(db):
    c = db()
    wid = insert(c, status="claimed", claimer="bob")
    assert fulfill_reveal(c, wid) == {"ok": True, "status": "fulfilled"}
    row = dict(c.execute("SELECT * FROM wishes WHERE id=?", (wid,)).fetchone())
    assert row["status"] == "fulfilled"
    assert project_wish(row)["note"] == "悄悄话"
    c.close()


def test_fulfill_reveal_requires_claim(db):
    c = db()
    wid = insert(c, status="open")
    r = fulfill_reveal(c, wid)
    assert r["ok"] is False and r["reason"] == "need_claim"
    row = c.execute("SELECT status FROM wishes WHERE id=?", (wid,)).fetchone()
    assert row["status"] == "open"
    c.close()


def test_fulfill_reveal_missing_wish(db):
    c = db()
    assert fulfill_reveal(c, 9999)["reason"] == "not_found"
    c.close()


def test_projection_reveals_only_after_fulfill(db):
    c = db()
    wid = insert(c, status="open", note="惊喜")
    row = lambda: dict(c.execute("SELECT * FROM wishes WHERE id=?", (wid,)).fetchone())
    assert project_wish(row())["note"] == ""
    c.execute("UPDATE wishes SET status='claimed', claimer='bob' WHERE id=?", (wid,)); c.commit()
    assert project_wish(row())["note"] == ""
    assert fulfill_reveal(c, wid)["ok"] is True
    assert project_wish(row())["note"] == "惊喜"
    c.close()


def test_edit_note_allowed_when_open(db):
    c = db()
    wid = insert(c, status="open", note="旧内容")
    r = edit_note(c, wid, "新内容")
    assert r["ok"] is True
    # 封存 open：即使对编辑者也不回明文
    assert r["wish"]["note"] == "" and r["wish"]["note_sealed"] is True
    assert c.execute("SELECT note FROM wishes WHERE id=?", (wid,)).fetchone()["note"] == "新内容"
    c.close()


def test_edit_note_allowed_when_released(db):
    c = db()
    wid = insert(c, status="released")
    assert edit_note(c, wid, "改写")["ok"] is True
    c.close()


def test_edit_note_blocked_when_claimed(db):
    c = db()
    wid = insert(c, status="claimed", note="原文")
    r = edit_note(c, wid, "偷改")
    assert r["ok"] is False and r["reason"] == "note_locked_claimed"
    assert c.execute("SELECT note FROM wishes WHERE id=?", (wid,)).fetchone()["note"] == "原文"
    c.close()


def test_edit_note_blocked_when_fulfilled(db):
    c = db()
    wid = insert(c, status="fulfilled", note="原文")
    r = edit_note(c, wid, "偷改")
    assert r["ok"] is False and r["reason"] == "note_locked_fulfilled"
    assert c.execute("SELECT note FROM wishes WHERE id=?", (wid,)).fetchone()["note"] == "原文"
    c.close()


def test_edit_note_missing_wish(db):
    c = db()
    assert edit_note(c, 9999, "x")["reason"] == "not_found"
    c.close()


def test_all_read_paths_share_one_projection(db):
    c = db()
    # 已认领未核销：墙路（全量）与我的认领路（按 claimer 过滤）对同一行投影必须一致且都遮蔽
    sealed_claimed = insert(c, status="claimed", note="秘密", claimer="bob")
    wall_row = dict(c.execute("SELECT * FROM wishes WHERE id=?", (sealed_claimed,)).fetchone())
    mine_row = dict(c.execute("SELECT * FROM wishes WHERE id=? AND claimer=?",
                              (sealed_claimed, "bob")).fetchone())
    wall_view = project_wish(wall_row)
    mine_view = project_wishes([mine_row])[0]
    assert wall_view == mine_view
    assert wall_view["note"] == "" and wall_view["note_sealed"] is True

    # 已核销：详情路与已完成路对同一行投影必须一致且都揭晓全文
    sealed_done = insert(c, status="fulfilled", note="谢谢", claimer="bob")
    detail_row = dict(c.execute("SELECT * FROM wishes WHERE id=?", (sealed_done,)).fetchone())
    done_row = dict(c.execute("SELECT * FROM wishes WHERE status='fulfilled' AND id=?",
                              (sealed_done,)).fetchone())
    detail_view = project_wish(detail_row)
    done_view = project_wishes([done_row])[0]
    assert detail_view == done_view
    assert detail_view["note"] == "谢谢" and detail_view["note_sealed"] is True
    c.close()


def test_legacy_db_migrates_seal_note_column(tmp_path, monkeypatch):
    monkeypatch.setenv("DATA_DIR", str(tmp_path))
    c = sqlite3.connect(str(tmp_path / "wishclaim.db"))
    c.execute(
        "CREATE TABLE wishes(id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT, note TEXT,"
        " status TEXT, claimer TEXT, claimed_at TEXT, expires_at TEXT, data_quality TEXT)")
    c.execute("CREATE TABLE settings(key TEXT PRIMARY KEY, value TEXT)")
    c.execute("INSERT INTO wishes(title,note,status,data_quality) VALUES ('旧愿望','旧附言','open','clean')")
    c.commit(); c.close()

    seed.init_db()
    seed.init_db()  # 二次调用不报错

    c = connect()
    cols = {r["name"] for r in c.execute("PRAGMA table_info(wishes)")}
    assert "seal_note" in cols
    row = dict(c.execute("SELECT * FROM wishes WHERE title='旧愿望'").fetchone())
    assert row["seal_note"] == 0
    out = project_wish(row)
    assert out["note"] == "旧附言" and out["note_sealed"] is False
    c.close()
