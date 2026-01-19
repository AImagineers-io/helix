/**
 * Tests for Dashboard page
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import Dashboard from '../Dashboard'
import { analyticsApi } from '../../services/analytics-api'

// Mock the analytics API
vi.mock('../../services/analytics-api')
const mockedAnalyticsApi = vi.mocked(analyticsApi)

describe('Dashboard', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render dashboard heading', async () => {
    mockedAnalyticsApi.getSummary.mockResolvedValue({
      qa_stats: { total: 0, active: 0, draft: 0, pending: 0 },
      conversation_stats: { today: 0, this_week: 0, this_month: 0 },
      cost_summary: {
        current_month: 0.0,
        projected_month_end: 0.0,
        by_provider: { openai: 0.0, anthropic: 0.0 },
      },
    })

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByRole('heading', { name: /dashboard/i })).toBeInTheDocument()
    })
  })

  it('should fetch analytics data on mount', async () => {
    const mockSummary = {
      qa_stats: { total: 100, active: 80, draft: 15, pending: 5 },
      conversation_stats: { today: 25, this_week: 150, this_month: 450 },
      cost_summary: {
        current_month: 125.5,
        projected_month_end: 250.0,
        by_provider: { openai: 100.0, anthropic: 25.5 },
      },
    }

    mockedAnalyticsApi.getSummary.mockResolvedValue(mockSummary)

    render(<Dashboard />)

    await waitFor(() => {
      expect(mockedAnalyticsApi.getSummary).toHaveBeenCalledTimes(1)
    })
  })

  it('should display loading state while fetching data', () => {
    mockedAnalyticsApi.getSummary.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    render(<Dashboard />)
    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('should display error message when fetch fails', async () => {
    mockedAnalyticsApi.getSummary.mockRejectedValue(new Error('API error'))

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('should display QA statistics', async () => {
    const mockSummary = {
      qa_stats: { total: 100, active: 80, draft: 15, pending: 5 },
      conversation_stats: { today: 25, this_week: 150, this_month: 450 },
      cost_summary: {
        current_month: 125.5,
        projected_month_end: 250.0,
        by_provider: { openai: 100.0, anthropic: 25.5 },
      },
    }

    mockedAnalyticsApi.getSummary.mockResolvedValue(mockSummary)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText(/Total: 100/)).toBeInTheDocument()
      expect(screen.getByText(/Active: 80/)).toBeInTheDocument()
    })
  })

  it('should display conversation statistics', async () => {
    const mockSummary = {
      qa_stats: { total: 100, active: 80, draft: 15, pending: 5 },
      conversation_stats: { today: 25, this_week: 150, this_month: 450 },
      cost_summary: {
        current_month: 125.5,
        projected_month_end: 250.0,
        by_provider: { openai: 100.0, anthropic: 25.5 },
      },
    }

    mockedAnalyticsApi.getSummary.mockResolvedValue(mockSummary)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText(/Today: 25/)).toBeInTheDocument()
      expect(screen.getByText(/This Week: 150/)).toBeInTheDocument()
      expect(screen.getByText(/This Month: 450/)).toBeInTheDocument()
    })
  })

  it('should display cost summary', async () => {
    const mockSummary = {
      qa_stats: { total: 100, active: 80, draft: 15, pending: 5 },
      conversation_stats: { today: 25, this_week: 150, this_month: 450 },
      cost_summary: {
        current_month: 125.5,
        projected_month_end: 250.0,
        by_provider: { openai: 100.0, anthropic: 25.5 },
      },
    }

    mockedAnalyticsApi.getSummary.mockResolvedValue(mockSummary)

    render(<Dashboard />)

    await waitFor(() => {
      expect(screen.getByText(/\$125.50/)).toBeInTheDocument() // current month
      expect(screen.getByText(/\$250.00/)).toBeInTheDocument() // projected
    })
  })
})
