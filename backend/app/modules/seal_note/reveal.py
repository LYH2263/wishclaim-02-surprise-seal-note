"""揭晓写库：核销揭晓与认领冻结期的附言改写。只吃 sqlite 连接，不依赖 FastAPI。"""

import sqlite3

from app.modules.seal_note.policy import can_edit_note
from app.modules.seal_note.projection import project_wish


def fulfill_reveal(c: sqlite3.Connection, wid: int) -> dict:
    r = c.execute("SELECT * FROM wishes WHERE id=?", (wid,)).fetchone()
    if not r:
        return {"ok": False, "reason": "not_found"}
    if r["status"] != "claimed":
        return {"ok": False, "reason": "need_claim"}
    c.execute("UPDATE wishes SET status='fulfilled' WHERE id=?", (wid,))
    c.commit()
    return {"ok": True, "status": "fulfilled"}


def edit_note(c: sqlite3.Connection, wid: int, note: str) -> dict:
    r = c.execute("SELECT * FROM wishes WHERE id=?", (wid,)).fetchone()
    if not r:
        return {"ok": False, "reason": "not_found"}
    guard = can_edit_note(r["status"])
    if not guard["ok"]:
        return {"ok": False, "reason": guard["reason"]}
    c.execute("UPDATE wishes SET note=? WHERE id=?", (note, wid))
    c.commit()
    fresh = c.execute("SELECT * FROM wishes WHERE id=?", (wid,)).fetchone()
    return {"ok": True, "wish": project_wish(dict(fresh))}
