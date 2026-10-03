// 封存附言可见性 —— 后端 project_wish 的前端镜像，墙卡/详情/我的认领/已完成共用一份口径
export const SEALED_PLACEHOLDER = '封存附言 · 核销后揭晓'
export const REVEALED_BADGE = '封存附言 · 已揭晓'

export function noteVisible(w) {
  return !(w && w.note_sealed === true && w.status !== 'fulfilled')
}

export function displayNote(w) {
  return noteVisible(w) ? (w.note || '') : SEALED_PLACEHOLDER
}

export function noteEditable(w) {
  return ['open', 'released'].includes(w && w.status)
}
