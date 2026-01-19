/**
 * Cost Tracking Widget
 *
 * Displays cost summary with provider breakdown.
 */
import type { CostSummary } from '../../services/analytics-api'
import StatsCard from './StatsCard'

export interface CostWidgetProps {
  summary: CostSummary
}

export default function CostWidget({ summary }: CostWidgetProps) {
  const formatCurrency = (amount: number) => `$${amount.toFixed(2)}`

  return (
    <div className="cost-widget">
      <h2>Costs</h2>
      <div className="stats-grid">
        <StatsCard title="Current Month" value={formatCurrency(summary.current_month)} />
        <StatsCard
          title="Projected Month-End"
          value={formatCurrency(summary.projected_month_end)}
        />
        <StatsCard title="OpenAI" value={formatCurrency(summary.by_provider.openai)} />
        <StatsCard title="Anthropic" value={formatCurrency(summary.by_provider.anthropic)} />
      </div>
    </div>
  )
}
