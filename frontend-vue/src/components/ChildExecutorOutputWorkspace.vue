<template>
  <div class="child-output-workspace">
    <div class="summary-grid">
      <div class="summary-card">
        <span class="summary-label">Replay Records</span>
        <strong>{{ replay.recordCount || 0 }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Latest Result</span>
        <strong>{{ summary.latestResultType || '-' }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Latest Strategy</span>
        <strong>{{ summary.latestMergeStrategy || '-' }}</strong>
      </div>
      <div class="summary-card">
        <span class="summary-label">Artifacts</span>
        <strong>{{ summary.artifactIds.length }}</strong>
      </div>
    </div>
    <div class="provider-grid">
      <div class="provider-card">
        <div class="provider-title-row">
          <strong>Replay Read Model</strong>
          <span class="status-badge online">{{ replay.recordCount || 0 }}</span>
        </div>
        <ul>
          <li><code>record_count</code>: {{ replay.recordCount || 0 }}</li>
          <li v-if="!replay.records.length">暂无 child output replay records</li>
          <li v-for="record in replay.records" :key="record.bindingId || `${record.executorPath}-${record.mergeStatus}`">
            <code>{{ record.bindingId || '-' }}</code> · {{ record.executionStatus || '-' }} · {{ record.mergeStatus || '-' }}
          </li>
        </ul>
      </div>
      <div class="provider-card">
        <div class="provider-title-row">
          <strong>Artifact Summary</strong>
          <span class="status-badge online">{{ summary.recordCount || 0 }}</span>
        </div>
        <ul>
          <li><code>latest_artifact_id</code>: {{ summary.latestArtifactId || '-' }}</li>
          <li><code>latest_merge_strategy</code>: {{ summary.latestMergeStrategy || '-' }}</li>
          <li><code>latest_result_type</code>: {{ summary.latestResultType || '-' }}</li>
          <li><code>latest_conclusion</code>: {{ summary.latestConclusion || '-' }}</li>
          <li><code>latest_entities</code>: {{ summary.latestEntities.length ? summary.latestEntities.join('、') : '-' }}</li>
          <li><code>latest_merged_summary</code>: {{ summary.latestMergedSummary || '-' }}</li>
          <li><code>artifact_count</code>: {{ summary.artifactIds.length }}</li>
        </ul>
      </div>
      <div class="provider-card">
        <div class="provider-title-row">
          <strong>Latest Processing Semantics</strong>
          <span class="status-badge online">{{ summary.latestFocusPoints.length || 0 }}</span>
        </div>
        <ul>
          <li><code>focus_points</code>: {{ summary.latestFocusPoints.length ? summary.latestFocusPoints.join('；') : '-' }}</li>
          <li><code>action_items</code>: {{ summary.latestActionItems.length ? summary.latestActionItems.join('；') : '-' }}</li>
        </ul>
      </div>
      <div class="provider-card">
        <div class="provider-title-row">
          <strong>Latest Merge Semantics</strong>
          <span class="status-badge online">{{ mergedSemantics.intentLabel || '-' }}</span>
        </div>
        <ul>
          <li><code>intent_catalog_version</code>: {{ mergedSemantics.intentCatalogVersion || '-' }}</li>
          <li><code>supported_intents</code>: {{ mergedSemantics.supportedIntents.length ? mergedSemantics.supportedIntents.join('、') : '-' }}</li>
          <li><code>intent_label</code>: {{ mergedSemantics.intentLabel || '-' }}</li>
          <li><code>entities_mode</code>: {{ mergedSemantics.mergeBehavior.entities || '-' }}</li>
          <li><code>focus_points_mode</code>: {{ mergedSemantics.mergeBehavior.focusPoints || '-' }}</li>
          <li><code>action_items_mode</code>: {{ mergedSemantics.mergeBehavior.actionItems || '-' }}</li>
        </ul>
      </div>
      <div class="provider-card">
        <div class="provider-title-row">
          <strong>Parent Merge Sections</strong>
          <span class="status-badge online">{{ mergedSemantics.mergedSections.mergedEntities.items.length + mergedSemantics.mergedSections.mergedFocus.items.length + mergedSemantics.mergedSections.mergedActions.items.length }}</span>
        </div>
        <ul>
          <li><code>merged_entities</code>: {{ mergedSemantics.mergedSections.mergedEntities.items.length ? mergedSemantics.mergedSections.mergedEntities.items.join('、') : '-' }}</li>
          <li><code>merged_focus</code>: {{ mergedSemantics.mergedSections.mergedFocus.items.length ? mergedSemantics.mergedSections.mergedFocus.items.join('；') : '-' }}</li>
          <li><code>merged_actions</code>: {{ mergedSemantics.mergedSections.mergedActions.items.length ? mergedSemantics.mergedSections.mergedActions.items.join('；') : '-' }}</li>
          <li><code>latest_conclusion</code>: {{ mergedSemantics.mergedSections.latestConclusion.text || '-' }}</li>
        </ul>
      </div>
      <div class="provider-card">
        <div class="provider-title-row">
          <strong>Latest Merge Output</strong>
          <span class="status-badge online">{{ summary.latestMergedOutput ? 'ready' : 'empty' }}</span>
        </div>
        <p class="provider-endpoint">{{ summary.latestMergedOutput || '暂无 merged output' }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  replay: {
    type: Object,
    required: true
  },
  summary: {
    type: Object,
    required: true
  },
  mergedSemantics: {
    type: Object,
    required: true
  }
})
</script>

<style scoped>
.summary-grid,
.provider-grid {
  display: grid;
  gap: 1rem;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  margin-bottom: 1rem;
}

.summary-card,
.provider-card {
  border: 1px solid var(--border-color);
  background: var(--bg-surface);
  border-radius: var(--radius-lg);
}

.summary-card {
  padding: 1rem;
  display: flex;
  flex-direction: column;
  gap: 0.25rem;
}

.summary-label {
  font-size: 0.78rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: var(--text-tertiary);
}

.provider-card {
  padding: 1rem;
}

.provider-title-row {
  display: flex;
  justify-content: space-between;
  gap: 0.75rem;
  align-items: center;
  margin-bottom: 0.5rem;
}

.status-badge {
  padding: 0.2rem 0.55rem;
  border-radius: 999px;
  font-size: 0.75rem;
  background: rgba(148, 163, 184, 0.16);
  color: var(--text-secondary);
}

.status-badge.online {
  background: rgba(34, 197, 94, 0.14);
  color: #15803d;
}

.provider-card ul {
  margin: 0;
  padding-left: 1rem;
  color: var(--text-secondary);
}

.provider-card li + li {
  margin-top: 0.4rem;
}

.provider-endpoint {
  margin: 0;
  color: var(--text-secondary);
  line-height: 1.6;
}
</style>
