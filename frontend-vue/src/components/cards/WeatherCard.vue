<template>
  <div class="weather-card" :class="{ compact }">
    <div class="weather-card-header">
      <div>
        <div class="weather-city">{{ card.city }}</div>
        <div class="weather-current">{{ card.current?.weather }}</div>
      </div>
      <div class="weather-temp">{{ card.current?.temperature }}</div>
    </div>

    <div class="weather-meta">
      <span>风速 {{ card.current?.wind_speed }}</span>
      <span>风向 {{ card.current?.wind_direction }}</span>
    </div>

    <div v-if="card.forecast?.length" class="weather-forecast">
      <div
        v-for="(day, index) in card.forecast"
        :key="`${card.city}-${day.date}-${index}`"
        class="forecast-item"
      >
        <div class="forecast-date">{{ day.date }}</div>
        <div class="forecast-weather">{{ day.weather }}</div>
        <div class="forecast-temp">{{ day.min_temp }} / {{ day.max_temp }}</div>
        <div v-if="!compact" class="forecast-precip">{{ day.precipitation }}</div>
      </div>
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
.weather-card {
  margin-bottom: var(--space-sm);
  padding: var(--space-md);
  border-radius: var(--radius-lg);
  border: 1px solid rgba(14, 116, 144, 0.18);
  background:
    linear-gradient(135deg, rgba(224, 242, 254, 0.92), rgba(240, 249, 255, 0.98)),
    radial-gradient(circle at top right, rgba(125, 211, 252, 0.35), transparent 45%);
  color: #0f172a;
}

.weather-card.compact {
  margin-bottom: 0;
  padding: var(--space-sm) var(--space-md);
}

.weather-card-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.weather-city {
  font-size: 1rem;
  font-weight: 700;
  color: #0c4a6e;
}

.weather-current {
  font-size: 0.9rem;
  color: #155e75;
  margin-top: 2px;
}

.weather-temp {
  font-size: 1.4rem;
  font-weight: 700;
  color: #0f172a;
  white-space: nowrap;
}

.weather-meta {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-md);
  margin-top: var(--space-sm);
  font-size: 0.82rem;
  color: #164e63;
}

.weather-forecast {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(118px, 1fr));
  gap: var(--space-sm);
  margin-top: var(--space-md);
}

.forecast-item {
  padding: var(--space-sm);
  border-radius: var(--radius-md);
  background: rgba(255, 255, 255, 0.72);
  border: 1px solid rgba(14, 116, 144, 0.12);
}

.forecast-date {
  font-size: 0.78rem;
  color: #0c4a6e;
  font-weight: 600;
}

.forecast-weather {
  margin-top: 4px;
  font-size: 0.84rem;
  color: #155e75;
}

.forecast-temp {
  margin-top: 6px;
  font-size: 0.8rem;
  color: #0f172a;
}

.forecast-precip {
  margin-top: 4px;
  font-size: 0.76rem;
  color: #475569;
}
</style>
