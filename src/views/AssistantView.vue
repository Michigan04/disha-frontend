<script setup>
import { computed, nextTick, onMounted, reactive, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useStudentStore } from '../stores/student'
import { ask, buildContext, RESPONSE_SCHEMA, usingLiveModel } from '../services/chat'
import JsonViewer from '../components/JsonViewer.vue'
import Icon from '../components/Icon.vue'

const store = useStudentStore()
const route = useRoute()

const messages = reactive([])
const draft = ref('')
const busy = ref(false)
const thread = ref(null)
const context = computed(() => buildContext(store))
const showContext = ref(false)

const starters = [
  'What is my CGPA?',
  'Will I pass my courses this term?',
  'Am I eligible for my next OPPE?',
  'How many terms do I have left?',
  'What should I do about my failed course?',
  'When is my next live session?',
  'What do I need to reach a CGPA of 8?',
]

const CONFIDENCE = { high: 'High confidence', medium: 'Medium confidence', low: 'Low confidence' }

async function scrollDown() {
  await nextTick()
  thread.value?.lastElementChild?.scrollIntoView({ behavior: 'smooth', block: 'end' })
}

async function send(text) {
  const q = (text ?? draft.value).trim()
  if (!q || busy.value) return
  draft.value = ''
  const history = messages.map((m) => ({ role: m.role, content: m.role === 'user' ? m.text : JSON.stringify(m.data ?? { error: m.error }) }))
  messages.push({ role: 'user', text: q })
  busy.value = true
  scrollDown()
  try {
    const data = await ask(q, history, store)
    messages.push({ role: 'assistant', data, showJson: false, requested: false })
  } catch (err) {
    messages.push({ role: 'assistant', error: err.message })
  } finally {
    busy.value = false
    scrollDown()
  }
}

function onKey(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault()
    send()
  }
}

onMounted(() => {
  if (route.query.q) send(String(route.query.q))
})
</script>

<template>
  <div class="page ask-page">
    <header class="page-head">
      <h1>Ask Disha</h1>
      <p>Questions about your CGPA, terms, OPPEs, failed courses or sessions. Disha answers from your own record and the program rules, and tells you when a person should help instead.</p>
    </header>

    <div class="layout">
      <section class="chat" aria-label="Conversation">
        <div ref="thread" class="thread" aria-live="polite">
          <div v-if="!messages.length" class="start">
            <p class="muted">Try one of these:</p>
            <div class="starters">
              <button v-for="s in starters" :key="s" type="button" @click="send(s)">{{ s }}</button>
            </div>
          </div>

          <template v-for="(m, i) in messages" :key="i">
            <div v-if="m.role === 'user'" class="msg user"><p>{{ m.text }}</p></div>

            <div v-else-if="m.error" class="msg bot error">
              <p><Icon name="alert" :size="18" /> {{ m.error }}</p>
            </div>

            <div v-else class="msg bot">
              <p class="answer">{{ m.data.answer }}</p>
              <ul v-if="m.data.key_points.length" class="points">
                <li v-for="p in m.data.key_points" :key="p">{{ p }}</li>
              </ul>
              <div v-if="m.data.actions.length" class="actions">
                <RouterLink v-for="a in m.data.actions" :key="a.route" class="btn quiet" :to="a.route">{{ a.label }}</RouterLink>
              </div>

              <div v-if="m.data.escalate_to_human" class="human">
                <Icon name="person" :size="18" />
                <div>
                  <strong>A person can help with this</strong>
                  <p v-if="!m.requested">Ask the support team to contact you about this question.</p>
                  <p v-else>Request sent. The support team will reply by email within two working days.</p>
                </div>
                <button v-if="!m.requested" type="button" class="btn" @click="m.requested = true">Ask support to contact me</button>
              </div>

              <div class="meta">
                <span class="chip" :class="{ ok: m.data.confidence === 'high', low: m.data.confidence === 'low', route: m.data.confidence === 'medium' }">{{ CONFIDENCE[m.data.confidence] }}</span>
                <span v-if="m.data.sources.length" class="muted src">From {{ m.data.sources.map((s) => s.title).join(', ') }}</span>
                <button type="button" class="json-toggle" :aria-expanded="m.showJson" @click="m.showJson = !m.showJson">
                  <Icon name="code" :size="16" /> {{ m.showJson ? 'Hide JSON' : 'View JSON' }}
                </button>
              </div>
              <JsonViewer v-if="m.showJson" :data="m.data" />

              <div v-if="m.data.follow_up_questions.length && i === messages.length - 1" class="follow">
                <button v-for="f in m.data.follow_up_questions" :key="f" type="button" @click="send(f)">{{ f }}</button>
              </div>
            </div>
          </template>

          <div v-if="busy" class="msg bot typing"><span></span><span></span><span></span><span class="sr-only">Disha is answering</span></div>
        </div>

        <form class="composer" @submit.prevent="send()">
          <label for="q" class="sr-only">Your question</label>
          <textarea id="q" v-model="draft" rows="1" placeholder="Ask about your degree" @keydown="onKey"></textarea>
          <button class="btn send" type="submit" :disabled="!draft.trim() || busy">
            <Icon name="send" :size="18" /><span class="sr-only">Send</span>
          </button>
        </form>
        <p class="note">Disha can be wrong. Check important dates on the official portal.</p>
      </section>

      <aside class="side">
        <section class="panel">
          <h2>What Disha knows about you</h2>
          <ul class="known">
            <li><span class="muted">Level and term</span>{{ context.student.level }}, {{ context.student.current_term }}</li>
            <li><span class="muted">CGPA</span>{{ context.student.cgpa?.toFixed(2) ?? "None yet" }}</li>
            <li><span class="muted">Risk level</span>{{ context.student.risk_level }}</li>
            <li><span class="muted">This term</span>{{ context.student.this_term.map((c) => c.course).join(', ') }}</li>
            <li><span class="muted">OPPEs</span>{{ context.student.oppe.length }} this term</li>
            <li><span class="muted">Next milestone</span>{{ context.student.next_milestone }}</li>
          </ul>
          <button type="button" class="json-toggle" :aria-expanded="showContext" @click="showContext = !showContext">
            <Icon name="code" :size="16" /> {{ showContext ? 'Hide' : 'View' }} the context sent with each question
          </button>
          <JsonViewer v-if="showContext" :data="context" class="ctx" />
        </section>

        <section class="panel">
          <h2>Structured answers</h2>
          <p class="muted small">Every reply is a JSON object, so the app can turn it into buttons and links and check it before showing it. Fields:</p>
          <ul class="fields">
            <li v-for="(v, k) in RESPONSE_SCHEMA.properties" :key="k"><code>{{ k }}</code></li>
          </ul>
          <p class="muted small">{{ usingLiveModel ? 'Answers come from the language model on your server.' : 'Demo mode: answers come from a built-in responder that uses the same format.' }}</p>
        </section>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.layout {
  display: grid;
  grid-template-columns: minmax(0, 1.7fr) minmax(0, 1fr);
  gap: 20px;
  align-items: start;
}

