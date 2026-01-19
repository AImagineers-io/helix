/**
 * StatsCard Component
 *
 * Reusable card component for displaying dashboard statistics.
 */
export interface StatsCardProps {
  title: string
  value: string | number
  subtitle?: string
}

export default function StatsCard({ title, value, subtitle }: StatsCardProps) {
  return (
    <div className="stats-card">
      <h3>{title}</h3>
      <div className="stats-value">{value}</div>
      {subtitle && <p className="stats-subtitle">{subtitle}</p>}
    </div>
  )
}
