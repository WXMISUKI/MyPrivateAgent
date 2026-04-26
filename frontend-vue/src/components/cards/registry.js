import DateTimeCard from './DateTimeCard.vue'
import SearchSummaryCard from './SearchSummaryCard.vue'
import WeatherCard from './WeatherCard.vue'

const CARD_REGISTRY = {
  'weather.v1': WeatherCard,
  'datetime.v1': DateTimeCard,
  'search_summary.v1': SearchSummaryCard
}

export function resolveStructuredCardComponent(cardSchema, card) {
  const schema = cardSchema || card?.schema || null
  if (!schema) {
    return null
  }
  return CARD_REGISTRY[schema] || null
}

export function hasStructuredCardSchema(cardSchema, card) {
  return !!resolveStructuredCardComponent(cardSchema, card)
}
