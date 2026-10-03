"""惊喜附言封存揭晓：封存策略 / 可见性投影 / 揭晓写库。"""

from app.modules.seal_note.policy import (
    EDITABLE_STATUSES,
    can_edit_note,
    is_sealed,
    note_hidden,
    seal_flag,
)
from app.modules.seal_note.projection import project_wish, project_wishes
from app.modules.seal_note.reveal import edit_note, fulfill_reveal

__all__ = [
    "EDITABLE_STATUSES",
    "can_edit_note",
    "is_sealed",
    "note_hidden",
    "seal_flag",
    "project_wish",
    "project_wishes",
    "edit_note",
    "fulfill_reveal",
]
