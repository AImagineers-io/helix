/**
 * Analytics API Client
 *
 * Provides methods for fetching dashboard analytics data.
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * QA pair statistics.
 */
export interface QAStats {
  total: number
  active: number
  draft: number
  pending: number
}

/**
 * Conversation count statistics.
 */
export interface ConversationStats {
  today: number
  this_week: number
  this_month: number
}

/**
 * Cost breakdown by LLM provider.
 */
export interface ProviderCosts {
  openai: number
  anthropic: number
}

/**
 * Cost summary statistics.
 */
export interface CostSummary {
  current_month: number
  projected_month_end: number
  by_provider: ProviderCosts
}

/**
 * Complete analytics summary response.
 */
export interface AnalyticsSummary {
  qa_stats: QAStats
  conversation_stats: ConversationStats
  cost_summary: CostSummary
}

export const analyticsApi = {
  /**
   * Get analytics summary for admin dashboard.
   *
   * @returns Analytics summary with QA stats, conversation metrics, and costs
   */
  async getSummary(): Promise<AnalyticsSummary> {
    const apiKey = import.meta.env.VITE_API_KEY
    const response = await axios.get<AnalyticsSummary>(`${API_BASE_URL}/analytics/summary`, {
      headers: {
        'X-API-Key': apiKey,
      },
    })
    return response.data
  },
}
