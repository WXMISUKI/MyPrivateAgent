<template>
  <div class="datetime-card" :class="{ compact }">
    <div class="datetime-title">当前时间</div>
    <div class="datetime-time">{{ card.time }}</div>
    <div class="datetime-meta">
      <span class="datetime-date">{{ card.date }}</span>
      <span class="datetime-weekday">{{ card.weekday }}</span>
    </div>
  </div>
</template>

<script setup>
defineProps({
  card: {
    type: Object,
    required: true
  },
  compact: {
    type: Boolean,
    default: false
  }
})
</script>

<style scoped>
.datetime-card {
  margin-bottom: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(148, 163, 184, 0.24);
  background:
    linear-gradient(145deg, rgba(30, 41, 59, 0.92), rgba(15, 23, 42, 0.98)),
    radial-gradient(circle at top right, rgba(148, 163, 184, 0.2), transparent 40%);
  color: #f8fafc;
}

.datetime-card.compact {
  margin-bottom: 0;
  padding: var(--space-sm) var(--space-md);
}

.datetime-title {
  font-size: 0.8rem;
  color: #cbd5e1;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.datetime-time {
  margin-top: var(--space-xs);
  font-size: 1.5rem;
  font-weight: 700;
  font-family: var(--font-mono);
  color: #ffffff;
}

.datetime-meta {
  display: flex;
  gap: var(--space-sm);
  margin-top: var(--space-sm);
  font-size: 0.84rem;
  color: #cbd5e1;
}

.datetime-weekday {
  color: #93c5fd;
}
</style>
