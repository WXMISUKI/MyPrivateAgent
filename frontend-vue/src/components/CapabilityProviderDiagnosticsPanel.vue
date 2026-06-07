<template>
  <section class="settings-section">
    <div class="section-header">
      <div>
        <h2>能力 Provider 测试</h2>
        <p class="section-desc">查看统一能力注册、外部服务心跳，并执行短链路能力测试。</p>
      </div>
      <button class="action-btn" type="button" @click="loadDiagnostics" :disabled="loading">
        {{ loading ? '刷新中...' : '刷新' }}
      </button>
    </div>

    <div v-if="loadError" class="test-result error">{{ loadError }}</div>

    <div class="heartbeat-list">
      <div v-for="provider in heartbeatProviders" :key="provider.provider_id + provider.base_url" class="provider-card compact">
        <div class="provider-header">
          <span class="provider-name">{{ provider.provider_id || 'local' }}</span>
          <span class="provider-badge" :class="statusClass(provider.status)">{{ provider.status || 'unknown' }}</span>
          <span class="source-tag">{{ provider.base_url || 'local' }}</span>
        </div>
        <div v-if="provider.circuit_breaker" class="breaker-meta">
          <span class="source-tag">circuit: {{ provider.circuit_breaker.state || 'unknown' }}</span>
          <span class="field-hint">failures: {{ provider.circuit_breaker.failure_count ?? 0 }}</span>
          <span v-if="provider.circuit_breaker.retry_after_seconds !== undefined" class="field-hint">
            retry in {{ formatRetryAfter(provider.circuit_breaker.retry_after_seconds) }}s
          </span>
        </div>
        <div v-if="provider.reason" class="field-hint">{{ provider.reason }}</div>
      </div>
    </div>

    <div v-if="loading" class="loading-hint">加载中...</div>

    <div class="provider-card">
      <div class="provider-header">
        <span class="provider-name">文档 Ingestion 测试</span>
        <span class="source-tag">upload -> parse -> artifact</span>
      </div>
      <div class="capability-meta">
        <span>通过统一能力运行时调用 OCR/Layout/VLM，并将成功结果持久化为 Artifact。</span>
      </div>
      <div class="field-row">
        <label>文档文件（图片/PDF）</label>
        <input class="field-input" data-test="document-ingest-file" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="handleIngestionFile" />
        <label>解析模式（parse_mode）</label>
        <select class="field-input" data-test="document-ingest-mode" v-model="ingestionParseMode">
          <option value="ocr">ocr</option>
          <option value="layout">layout</option>
          <option value="vlm_async">vlm_async</option>
        </select>
        <template v-if="ingestionParseMode === 'layout'">
          <label>输出格式（output_format）</label>
          <select class="field-input" v-model="ingestionLayoutOutputFormat">
            <option value="markdown">markdown</option>
            <option value="json">json</option>
          </select>
          <label class="inline-check">
            <input type="checkbox" v-model="ingestionLayoutIncludeTables" />
            包含表格（include_tables）
          </label>
          <label class="inline-check">
            <input type="checkbox" v-model="ingestionLayoutIncludeLayout" />
            包含版面（include_layout）
          </label>
        </template>
        <template v-if="ingestionParseMode === 'vlm_async'">
          <label>任务（task）</label>
          <select class="field-input" v-model="ingestionVlmTask">
            <option value="summarize">summarize</option>
            <option value="extract_fields">extract_fields</option>
            <option value="chart_understanding">chart_understanding</option>
            <option value="qa">qa</option>
          </select>
          <label>问题（question，可选）</label>
          <input class="field-input" type="text" v-model="ingestionVlmQuestion" placeholder="例如：请总结合同关键条款" />
        </template>
        <label>最大页数（max_pages，可选）</label>
        <input class="field-input" type="number" min="1" step="1" v-model="ingestionMaxPages" placeholder="例如 5" />
      </div>
      <div class="provider-actions">
        <button
          class="action-btn test-btn"
          data-test="document-ingest-submit"
          type="button"
          @click="submitDocumentIngestion"
          :disabled="ingestionSubmitting"
        >
          {{ ingestionSubmitting ? '提交中...' : '提交 Ingestion' }}
        </button>
      </div>
      <div
        v-if="ingestionResult"
        class="test-result"
        :class="ingestionResult.ok ? 'ok' : 'error'"
      >
        <template v-if="ingestionResult.ok">
          <div class="ocr-summary">
            <span>ingest_id: {{ ingestionResult.ingestion?.ingest_id || '(missing)' }}</span>
            <span>status: {{ ingestionResult.ingestion?.status || '(missing)' }}</span>
            <span>artifact_id: {{ ingestionResult.ingestion?.artifact_id || '(pending)' }}</span>
          </div>
          <div v-if="ingestionWarnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in ingestionWarnings"
              :key="'ingestion-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
        </template>
        <template v-else>
          <span>{{ ingestionErrorText }}</span>
        </template>
        <details class="ocr-section">
          <summary>Raw JSON</summary>
          <pre>{{ formatJson(ingestionResult) }}</pre>
        </details>
      </div>
    </div>

    <div class="provider-card">
      <div class="provider-header">
        <span class="provider-name">本地文档 RAG 操作入口</span>
        <span class="source-tag">readiness -> upload-to-use</span>
      </div>
      <div class="capability-meta">
        <span>组合本地 readiness 与真实文档 RAG 试跑，保持显式本地操作，不接入默认聊天。</span>
      </div>
      <div class="field-row">
        <label>上传文档文件</label>
        <input class="field-input" data-test="document-rag-file" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="handleDocumentRagFile" />
        <span v-if="documentRagFileName" class="field-hint">selected: {{ documentRagFileName }}</span>
        <label>本地文档路径</label>
        <input class="field-input" data-test="document-rag-path" type="text" v-model="documentRagPath" placeholder="例如 D:\xwechat_files\...\公司简介.pdf" />
        <label>解析模式（parse_mode）</label>
        <select class="field-input" data-test="document-rag-parse-mode" v-model="documentRagParseMode">
          <option value="ocr">ocr</option>
          <option value="layout">layout</option>
        </select>
        <label>Source ID</label>
        <input class="field-input" data-test="document-rag-source-id" type="text" v-model="documentRagSourceId" />
        <label>OCR Profile</label>
        <select class="field-input" data-test="document-rag-ocr-profile" v-model="documentRagOcrProfile">
          <option value="gpu">gpu</option>
          <option value="cpu">cpu</option>
          <option value="unknown">unknown</option>
        </select>
        <label>OCR Timeout Seconds</label>
        <input class="field-input" data-test="document-rag-ocr-timeout" type="number" min="1" step="1" v-model="documentRagOcrTimeoutSeconds" />
        <label>Provider Base URL</label>
        <input class="field-input" data-test="document-rag-provider-url" type="text" v-model="documentRagProviderBaseUrl" />
        <label>Knowledge Provider Repo</label>
        <input class="field-input" data-test="document-rag-provider-repo" type="text" v-model="documentRagProviderRepo" />
        <label>Provider Python</label>
        <input class="field-input" data-test="document-rag-provider-python" type="text" v-model="documentRagProviderPython" />
        <label>RAG 试问问题</label>
        <input class="field-input" data-test="document-rag-question" type="text" v-model="documentRagQuestion" placeholder="例如：公司主营业务和服务范围是什么？" />
        <label>Top K</label>
        <input class="field-input" data-test="document-rag-top-k" type="number" min="1" step="1" v-model="documentRagTopK" />
      </div>
      <div class="provider-actions">
        <button
          class="action-btn test-btn"
          data-test="document-rag-readiness"
          type="button"
          @click="runDocumentRagReadiness"
          :disabled="documentRagReadinessRunning"
        >
          {{ documentRagReadinessRunning ? '检查中...' : '检查 RAG Readiness' }}
        </button>
        <button
          class="action-btn test-btn"
          data-test="document-rag-run-trial"
          type="button"
          @click="runDocumentRagLocalTrial"
          :disabled="documentRagTrialRunning"
        >
          {{ documentRagTrialRunning ? '试跑中...' : '运行本地 RAG 试跑' }}
        </button>
        <button
          class="action-btn test-btn"
          data-test="document-rag-run-question"
          type="button"
          @click="runDocumentRagQuestionTrial"
          :disabled="documentRagQuestionRunning"
        >
          {{ documentRagQuestionRunning ? '试问中...' : '试问 RAG' }}
        </button>
      </div>
      <div
        v-if="documentRagResult"
        class="test-result"
        :class="documentRagResult.ok ? 'ok' : 'error'"
      >
        <div class="ocr-summary">
          <span>decision: {{ documentRagResult.decision || '(missing)' }}</span>
          <span>reason: {{ documentRagResult.reason_code || '(missing)' }}</span>
          <span>source_id: {{ documentRagResult.summary?.source_id || documentRagSourceId }}</span>
        </div>
        <div class="ocr-summary">
          <span>readiness: {{ documentRagResult.readiness?.decision || '(missing)' }}</span>
          <span>upload: {{ documentRagResult.upload_to_use?.decision || documentRagResult.upload_to_use?.status || '(not_run)' }}</span>
          <span v-if="documentRagMaterializedUploadPath">input: uploaded_file</span>
        </div>
        <div class="ocr-warning-list">
          <span v-if="documentRagSelectedFilename" class="field-hint">selected file: {{ documentRagSelectedFilename }}</span>
          <span v-if="documentRagMaterializedUploadPath" class="field-hint">materialized upload: {{ documentRagMaterializedUploadPath }}</span>
          <span v-if="documentRagReadinessReportPath" class="field-hint">readiness report: {{ documentRagReadinessReportPath }}</span>
          <span v-if="documentRagUploadReportPath" class="field-hint">upload report: {{ documentRagUploadReportPath }}</span>
          <span v-if="documentRagParserArtifactPath" class="field-hint">parser artifact: {{ documentRagParserArtifactPath }}</span>
        </div>
        <details class="ocr-section">
          <summary>Raw JSON</summary>
          <pre>{{ formatJson(documentRagResult) }}</pre>
        </details>
      </div>
      <div
        v-if="documentRagQuestionResult"
        class="test-result"
        :class="documentRagQuestionResult.ok ? 'ok' : 'error'"
      >
        <div class="ocr-summary">
          <span>question decision: {{ documentRagQuestionResult.decision || '(missing)' }}</span>
          <span>reason: {{ documentRagQuestionResult.reason_code || '(missing)' }}</span>
          <span>answer_status: {{ documentRagQuestionResult.answer_status || '(missing)' }}</span>
          <span>evidence: {{ documentRagQuestionResult.evidence_pack?.status || '(missing)' }}</span>
        </div>
        <div v-if="documentRagQuestionResult.answer" class="ocr-section">
          <strong>Answer</strong>
          <pre>{{ documentRagQuestionResult.answer }}</pre>
        </div>
        <div class="ocr-warning-list">
          <span
            v-for="citation in documentRagQuestionCitations"
            :key="'document-rag-question-citation-' + citation"
            class="field-hint"
          >
            citation: {{ citation }}
          </span>
          <span v-if="documentRagQuestionReportPath" class="field-hint">question report: {{ documentRagQuestionReportPath }}</span>
        </div>
        <details class="ocr-section">
          <summary>Raw JSON</summary>
          <pre>{{ formatJson(documentRagQuestionResult) }}</pre>
        </details>
      </div>
    </div>

    <div v-for="capability in capabilities" :key="capability.capability_id" class="provider-card">
      <div class="provider-header">
        <span class="provider-name">{{ capability.capability_id }}</span>
        <span class="provider-badge" :class="statusClass(capability.status)">{{ capability.status || 'unknown' }}</span>
        <span class="source-tag">{{ capability.kind }} / {{ capability.transport }}</span>
      </div>
      <div class="capability-meta">
        <span>Provider: {{ capability.provider }}</span>
        <span v-if="capability.reason">Reason: {{ capability.reason }}</span>
      </div>

      <div v-if="capability.kind === 'asr'" class="field-row">
        <label>ASR PCM 文件（可选）</label>
        <input class="field-input" type="file" accept=".pcm,.raw,application/octet-stream" @change="event => handleAsrFile(capability.capability_id, event)" />
        <span class="field-hint">仅支持 16kHz / mono / PCM s16le；不上传文件时只执行 health-only readiness 测试。</span>
      </div>

      <div v-if="capability.kind === 'ocr'" class="field-row">
        <label>OCR 文件（图片/PDF）</label>
        <input class="field-input" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="event => handleOcrFile(capability.capability_id, event)" />
        <label class="inline-check">
          <input type="checkbox" :checked="ocrVisualize[capability.capability_id] === true" @change="event => setOcrVisualize(capability.capability_id, event)" />
          返回可视化（visualize）
        </label>
        <span class="field-hint">建议先用小图测试。图片自动映射为 image/*，PDF 映射为 application/pdf。</span>
      </div>

      <div v-if="capability.kind === 'layout'" class="field-row">
        <label>Layout 文件（图片/PDF）</label>
        <input class="field-input" data-test="layout-file" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="event => handleLayoutFile(capability.capability_id, event)" />
        <label>输出格式（output_format）</label>
        <select class="field-input" data-test="layout-output-format" :value="layoutOutputFormat[capability.capability_id] || 'markdown'" @change="event => setLayoutOutputFormat(capability.capability_id, event)">
          <option value="markdown">markdown</option>
          <option value="json">json</option>
        </select>
        <label class="inline-check">
            <input data-test="layout-include-tables" type="checkbox" :checked="layoutIncludeTables[capability.capability_id] !== false" @change="event => setLayoutIncludeTables(capability.capability_id, event)" />
          包含表格（include_tables）
        </label>
        <label class="inline-check">
            <input data-test="layout-include-layout" type="checkbox" :checked="layoutIncludeLayout[capability.capability_id] !== false" @change="event => setLayoutIncludeLayout(capability.capability_id, event)" />
          包含版面（include_layout）
        </label>
        <label>最大页数（max_pages，可选）</label>
        <input class="field-input" data-test="layout-max-pages" type="number" min="1" step="1" :value="layoutMaxPages[capability.capability_id] || ''" @input="event => setLayoutMaxPages(capability.capability_id, event)" placeholder="例如 10" />
        <span class="field-hint">默认输出 markdown，参数会透传到 layout provider。</span>
      </div>
      <div v-if="capability.kind === 'vlm'" class="field-row">
        <label>VLM 文件（图片/PDF）</label>
        <input class="field-input" type="file" accept=".png,.jpg,.jpeg,.pdf,image/png,image/jpeg,application/pdf" @change="event => handleVlmFile(capability.capability_id, event)" />
        <label>任务（task）</label>
        <select class="field-input" :value="vlmTasks[capability.capability_id] || 'summarize'" @change="event => setVlmTask(capability.capability_id, event)">
          <option value="summarize">summarize</option>
          <option value="extract_fields">extract_fields</option>
          <option value="chart_understanding">chart_understanding</option>
          <option value="qa">qa</option>
        </select>
        <label>问题（question，可选）</label>
        <input class="field-input" type="text" :value="vlmQuestions[capability.capability_id] || ''" @input="event => setVlmQuestion(capability.capability_id, event)" placeholder="例如：请总结合同关键条款" />
        <label>最大页数（max_pages，可选）</label>
        <input class="field-input" type="number" min="1" step="1" :value="vlmMaxPages[capability.capability_id] || ''" @input="event => setVlmMaxPages(capability.capability_id, event)" placeholder="例如 5" />
        <template v-if="capability.capability_id === 'document.vlm.parse.async'">
          <label>任务 ID（job_id，用于查询）</label>
          <input class="field-input" type="text" :value="vlmJobIds[capability.capability_id] || ''" @input="event => setVlmJobId(capability.capability_id, event)" placeholder="例如 job_20260601_001" />
        </template>
      </div>

      <div class="provider-actions">
        <button
          class="action-btn test-btn"
          data-test="capability-test"
          type="button"
          @click="runCapabilityTest(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试能力' }}
        </button>
        <button
          v-if="capability.kind === 'ocr'"
          class="action-btn test-btn"
          data-test="ocr-invoke"
          type="button"
          @click="runOcrInvoke(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试 OCR' }}
        </button>
        <button
          v-if="capability.kind === 'layout'"
          class="action-btn test-btn"
          data-test="layout-invoke"
          type="button"
          @click="runLayoutInvoke(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试 Layout' }}
        </button>
        <button
          v-if="capability.kind === 'vlm' && capability.capability_id !== 'document.vlm.parse.async'"
          class="action-btn test-btn"
          data-test="vlm-invoke"
          type="button"
          @click="runVlmInvoke(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '测试 VLM' }}
        </button>
        <button
          v-if="capability.kind === 'vlm' && capability.capability_id === 'document.vlm.parse.async'"
          class="action-btn test-btn"
          data-test="vlm-async-submit"
          type="button"
          @click="runVlmAsyncSubmit(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '提交 VLM 任务' }}
        </button>
        <button
          v-if="capability.kind === 'vlm' && capability.capability_id === 'document.vlm.parse.async'"
          class="action-btn test-btn"
          data-test="vlm-async-status"
          type="button"
          @click="runVlmAsyncStatus(capability)"
          :disabled="testing[capability.capability_id]"
        >
          {{ testing[capability.capability_id] ? '测试中...' : '查询任务状态' }}
        </button>
      </div>

      <div
        v-if="testResults[capability.capability_id]"
        class="test-result"
        :class="testResults[capability.capability_id].ok ? 'ok' : 'error'"
      >
        <span>{{ testResults[capability.capability_id].ok ? '测试通过' : '测试失败' }}</span>
        <span v-if="testResults[capability.capability_id].latency_ms !== undefined">
          ({{ testResults[capability.capability_id].latency_ms }}ms)
        </span>
        <div v-if="canPersistDocumentArtifact(capability)" class="provider-actions">
          <button
            class="action-btn test-btn"
            type="button"
            @click="persistDocumentArtifact(capability)"
            :disabled="artifactSaving[capability.capability_id]"
          >
            {{ artifactSaving[capability.capability_id] ? '保存中...' : '保存 Artifact' }}
          </button>
          <span v-if="artifactStatusText(capability.capability_id)" class="field-hint">
            {{ artifactStatusText(capability.capability_id) }}
          </span>
        </div>
        <template v-if="capability.kind === 'ocr' && ocrResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>文本长度: {{ ocrResultView(testResults[capability.capability_id]).text.length }}</span>
            <span>页面数: {{ ocrResultView(testResults[capability.capability_id]).pages.length }}</span>
            <span>Blocks: {{ ocrResultView(testResults[capability.capability_id]).blocks.length }}</span>
          </div>
          <div v-if="ocrResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in ocrResultView(testResults[capability.capability_id]).warnings"
              :key="'ocr-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>文本结果</summary>
            <pre>{{ ocrResultView(testResults[capability.capability_id]).text || '(empty)' }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Blocks / 置信度</summary>
            <pre>{{ formatOcrBlocks(ocrResultView(testResults[capability.capability_id]).blocks) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Pages</summary>
            <pre>{{ formatJson(ocrResultView(testResults[capability.capability_id]).pages) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(ocrResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <template v-else-if="capability.kind === 'layout' && layoutResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>Markdown 长度: {{ layoutResultView(testResults[capability.capability_id]).markdown.length }}</span>
            <span>Elements: {{ layoutResultView(testResults[capability.capability_id]).elements.length }}</span>
            <span>Tables: {{ layoutResultView(testResults[capability.capability_id]).tables.length }}</span>
          </div>
          <div v-if="layoutResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in layoutResultView(testResults[capability.capability_id]).warnings"
              :key="'layout-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>Markdown</summary>
            <pre>{{ layoutResultView(testResults[capability.capability_id]).markdown || '(empty)' }}</pre>
          </details>
          <div class="provider-actions">
            <button class="action-btn test-btn" type="button" @click="copyLayoutMarkdown(layoutResultView(testResults[capability.capability_id]).markdown)">
              复制 Markdown
            </button>
            <button class="action-btn test-btn" type="button" @click="downloadLayoutResult(capability.capability_id, layoutResultView(testResults[capability.capability_id]))">
              导出 JSON
            </button>
          </div>
          <details class="ocr-section">
            <summary>Elements</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).elements) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Tables</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).tables) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Pages</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).pages) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(layoutResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <template v-else-if="capability.capability_id === 'document.vlm.parse.async' && vlmAsyncResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>Job: {{ vlmAsyncResultView(testResults[capability.capability_id]).job_id || '(missing)' }}</span>
            <span>Status: {{ vlmAsyncResultView(testResults[capability.capability_id]).status }}</span>
            <span>Progress: {{ vlmAsyncResultView(testResults[capability.capability_id]).progress }}</span>
          </div>
          <div v-if="vlmAsyncResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in vlmAsyncResultView(testResults[capability.capability_id]).warnings"
              :key="'vlm-async-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>Async Result</summary>
            <pre>{{ formatJson(vlmAsyncResultView(testResults[capability.capability_id]).result) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Async Error</summary>
            <pre>{{ formatJson(vlmAsyncResultView(testResults[capability.capability_id]).error) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(vlmAsyncResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <template v-else-if="capability.kind === 'vlm' && vlmResultView(testResults[capability.capability_id])">
          <div class="ocr-summary">
            <span>Summary 长度: {{ vlmResultView(testResults[capability.capability_id]).summary.length }}</span>
            <span>Sections: {{ vlmResultView(testResults[capability.capability_id]).sections.length }}</span>
            <span>Evidence: {{ vlmResultView(testResults[capability.capability_id]).evidence.length }}</span>
          </div>
          <div v-if="vlmResultView(testResults[capability.capability_id]).warnings.length" class="ocr-warning-list">
            <span
              v-for="(warning, idx) in vlmResultView(testResults[capability.capability_id]).warnings"
              :key="'vlm-warning-' + idx"
              class="field-hint"
            >
              warning: {{ warning }}
            </span>
          </div>
          <details class="ocr-section" open>
            <summary>Summary</summary>
            <pre>{{ vlmResultView(testResults[capability.capability_id]).summary || '(empty)' }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Sections</summary>
            <pre>{{ formatJson(vlmResultView(testResults[capability.capability_id]).sections) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Answers</summary>
            <pre>{{ formatJson(vlmResultView(testResults[capability.capability_id]).answers) }}</pre>
          </details>
          <details class="ocr-section">
            <summary>Raw JSON</summary>
            <pre>{{ formatJson(vlmResultView(testResults[capability.capability_id]).raw) }}</pre>
          </details>
        </template>
        <pre v-else>{{ formatResult(testResults[capability.capability_id]) }}</pre>
        <audio v-if="audioUrls[capability.capability_id]" :src="audioUrls[capability.capability_id]" controls />
      </div>
    </div>
  </section>
</template>

<script setup>
import { computed, onBeforeUnmount, onMounted, reactive, ref } from 'vue'
import { capabilityApi, documentArtifactApi, documentIngestionApi, documentRagLocalTrialApi } from '../api'

const capabilities = ref([])
const heartbeat = ref(null)
const loading = ref(false)
const loadError = ref('')
const testing = reactive({})
const testResults = reactive({})
const artifactSaving = reactive({})
const artifactResults = reactive({})
const audioUrls = reactive({})
const asrFiles = reactive({})
const ocrFiles = reactive({})
const ocrVisualize = reactive({})
const layoutFiles = reactive({})
const layoutIncludeTables = reactive({})
const layoutIncludeLayout = reactive({})
const layoutOutputFormat = reactive({})
const layoutMaxPages = reactive({})
const vlmFiles = reactive({})
const vlmTasks = reactive({})
const vlmQuestions = reactive({})
const vlmMaxPages = reactive({})
const vlmJobIds = reactive({})
const ingestionFile = ref(null)
const ingestionParseMode = ref('layout')
const ingestionLayoutOutputFormat = ref('markdown')
const ingestionLayoutIncludeTables = ref(true)
const ingestionLayoutIncludeLayout = ref(true)
const ingestionVlmTask = ref('summarize')
const ingestionVlmQuestion = ref('')
const ingestionMaxPages = ref('')
const ingestionSubmitting = ref(false)
const ingestionResult = ref(null)
const documentRagPath = ref('')
const documentRagParseMode = ref('ocr')
const documentRagSourceId = ref('company_profile_2025_trial')
const documentRagOcrProfile = ref('gpu')
const documentRagOcrTimeoutSeconds = ref('180')
const documentRagProviderBaseUrl = ref('http://127.0.0.1:8020')
const documentRagProviderRepo = ref('D:\\AI\\AIcode\\unifiedKnowledgeRAG')
const documentRagProviderPython = ref('conda run -n GRAPHRAG python')
const documentRagQuestion = ref('公司主营业务和服务范围是什么？')
const documentRagTopK = ref('3')
const documentRagReadinessRunning = ref(false)
const documentRagTrialRunning = ref(false)
const documentRagQuestionRunning = ref(false)
const documentRagResult = ref(null)
const documentRagQuestionResult = ref(null)
const documentRagFile = ref(null)

const heartbeatProviders = computed(() => heartbeat.value?.providers || [])
const ingestionWarnings = computed(() => {
  const warnings = ingestionResult.value?.ingestion?.warnings
  return Array.isArray(warnings) ? warnings.map(item => String(item)) : []
})
const ingestionErrorText = computed(() => {
  const error = ingestionResult.value?.error || {}
  return `${error.code || 'DOCUMENT_INGEST_FAILED'}: ${error.message || '提交失败'}`
})
const documentRagReadinessReportPath = computed(() => {
  return documentRagResult.value?.readiness?.markdown_path || documentRagResult.value?.readiness?.json_path || ''
})
const documentRagUploadReportPath = computed(() => {
  return documentRagResult.value?.upload_to_use?.markdown_path || documentRagResult.value?.upload_to_use?.json_path || ''
})
const documentRagParserArtifactPath = computed(() => {
  return documentRagResult.value?.upload_to_use?.parser_artifact_path || ''
})
const documentRagMaterializedUploadPath = computed(() => {
  return documentRagResult.value?.summary?.upload_materialization?.document_path || ''
})
const documentRagSelectedFilename = computed(() => {
  return documentRagResult.value?.summary?.upload_materialization?.filename || documentRagFile.value?.name || ''
})
const documentRagFileName = computed(() => documentRagFile.value?.name || '')
const documentRagQuestionReportPath = computed(() => {
  return documentRagQuestionResult.value?.markdown_path || documentRagQuestionResult.value?.json_path || ''
})
const documentRagQuestionCitations = computed(() => {
  const citations = documentRagQuestionResult.value?.citations
  return Array.isArray(citations) ? citations : []
})

onMounted(() => {
  loadDiagnostics()
})

onBeforeUnmount(() => {
  Object.values(audioUrls).forEach(url => URL.revokeObjectURL(url))
})

async function loadDiagnostics() {
  loading.value = true
  loadError.value = ''
  try {
    const [capabilitiesResponse, heartbeatResponse] = await Promise.all([
      capabilityApi.list(),
      capabilityApi.heartbeat()
    ])
    capabilities.value = capabilitiesResponse.data?.capabilities || []
    heartbeat.value = heartbeatResponse.data || null
  } catch (error) {
    loadError.value = '能力诊断加载失败: ' + (error.response?.data?.error?.message || error.message || '未知错误')
  } finally {
    loading.value = false
  }
}

async function runCapabilityTest(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  clearArtifactResult(capabilityId)
  clearAudioUrl(capabilityId)
  try {
    const payload = await buildTestPayload(capability)
    const response = await capabilityApi.test(capabilityId, { payload, mode: 'default' })
    testResults[capabilityId] = response.data
    attachAudioUrl(capabilityId, response.data?.result_summary)
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'CAPABILITY_TEST_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runOcrInvoke(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  clearArtifactResult(capabilityId)
  try {
    const payload = await buildOcrInvokePayload(capabilityId)
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'OCR_INVOKE_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runLayoutInvoke(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  clearArtifactResult(capabilityId)
  try {
    const payload = await buildLayoutInvokePayload(capabilityId)
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'LAYOUT_INVOKE_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runVlmInvoke(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  clearArtifactResult(capabilityId)
  try {
    const payload = await buildVlmInvokePayload(capabilityId)
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'VLM_INVOKE_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runVlmAsyncSubmit(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  clearArtifactResult(capabilityId)
  try {
    const payload = await buildVlmInvokePayload(capabilityId, 'submit')
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
    if (response.data?.ok && response.data?.result?.job_id) {
      vlmJobIds[capabilityId] = String(response.data.result.job_id)
    }
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'VLM_ASYNC_SUBMIT_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function runVlmAsyncStatus(capability) {
  const capabilityId = capability.capability_id
  testing[capabilityId] = true
  testResults[capabilityId] = null
  clearArtifactResult(capabilityId)
  try {
    const payload = await buildVlmInvokePayload(capabilityId, 'status')
    const response = await capabilityApi.invoke(capabilityId, payload)
    testResults[capabilityId] = response.data
  } catch (error) {
    testResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'VLM_ASYNC_STATUS_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    testing[capabilityId] = false
  }
}

async function buildTestPayload(capability) {
  if (capability.kind !== 'asr' || !asrFiles[capability.capability_id]) {
    return {}
  }
  const file = asrFiles[capability.capability_id]
  const mediaType = resolveAsrMediaType(file)
  if (!isSupportedAsrMediaType(mediaType)) {
    throw new Error('ASR 测试仅支持 16kHz / mono / PCM s16le 文件，请先将 MP3/WAV/WebM 转为 raw PCM。')
  }
  const audioBase64 = await readFileAsBase64(file)
  return {
    audio_base64: audioBase64,
    media_type: mediaType,
    language: 'zh-cn'
  }
}

function handleAsrFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    asrFiles[capabilityId] = file
    return
  }
  delete asrFiles[capabilityId]
}

function handleOcrFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    ocrFiles[capabilityId] = file
    return
  }
  delete ocrFiles[capabilityId]
}

function setOcrVisualize(capabilityId, event) {
  ocrVisualize[capabilityId] = Boolean(event.target.checked)
}

function handleLayoutFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    layoutFiles[capabilityId] = file
    return
  }
  delete layoutFiles[capabilityId]
}

function setLayoutIncludeTables(capabilityId, event) {
  layoutIncludeTables[capabilityId] = Boolean(event.target.checked)
}

function setLayoutIncludeLayout(capabilityId, event) {
  layoutIncludeLayout[capabilityId] = Boolean(event.target.checked)
}

function setLayoutOutputFormat(capabilityId, event) {
  layoutOutputFormat[capabilityId] = String(event.target.value || 'markdown')
}

function setLayoutMaxPages(capabilityId, event) {
  const value = String(event.target.value || '').trim()
  layoutMaxPages[capabilityId] = value
}

function handleVlmFile(capabilityId, event) {
  const file = event.target.files?.[0]
  if (file) {
    vlmFiles[capabilityId] = file
    return
  }
  delete vlmFiles[capabilityId]
}

function setVlmTask(capabilityId, event) {
  vlmTasks[capabilityId] = String(event.target.value || 'summarize')
}

function setVlmQuestion(capabilityId, event) {
  vlmQuestions[capabilityId] = String(event.target.value || '')
}

function setVlmMaxPages(capabilityId, event) {
  vlmMaxPages[capabilityId] = String(event.target.value || '').trim()
}

function setVlmJobId(capabilityId, event) {
  vlmJobIds[capabilityId] = String(event.target.value || '').trim()
}

function handleIngestionFile(event) {
  const file = event.target.files?.[0]
  ingestionFile.value = file || null
  ingestionResult.value = null
}

function handleDocumentRagFile(event) {
  const file = event.target.files?.[0]
  documentRagFile.value = file || null
  documentRagResult.value = null
  documentRagQuestionResult.value = null
}

async function submitDocumentIngestion() {
  ingestionSubmitting.value = true
  ingestionResult.value = null
  try {
    const payload = await buildDocumentIngestionPayload()
    const response = await documentIngestionApi.submit(payload)
    ingestionResult.value = response.data
  } catch (error) {
    ingestionResult.value = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'DOCUMENT_INGEST_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    ingestionSubmitting.value = false
  }
}

async function runDocumentRagReadiness() {
  documentRagReadinessRunning.value = true
  documentRagResult.value = null
  try {
    const response = await documentRagLocalTrialApi.readiness(buildDocumentRagBasePayload())
    documentRagResult.value = response.data
  } catch (error) {
    documentRagResult.value = {
      ok: false,
      ...(error.response?.data || {}),
      error: error.response?.data?.error || {
        code: 'DOCUMENT_RAG_READINESS_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    documentRagReadinessRunning.value = false
  }
}

async function runDocumentRagLocalTrial() {
  documentRagTrialRunning.value = true
  documentRagResult.value = null
  try {
    const payload = {
      ...buildDocumentRagBasePayload(),
      parse_mode: documentRagParseMode.value || 'ocr',
      allow_review_readiness: true
    }
    const file = documentRagFile.value
    if (file) {
      payload.file_base64 = await readFileAsBase64(file)
      payload.media_type = resolveOcrMediaType(file)
      payload.filename = file.name
    } else {
      payload.document_path = String(documentRagPath.value || '').trim()
    }
    const response = await documentRagLocalTrialApi.run(payload)
    documentRagResult.value = response.data
  } catch (error) {
    documentRagResult.value = {
      ok: false,
      ...(error.response?.data || {}),
      error: error.response?.data?.error || {
        code: 'DOCUMENT_RAG_LOCAL_TRIAL_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    documentRagTrialRunning.value = false
  }
}

async function runDocumentRagQuestionTrial() {
  documentRagQuestionRunning.value = true
  documentRagQuestionResult.value = null
  try {
    const response = await documentRagLocalTrialApi.questionTrial({
      ...buildDocumentRagBasePayload(),
      question: String(documentRagQuestion.value || '').trim(),
      top_k: toPositiveInteger(documentRagTopK.value) || 3
    })
    documentRagQuestionResult.value = response.data
  } catch (error) {
    documentRagQuestionResult.value = {
      ok: false,
      ...(error.response?.data || {}),
      error: error.response?.data?.error || {
        code: 'DOCUMENT_RAG_QUESTION_TRIAL_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    documentRagQuestionRunning.value = false
  }
}

function buildDocumentRagBasePayload() {
  return {
    source_id: String(documentRagSourceId.value || '').trim() || 'company_profile_2025_trial',
    ocr_profile: documentRagOcrProfile.value || 'unknown',
    ocr_timeout_seconds: Number(documentRagOcrTimeoutSeconds.value) || 180,
    provider_base_url: String(documentRagProviderBaseUrl.value || '').trim() || 'http://127.0.0.1:8020',
    knowledge_provider_repo: String(documentRagProviderRepo.value || '').trim(),
    provider_python: String(documentRagProviderPython.value || '').trim() || 'conda run -n GRAPHRAG python'
  }
}

async function buildDocumentIngestionPayload() {
  const file = ingestionFile.value
  if (!file) {
    throw new Error('请先选择文档文件（png/jpg/pdf）')
  }
  const parseMode = String(ingestionParseMode.value || 'layout')
  const payload = {
    parse_mode: parseMode,
    file_base64: await readFileAsBase64(file),
    media_type: resolveOcrMediaType(file),
    filename: file.name,
    max_pages: toPositiveInteger(ingestionMaxPages.value)
  }
  if (parseMode === 'layout') {
    payload.output_format = ingestionLayoutOutputFormat.value || 'markdown'
    payload.include_tables = ingestionLayoutIncludeTables.value
    payload.include_layout = ingestionLayoutIncludeLayout.value
  }
  if (parseMode === 'vlm_async') {
    payload.task = ingestionVlmTask.value || 'summarize'
    payload.question = String(ingestionVlmQuestion.value || '')
  }
  return payload
}

function resolveAsrMediaType(file) {
  if (!file.type || file.name?.toLowerCase().endsWith('.pcm') || file.name?.toLowerCase().endsWith('.raw')) {
    return 'audio/pcm;rate=16000;channels=1;format=s16le'
  }
  return file.type
}

function isSupportedAsrMediaType(mediaType) {
  const value = String(mediaType || '').toLowerCase()
  return value.startsWith('audio/pcm') || value === 'application/octet-stream'
}

function readFileAsBase64(file) {
  if (file && typeof file.arrayBuffer === 'function') {
    return file.arrayBuffer().then(buffer => {
      const bytes = new Uint8Array(buffer)
      let binary = ''
      for (let i = 0; i < bytes.length; i += 1) {
        binary += String.fromCharCode(bytes[i])
      }
      return btoa(binary)
    })
  }
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = () => {
      const value = String(reader.result || '')
      resolve(value.includes(',') ? value.split(',').pop() : value)
    }
    reader.onerror = () => reject(reader.error)
    reader.readAsDataURL(file)
  })
}

async function buildOcrInvokePayload(capabilityId) {
  const file = ocrFiles[capabilityId]
  if (!file) {
    throw new Error('请先选择 OCR 文件（png/jpg/pdf）')
  }
  const mediaType = resolveOcrMediaType(file)
  const fileBase64 = await readFileAsBase64(file)
  return {
    file_base64: fileBase64,
    media_type: mediaType,
    filename: file.name,
    visualize: ocrVisualize[capabilityId] === true
  }
}

function resolveOcrMediaType(file) {
  const name = String(file.name || '').toLowerCase()
  if (name.endsWith('.pdf')) return 'application/pdf'
  if (name.endsWith('.png')) return 'image/png'
  if (name.endsWith('.jpg') || name.endsWith('.jpeg')) return 'image/jpeg'
  if (file.type) return file.type
  return 'application/octet-stream'
}

async function buildLayoutInvokePayload(capabilityId) {
  const file = layoutFiles[capabilityId]
  if (!file) {
    throw new Error('请先选择 Layout 文件（png/jpg/pdf）')
  }
  const mediaType = resolveOcrMediaType(file)
  const fileBase64 = await readFileAsBase64(file)
  return {
    file_base64: fileBase64,
    media_type: mediaType,
    filename: file.name,
    output_format: layoutOutputFormat[capabilityId] || 'markdown',
    include_tables: layoutIncludeTables[capabilityId] !== false,
    include_layout: layoutIncludeLayout[capabilityId] !== false,
    max_pages: toPositiveInteger(layoutMaxPages[capabilityId])
  }
}

async function buildVlmInvokePayload(capabilityId, operation = 'submit') {
  if (operation === 'status') {
    const jobId = String(vlmJobIds[capabilityId] || '').trim()
    if (!jobId) {
      throw new Error('请先输入任务 ID（job_id）')
    }
    return {
      operation: 'status',
      job_id: jobId
    }
  }
  const file = vlmFiles[capabilityId]
  if (!file) {
    throw new Error('请先选择 VLM 文件（png/jpg/pdf）')
  }
  const mediaType = resolveOcrMediaType(file)
  const fileBase64 = await readFileAsBase64(file)
  return {
    operation: 'submit',
    file_base64: fileBase64,
    media_type: mediaType,
    filename: file.name,
    task: vlmTasks[capabilityId] || 'summarize',
    question: String(vlmQuestions[capabilityId] || ''),
    max_pages: toPositiveInteger(vlmMaxPages[capabilityId])
  }
}

function toPositiveInteger(value) {
  if (value === undefined || value === null || value === '') {
    return undefined
  }
  const numeric = Number.parseInt(String(value), 10)
  if (!Number.isFinite(numeric) || numeric <= 0) {
    return undefined
  }
  return numeric
}

function attachAudioUrl(capabilityId, summary = {}) {
  const audioBase64 = summary.audio_base64
  if (!audioBase64) return
  const mediaType = summary.media_type || 'audio/mpeg'
  const bytes = Uint8Array.from(atob(audioBase64), char => char.charCodeAt(0))
  const blob = new Blob([bytes], { type: mediaType })
  audioUrls[capabilityId] = URL.createObjectURL(blob)
}

function clearAudioUrl(capabilityId) {
  if (audioUrls[capabilityId]) {
    URL.revokeObjectURL(audioUrls[capabilityId])
    delete audioUrls[capabilityId]
  }
}

function formatResult(result) {
  return JSON.stringify(result.result_summary || result.error || result, null, 2)
}

function formatJson(value) {
  return JSON.stringify(value ?? {}, null, 2)
}

function ocrResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    text: String(payload.text || ''),
    pages: Array.isArray(payload.pages) ? payload.pages : [],
    blocks: Array.isArray(payload.blocks) ? payload.blocks : [],
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

function layoutResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    markdown: String(payload.markdown || ''),
    elements: Array.isArray(payload.elements) ? payload.elements : [],
    tables: Array.isArray(payload.tables) ? payload.tables : [],
    pages: Array.isArray(payload.pages) ? payload.pages : [],
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

function vlmResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    summary: String(payload.summary || ''),
    sections: Array.isArray(payload.sections) ? payload.sections : [],
    answers: Array.isArray(payload.answers) ? payload.answers : [],
    evidence: Array.isArray(payload.evidence) ? payload.evidence : [],
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

function vlmAsyncResultView(result) {
  if (!result || !result.ok) return null
  const payload = typeof result.result === 'object' && result.result ? result.result : null
  if (!payload) return null
  return {
    job_id: String(payload.job_id || ''),
    status: String(payload.status || 'unknown'),
    progress: payload.progress ?? 0,
    result: typeof payload.result === 'object' && payload.result ? payload.result : {},
    error: typeof payload.error === 'object' && payload.error ? payload.error : {},
    warnings: Array.isArray(payload.warnings) ? payload.warnings.map(item => String(item)) : [],
    raw: typeof payload.raw === 'object' && payload.raw ? payload.raw : {}
  }
}

function canPersistDocumentArtifact(capability) {
  const capabilityId = capability.capability_id
  const result = testResults[capabilityId]
  if (!result?.ok) return false
  if (capability.kind === 'ocr') return Boolean(ocrResultView(result))
  if (capability.kind === 'layout') return Boolean(layoutResultView(result))
  if (capability.kind !== 'vlm') return false
  if (capabilityId !== 'document.vlm.parse.async') return Boolean(vlmResultView(result))
  const asyncView = vlmAsyncResultView(result)
  return Boolean(asyncView && asyncView.status === 'succeeded' && Object.keys(asyncView.result || {}).length > 0)
}

async function persistDocumentArtifact(capability) {
  const capabilityId = capability.capability_id
  artifactSaving[capabilityId] = true
  clearArtifactResult(capabilityId)
  try {
    const response = await documentArtifactApi.persist({
      source_filename: resolveDocumentSourceFilename(capabilityId),
      media_type: resolveDocumentSourceMediaType(capabilityId),
      capability_id: capabilityId,
      provider: capability.provider || 'unknown',
      result: documentResultPayload(capability),
      include_raw: false
    })
    artifactResults[capabilityId] = {
      ok: true,
      artifact: response.data?.artifact || {}
    }
  } catch (error) {
    artifactResults[capabilityId] = {
      ok: false,
      error: error.response?.data?.error || error.response?.data || {
        code: 'DOCUMENT_ARTIFACT_PERSIST_REQUEST_FAILED',
        message: error.message || '请求失败'
      }
    }
  } finally {
    artifactSaving[capabilityId] = false
  }
}

function documentResultPayload(capability) {
  const capabilityId = capability.capability_id
  const result = testResults[capabilityId]
  if (capability.kind === 'ocr') return ocrResultView(result) || {}
  if (capability.kind === 'layout') return layoutResultView(result) || {}
  if (capabilityId === 'document.vlm.parse.async') return vlmAsyncResultView(result)?.result || {}
  if (capability.kind === 'vlm') return vlmResultView(result) || {}
  return {}
}

function resolveDocumentSourceFilename(capabilityId) {
  const file = ocrFiles[capabilityId] || layoutFiles[capabilityId] || vlmFiles[capabilityId]
  return file?.name || ''
}

function resolveDocumentSourceMediaType(capabilityId) {
  const file = ocrFiles[capabilityId] || layoutFiles[capabilityId] || vlmFiles[capabilityId]
  return file ? resolveOcrMediaType(file) : ''
}

function artifactStatusText(capabilityId) {
  const result = artifactResults[capabilityId]
  if (!result) return ''
  if (result.ok) {
    return `artifact_id: ${result.artifact?.artifact_id || '(missing)'}`
  }
  const error = result.error || {}
  return `${error.code || 'DOCUMENT_ARTIFACT_PERSIST_FAILED'}: ${error.message || '保存失败'}`
}

function clearArtifactResult(capabilityId) {
  delete artifactResults[capabilityId]
}

async function copyLayoutMarkdown(markdown) {
  const value = String(markdown || '')
  if (!value || !navigator?.clipboard?.writeText) {
    return
  }
  await navigator.clipboard.writeText(value)
}

function downloadLayoutResult(capabilityId, result) {
  const payload = JSON.stringify(result || {}, null, 2)
  const blob = new Blob([payload], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `${capabilityId.replace(/[^\w.-]/g, '_')}.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
}

function formatOcrBlocks(blocks) {
  if (!Array.isArray(blocks) || blocks.length === 0) {
    return '(empty)'
  }
  return blocks
    .map((block, idx) => {
      const confidence = block?.confidence === null || block?.confidence === undefined ? '-' : block.confidence
      const bbox = Array.isArray(block?.bbox) ? JSON.stringify(block.bbox) : '-'
      const text = String(block?.text || '').trim() || '(empty)'
      return `${idx + 1}. conf=${confidence} bbox=${bbox}\n${text}`
    })
    .join('\n\n')
}

function statusClass(status) {
  if (['ok', 'ready', 'succeeded'].includes(status)) return 'configured'
  if (['queued', 'running', 'disabled', 'unconfigured', 'missing_dependency', 'unreachable'].includes(status)) return 'unconfigured'
  return 'error'
}

function formatRetryAfter(value) {
  const numeric = Number(value)
  if (!Number.isFinite(numeric) || numeric < 0) return '0.00'
  return numeric.toFixed(2)
}
</script>

<style scoped>
.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--space-md);
}

.section-desc {
  color: var(--text-secondary);
  font-size: 0.875rem;
  margin: 4px 0 var(--space-md);
}

.heartbeat-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: var(--space-sm);
  margin-bottom: var(--space-md);
}

.breaker-meta {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.provider-card {
  background: var(--bg-secondary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-md);
  padding: var(--space-md);
  margin-bottom: var(--space-md);
}

.provider-card.compact {
  margin-bottom: 0;
}

.provider-header {
  display: flex;
  align-items: center;
  gap: var(--space-sm);
  flex-wrap: wrap;
  margin-bottom: var(--space-sm);
}

.provider-name {
  font-weight: 600;
}

.provider-badge,
.source-tag {
  font-size: 0.75rem;
  padding: 2px 8px;
  border-radius: var(--radius-sm);
}

.provider-badge.configured {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.15);
}

.provider-badge.unconfigured {
  color: #eab308;
  background: rgba(234, 179, 8, 0.15);
}

.provider-badge.error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.15);
}

.source-tag {
  color: var(--text-tertiary);
  background: var(--bg-tertiary);
}

.capability-meta,
.field-hint,
.loading-hint {
  color: var(--text-secondary);
  font-size: 0.8rem;
}

.capability-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-sm);
}

.provider-actions {
  display: flex;
  gap: var(--space-sm);
  margin: var(--space-sm) 0;
}

.action-btn {
  padding: 6px 14px;
  font-size: 0.8rem;
  border-radius: var(--radius-sm);
  cursor: pointer;
  border: 1px solid var(--border-color);
  background: var(--bg-tertiary);
  color: var(--text-primary);
}

.action-btn:hover:not(:disabled) {
  border-color: var(--primary);
}

.action-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.field-row {
  display: flex;
  flex-direction: column;
  gap: 4px;
  margin-bottom: var(--space-sm);
}

.field-input {
  padding: 6px 10px;
  background: var(--bg-primary);
  border: 1px solid var(--border-color);
  border-radius: var(--radius-sm);
  color: var(--text-primary);
}

.inline-check {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 0.8rem;
  color: var(--text-secondary);
}

.test-result {
  font-size: 0.8rem;
  padding: 8px 10px;
  border-radius: var(--radius-sm);
}

.test-result.ok {
  color: #22c55e;
  background: rgba(34, 197, 94, 0.1);
}

.test-result.error {
  color: #ef4444;
  background: rgba(239, 68, 68, 0.1);
}

.ocr-summary {
  display: flex;
  flex-wrap: wrap;
  gap: var(--space-sm);
  margin-top: 8px;
  color: var(--text-primary);
}

.ocr-warning-list {
  display: flex;
  flex-direction: column;
  margin-top: 8px;
}

.ocr-section {
  margin-top: 8px;
}

.ocr-section > summary {
  cursor: pointer;
  color: var(--text-primary);
}

pre {
  overflow: auto;
  max-height: 180px;
  margin: 8px 0;
  color: var(--text-primary);
  white-space: pre-wrap;
}

audio {
  width: 100%;
  margin-top: 8px;
}
</style>
