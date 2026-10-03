"""封存策略：决定附言是否封存、何时隐藏、何时可改写。纯函数，无 IO。"""

EDITABLE_STATUSES = ("open", "released")


def is_sealed(value) -> bool:
    """归一化库内 0/1 与入参 bool：None/0/False → False，其余真值 → True。"""
    return bool(value)


def seal_flag(value: bool) -> int:
    """写库绑定值。"""
    return 1 if value else 0


def note_hidden(seal_note, status: str) -> bool:
    """唯一可见性判据：封存且未核销则隐藏。fulfilled 是唯一揭晓事实源。"""
    return is_sealed(seal_note) and status != "fulfilled"


def can_edit_note(status: str) -> dict:
    """认领即冻结：open/released 可改，claimed/fulfilled 拒绝。形状对齐 claim_allowed。"""
    if status in EDITABLE_STATUSES:
        return {"ok": True, "reason": ""}
    if status == "claimed":
        return {"ok": False, "reason": "note_locked_claimed"}
    if status == "fulfilled":
        return {"ok": False, "reason": "note_locked_fulfilled"}
    return {"ok": False, "reason": "bad_status"}
