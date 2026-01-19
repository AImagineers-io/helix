/**
 * QA Statistics Widget
 *
 * Displays QA pair statistics with breakdown by status.
 */
import type { QAStats } from '../../services/analytics-api'
import StatsCard from './StatsCard'

export interface QAStatsWidgetProps {
  stats: QAStats
}

export default function QAStatsWidget({ stats }: QAStatsWidgetProps) {
  return (
    <div className="qa-stats-widget">
      <h2>QA Pairs</h2>
      <div className="stats-grid">
        <StatsCard title="Total" value={stats.total} />
        <StatsCard title="Active" value={stats.active} />
        <StatsCard title="Draft" value={stats.draft} />
        <StatsCard title="Pending" value={stats.pending} />
      </div>
    </div>
  )
}
