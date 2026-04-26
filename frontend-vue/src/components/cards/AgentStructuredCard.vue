<template>
  <component
    :is="resolvedComponent"
    v-if="resolvedComponent"
    :card="card"
    :compact="compact"
  />
</template>

<script setup>
import { computed } from 'vue'
import { resolveStructuredCardComponent } from './registry'

const props = defineProps({
  card: {
    type: Object,
    default: null
  },
  cardSchema: {
    type: String,
    default: ''
  },
  compact: {
    type: Boolean,
    default: false
  }
})

const resolvedComponent = computed(() => resolveStructuredCardComponent(props.cardSchema, props.card))
</script>
