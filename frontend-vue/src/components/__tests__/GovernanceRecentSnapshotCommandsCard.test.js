import { describe, expect, it } from 'vitest'
import { mount } from '@vue/test-utils'

import GovernanceRecentSnapshotCommandsCard from '../GovernanceRecentSnapshotCommandsCard.vue'

describe('GovernanceRecentSnapshotCommandsCard', () => {
  it('renders recent snapshot commands and emits copy action', async () => {
    const wrapper = mount(GovernanceRecentSnapshotCommandsCard, {
      props: {
        items: [{
          commandText: '/snapshot RUNT-BOOT-321',
          domain: 'runtime_control',
          snapshotId: 'RUNT-BOOT-321',
          eventLabel: 'Embedded Runtime Bootstrap 更新',
          summary: 'workspace_mode=memory_only · runtime=memory_preview',
          copiedAt: '2026-05-20T10:00:00Z',
        }],
      },
    })

    expect(wrapper.text()).toContain('最近治理快照命令')
    expect(wrapper.text()).toContain('/snapshot RUNT-BOOT-321')
    expect(wrapper.text()).toContain('事件: Embedded Runtime Bootstrap 更新')
    expect(wrapper.text()).toContain('workspace_mode=memory_only · runtime=memory_preview')

    await wrapper.find('button').trigger('click')
    expect(wrapper.emitted('copy-command')?.[0]).toEqual([expect.objectContaining({
      commandText: '/snapshot RUNT-BOOT-321',
      snapshotId: 'RUNT-BOOT-321',
    })])
  })

  it('renders copied feedback with event label and summary', () => {
    const wrapper = mount(GovernanceRecentSnapshotCommandsCard, {
      props: {
        items: [{
          commandText: '/snapshot RUNT-BOOT-321',
          domain: 'runtime_control',
          snapshotId: 'RUNT-BOOT-321',
          eventLabel: 'Embedded Runtime Bootstrap 更新',
          summary: 'workspace_mode=memory_only · runtime=memory_preview',
          copiedAt: '2026-05-20T10:00:00Z',
        }],
        copiedCommandText: '/snapshot RUNT-BOOT-321',
        copiedCommandDisplay: {
          eventLabel: 'Embedded Runtime Bootstrap 更新',
          summary: 'workspace_mode=memory_only · runtime=memory_preview',
        },
      },
    })

    expect(wrapper.text()).toContain('最近复制：')
    expect(wrapper.text()).toContain('Embedded Runtime Bootstrap 更新')
    expect(wrapper.text()).toContain('workspace_mode=memory_only · runtime=memory_preview')
  })
})
