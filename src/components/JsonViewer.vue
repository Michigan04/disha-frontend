<script setup>
import { computed } from 'vue'

const props = defineProps({ data: { type: [Object, Array], required: true } })

const esc = (s) => s.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')

// Light syntax colouring for keys, strings, numbers and booleans.
const html = computed(() =>
  esc(JSON.stringify(props.data, null, 2)).replace(
    /("(?:\\.|[^"\\])*")(\s*:)?|\b(true|false|null)\b|-?\b\d+(?:\.\d+)?\b/g,
    (m, str, colon, lit) => {
      if (str) return colon ? `<span class="k">${str}</span>${colon}` : `<span class="s">${str}</span>`
      if (lit) return `<span class="b">${m}</span>`
      return `<span class="n">${m}</span>`
    },
  ),
)
</script>

<template>
  <pre class="json"><code v-html="html"></code></pre>
</template>

<style scoped>
.json {
  margin: 0;
  padding: 14px 16px;
  border-radius: var(--r-s);
  background: #141a32;
  color: #e7e9f5;
  font: 13px/1.55 ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  overflow-x: auto;
  white-space: pre-wrap;
  overflow-wrap: anywhere;
}

.json :deep(.k) {
  color: #a8b0ff;
}
.json :deep(.s) {
  color: #b8e6c8;
}
.json :deep(.n) {
  color: #ffd29a;
}
.json :deep(.b) {
  color: #ffb1a8;
}
</style>
