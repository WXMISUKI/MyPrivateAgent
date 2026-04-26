import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import AgentStructuredCard from '../AgentStructuredCard.vue'

describe('AgentStructuredCard', () => {
  it('resolves and renders weather card by schema', () => {
    const wrapper = mount(AgentStructuredCard, {
      props: {
        cardSchema: 'weather.v1',
        card: {
          city: 'Shanghai',
          current: {
            weather: '晴',
            temperature: '26C',
            wind_speed: '3级',
            wind_direction: '东南风'
          }
        }
      }
    })

    expect(wrapper.find('.weather-card').exists()).toBe(true)
    expect(wrapper.text()).toContain('Shanghai')
    expect(wrapper.text()).toContain('26C')
  })
})
