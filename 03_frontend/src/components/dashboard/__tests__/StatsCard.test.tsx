/**
 * Tests for StatsCard component
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import StatsCard from '../StatsCard'

describe('StatsCard', () => {
  it('should render title and value', () => {
    render(<StatsCard title="Total QA Pairs" value={100} />)
    expect(screen.getByText('Total QA Pairs')).toBeInTheDocument()
    expect(screen.getByText('100')).toBeInTheDocument()
  })

  it('should render subtitle when provided', () => {
    render(<StatsCard title="Active" value={80} subtitle="Currently active" />)
    expect(screen.getByText('Currently active')).toBeInTheDocument()
  })

  it('should handle string values', () => {
    render(<StatsCard title="Cost" value="$125.50" />)
    expect(screen.getByText('$125.50')).toBeInTheDocument()
  })
})
