<template>
  <div class="wall">
    <h1 class="serif">已完成</h1>
    <article v-for="w in rows" :key="w.id" class="card">
      <h3>{{ w.title }}</h3>
      <p>{{ w.claimer }}</p>
      <p>{{ w.note }}</p>
      <span v-if="w.note_sealed" class="badge">封存附言 · 已揭晓</span>
    </article>
  </div>
</template>
<script setup>
import { ref, onMounted } from 'vue'
import { api } from '../api'
const rows = ref([])
onMounted(async () => { rows.value = await api('/done') })
</script>
