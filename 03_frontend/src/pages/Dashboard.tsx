/**
 * Dashboard page component
 *
 * Main admin dashboard displaying:
 * - QA pair statistics
 * - Conversation metrics
 * - Cost tracking
 */
import { useEffect, useState } from 'react'
import { analyticsApi, type AnalyticsSummary } from '../services/analytics-api'

export default function Dashboard() {
  const [summary, setSummary] = useState<AnalyticsSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchSummary() {
      try {
        setLoading(true)
        setError(null)
        const data = await analyticsApi.getSummary()
        setSummary(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load dashboard data')
      } finally {
        setLoading(false)
      }
    }

    fetchSummary()
  }, [])

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error: {error}</div>
  }

  if (!summary) {
    return <div>No data available</div>
  }

  const formatCurrency = (amount: number) => {
    return `$${amount.toFixed(2)}`
  }

  return (
    <div>
      <h1>Dashboard</h1>

      {/* QA Statistics */}
      <section>
        <h2>QA Pairs</h2>
        <div>
          <div>Total: {summary.qa_stats.total}</div>
          <div>Active: {summary.qa_stats.active}</div>
          <div>Draft: {summary.qa_stats.draft}</div>
          <div>Pending: {summary.qa_stats.pending}</div>
        </div>
      </section>

      {/* Conversation Statistics */}
      <section>
        <h2>Conversations</h2>
        <div>
          <div>Today: {summary.conversation_stats.today}</div>
          <div>This Week: {summary.conversation_stats.this_week}</div>
          <div>This Month: {summary.conversation_stats.this_month}</div>
        </div>
      </section>

      {/* Cost Summary */}
      <section>
        <h2>Costs</h2>
        <div>
          <div>Current Month: {formatCurrency(summary.cost_summary.current_month)}</div>
          <div>Projected Month-End: {formatCurrency(summary.cost_summary.projected_month_end)}</div>
          <div>OpenAI: {formatCurrency(summary.cost_summary.by_provider.openai)}</div>
          <div>Anthropic: {formatCurrency(summary.cost_summary.by_provider.anthropic)}</div>
        </div>
      </section>
    </div>
  )
}
