<template>
  <div class="wall">
    <h1 class="serif">{{ w.title }}</h1>
    <p :class="{ badge: !noteVisible(w) }">{{ displayNote(w) }}</p>
    <p class="tag">状态 {{ w.status }} · 认领人 {{ w.claimer || '—' }}</p>
    <div v-if="noteEditable(w)">
      <button v-if="!editing" class="ghost" @click="startEdit">修改附言</button>
      <div v-else>
        <textarea v-model="draft" rows="4" placeholder="附言" />
        <div style="display:flex;gap:8px;flex-wrap:wrap">
          <button @click="saveNote">保存</button>
          <button class="ghost" @click="editing=false">取消</button>
        </div>
      </div>
    </div>
    <p v-if="err" class="err">{{ err }}</p>
    <input v-model="claimer" placeholder="你的名字" />
    <div style="display:flex;gap:8px;flex-wrap:wrap">
      <button @click="claim">认领锁定</button>
      <button class="ghost" @click="release">释放</button>
      <button class="ghost" @click="fulfill">核销完成</button>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
import { displayNote, noteEditable, noteVisible } from '../lib/visibility'
const props = defineProps({ id: String })
const w = ref({})
const claimer = ref('访客')
const err = ref('')
const editing = ref(false)
const draft = ref('')
const NOTE_ERRORS = {
  note_locked_claimed: '认领开始后附言已冻结',
  note_locked_fulfilled: '已核销，附言不可修改',
}
async function load() { w.value = await api('/wishes/' + props.id) }
function startEdit() { draft.value = w.value.note || ''; editing.value = true }
async function saveNote() {
  err.value = ''
  try {
    await api('/wishes/' + props.id, { method: 'PATCH', body: JSON.stringify({ note: draft.value }) })
    editing.value = false
    await load()
  } catch (e) { err.value = NOTE_ERRORS[e.message] || e.message }
}
async function claim() {
  err.value=''; try { await api('/wishes/'+props.id+'/claim',{method:'POST',body:JSON.stringify({claimer:claimer.value})}); await load() } catch(e){ err.value=e.message }
}
async function release() {
  err.value=''; try { await api('/wishes/'+props.id+'/release',{method:'POST',body:'{}'}); await load() } catch(e){ err.value=e.message }
}
async function fulfill() {
  err.value=''; try { await api('/wishes/'+props.id+'/fulfill',{method:'POST',body:'{}'}); await load() } catch(e){ err.value=e.message }
}
onMounted(load)
</script>