.chat {
  min-width: 0;
  display: flex;
  flex-direction: column;
  background: var(--surface);
  border: 1px solid var(--line);
  border-radius: var(--r-l);
  padding: 20px;
  min-height: 520px;
}

.thread {
  min-width: 0;
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 14px;
  padding-bottom: 12px;
}

.start .muted {
  margin-bottom: 10px;
}

.starters {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.starters button,
.follow button {
  border: 1px solid var(--line-2);
  background: var(--surface);
  border-radius: 999px;
  padding: 7px 14px;
  cursor: pointer;
  color: var(--ink-2);
}

.starters button:hover,
.follow button:hover {
  border-color: var(--route);
  color: var(--route-ink);
}

.msg {
  max-width: 88%;
  min-width: 0;
}

.msg.user {
  align-self: flex-end;
  background: var(--route);
  color: #fff;
  padding: 10px 16px;
  border-radius: 18px 18px 4px 18px;
}

.msg.bot {
  align-self: flex-start;
  background: var(--paper);
  padding: 14px 18px;
  border-radius: 18px 18px 18px 4px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.msg.error p {
  display: flex;
  gap: 8px;
  color: var(--high);
}

.answer {
  font-size: 1.0625rem;
}

.points {
  margin: 0;
  padding-left: 20px;
  color: var(--ink-2);
}

.points li + li {
  margin-top: 4px;
}

.actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.actions .btn {
  background: var(--surface);
}

.human {
  display: grid;
  grid-template-columns: auto 1fr auto;
  gap: 10px;
  align-items: center;
  background: var(--surface);
  border-radius: var(--r-m);
  padding: 12px 14px;
}

.human svg {
  color: var(--route);
}

.human p {
  font-size: 0.9375rem;
  color: var(--ink-2);
}

.meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px 12px;
  font-size: 0.875rem;
}

.src {
  flex: 1;
  min-width: 12ch;
}

.json-toggle {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  border: 0;
  background: none;
  color: var(--route-ink);
  font-weight: 500;
  font-size: 0.875rem;
  cursor: pointer;
  padding: 2px 0;
}

.json-toggle:hover {
  text-decoration: underline;
}

.follow {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 2px;
}

.typing {
  flex-direction: row !important;
  gap: 5px !important;
  padding: 14px 18px;
}

.typing span:not(.sr-only) {
  width: 7px;
  height: 7px;
  border-radius: 50%;
  background: var(--muted);
  animation: blink 1.2s infinite ease-in-out;
}

.typing span:nth-child(2) {
  animation-delay: 0.15s;
}

.typing span:nth-child(3) {
  animation-delay: 0.3s;
}

@keyframes blink {
  0%, 80%, 100% { opacity: 0.25; }
  40% { opacity: 1; }
}

.composer {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  border: 1px solid var(--line-2);
  border-radius: var(--r-m);
  padding: 8px 8px 8px 14px;
  background: var(--surface);
}

.composer:focus-within {
  border-color: var(--route);
  box-shadow: 0 0 0 3px var(--route-soft);
}

.composer textarea {
  flex: 1;
  border: 0;
  resize: none;
  outline: none;
  padding: 6px 0;
  min-height: 24px;
  max-height: 140px;
  background: transparent;
}

.send {
  padding: 9px 12px;
}

.side {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.known {
  list-style: none;
  margin: 12px 0 12px;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.known li {
  display: flex;
  flex-direction: column;
  line-height: 1.35;
}

.known .muted {
  font-size: 0.8125rem;
}

.ctx {
  margin-top: 10px;
  max-height: 320px;
  overflow: auto;
}

.small {
  font-size: 0.9375rem;
  margin-top: 6px;
}

.fields {
  list-style: none;
  margin: 10px 0;
  padding: 0;
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.fields code {
  font: 13px ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
  background: var(--paper);
  border-radius: 6px;
  padding: 2px 8px;
}

@media (max-width: 1000px) {
  .layout {
    grid-template-columns: 1fr;
  }
  .msg {
    max-width: 100%;
  }
  .human {
    grid-template-columns: auto 1fr;
  }
  .human .btn {
    grid-column: 1 / -1;
    justify-self: start;
  }
}
</style>
