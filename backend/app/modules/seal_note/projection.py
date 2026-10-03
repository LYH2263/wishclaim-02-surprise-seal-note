"""可见性投影：全系统唯一的愿望读出整形。

墙卡 / 公开详情 / 我的认领 / 已完成 四路读接口都必须经过本模块，
使「封存而未核销」在任何页面口径一致，杜绝各端自行其是。
"""

from app.modules.seal_note.policy import is_sealed, note_hidden


def project_wish(row: dict) -> dict:
    out = dict(row)
    sealed = is_sealed(out.get("seal_note"))
    out["seal_note"] = sealed
    out["note_sealed"] = sealed
    if note_hidden(sealed, out.get("status")):
        out["note"] = ""
    return out


def project_wishes(rows) -> list:
    return [project_wish(dict(r)) for r in rows]
