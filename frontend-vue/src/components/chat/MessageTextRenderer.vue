<template>
  <div v-if="hasContent" class="message-markdown" v-html="renderedHtml"></div>
</template>

<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { hasStructuredCardSchema } from '../cards/registry'

const props = defineProps({
  content: {
    type: [String, Number, Array],
    default: ''
  },
  renderMode: {
    type: String,
    default: 'markdown'
  },
  cardData: {
    type: [Object, Array, null],
    default: null
  },
  cardSchema: {
    type: [String, Object, null],
    default: null
  },
  forcePlainText: {
    type: Boolean,
    default: false
  }
})

const renderedHtml = ref('')

let markdownParser = null
let markdownLoadPromise = null

function normalizeContent(content) {
  if (Array.isArray(content)) {
    return content.join('')
  }
  if (content === null || content === undefined) {
    return ''
  }
  return String(content)
}

function hasStructuredCard(cardData, cardSchema) {
  return !!cardData && hasStructuredCardSchema(cardSchema, cardData)
}

function escapeHtml(content) {
  return String(content || '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;')
}

function plainText(content) {
  return escapeHtml(content).replace(/\n/g, '<br>')
}

function hasContentToRender(text, renderMode, cardData, cardSchema, forcePlainText) {
  if (!text.trim()) return false
  if (!forcePlainText && renderMode === 'structured_card' && hasStructuredCard(cardData, cardSchema)) {
    return false
  }
  return true
}

async function ensureMarked() {
  if (markdownParser) {
    return markdownParser
  }
  if (!markdownLoadPromise) {
    markdownLoadPromise = import('marked').then((mod) => {
      const parser = mod.marked || mod.default?.marked || mod.default
      if (parser && typeof parser.setOptions === 'function') {
        parser.setOptions({
          breaks: true
        })
      }
      return parser
    }).catch((error) => {
      markdownLoadPromise = null
      console.error('[MessageTextRenderer] Failed to load marked:', error)
      return null
    })
  }
  markdownParser = await markdownLoadPromise
  return markdownParser
}

const rawText = computed(() => normalizeContent(props.content))

const hasContent = computed(() => {
  if (!rawText.value) {
    return false
  }
  return hasContentToRender(
    rawText.value,
    props.forcePlainText ? 'markdown' : props.renderMode,
    props.cardData,
    props.cardSchema,
    props.forcePlainText
  )
})

async function render() {
  const text = rawText.value
  if (!hasContent.value) {
    renderedHtml.value = ''
    return
  }

  if (props.forcePlainText || props.renderMode === 'plain_text') {
    renderedHtml.value = plainText(text)
    return
  }

  const parser = await ensureMarked()
  if (!parser || typeof parser.parse !== 'function') {
    renderedHtml.value = plainText(text)
    return
  }
  renderedHtml.value = parser.parse(text)
}

watch(() => [rawText.value, props.renderMode, props.cardData, props.cardSchema, props.forcePlainText], async () => {
  await render()
}, { immediate: true })

onMounted(async () => {
  await render()
})
</script>

<style scoped>
.message-markdown :deep(pre) {
  background: var(--bg-elevated);
  padding: var(--space-md);
  border-radius: var(--radius-md);
  overflow-x: auto;
  margin: var(--space-sm) 0;
}

.message-markdown :deep(code) {
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 0.9em;
}

.message-markdown :deep(p:not(:last-child)) {
  margin-bottom: var(--space-sm);
}

.message-markdown :deep(ul),
.message-markdown :deep(ol) {
  margin: var(--space-sm) 0;
  padding-left: var(--space-lg);
}

.message-markdown :deep(a) {
  color: var(--primary);
}
</style>
