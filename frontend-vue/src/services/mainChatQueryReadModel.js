import { normalizeMainChatQueryDetailContract } from './mainChatQueryDetail'
import { normalizeMainChatQueryHistoryContract } from './mainChatQueryHistory'
import {
  buildCurrentQueryDetail,
  buildCurrentQueryOverview,
  buildHistoryStageTags,
  buildMainChatHistoryContextLabel,
  buildMainChatHistoryStatus,
  filterMainChatHistoryItems,
  isHistoryStageFocused,
} from './mainChatQueryGovernance'

const EMPTY_MAIN_CHAT_QUERY_DETAIL = {
  connected: false,
  readModelLayer: '',
  sourceChannel: '',
  identityKind: '',
  queryId: '',
  associatedRunIds: [],
  recordingState: 'unavailable',
  stageChain: [],
  dedupeKeys: [],
  dedupeKeyCount: 0,
  recentEvents: [],
  latestSnapshotId: '',
  latestWarningSummary: '',
  latestStage: '',
  latestSummary: '',
  stageCount: 0,
  warningCount: 0,
  eventCount: 0,
  recentEventCount: 0,
  reason: '',
}

export function buildMainChatQueryDetailContract(value) {
  return normalizeMainChatQueryDetailContract(value) || { ...EMPTY_MAIN_CHAT_QUERY_DETAIL }
}

export function buildMainChatQueryHistoryContract(value) {
  return normalizeMainChatQueryHistoryContract(value)
}

export {
  buildCurrentQueryDetail,
  buildCurrentQueryOverview,
  buildHistoryStageTags,
  buildMainChatHistoryContextLabel,
  buildMainChatHistoryStatus,
  filterMainChatHistoryItems,
  isHistoryStageFocused,
  normalizeMainChatQueryDetailContract,
  normalizeMainChatQueryHistoryContract,
}
