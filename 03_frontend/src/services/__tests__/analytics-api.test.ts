/**
 * Tests for Analytics API Client
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { analyticsApi } from '../analytics-api'

// Mock axios
vi.mock('axios')
const mockedAxios = vi.mocked(axios, true)

describe('analyticsApi', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('getSummary', () => {
    it('should fetch analytics summary from API', async () => {
      const mockData = {
        qa_stats: {
          total: 100,
          active: 80,
          draft: 15,
          pending: 5,
        },
        conversation_stats: {
          today: 25,
          this_week: 150,
          this_month: 450,
        },
        cost_summary: {
          current_month: 125.50,
          projected_month_end: 250.00,
          by_provider: {
            openai: 100.00,
            anthropic: 25.50,
          },
        },
      }

      mockedAxios.get.mockResolvedValueOnce({ data: mockData })

      const result = await analyticsApi.getSummary()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/analytics/summary', {
        headers: {
          'X-API-Key': undefined,
        },
      })
      expect(result).toEqual(mockData)
    })

    it('should include API key from environment', async () => {
      const mockData = {
        qa_stats: { total: 0, active: 0, draft: 0, pending: 0 },
        conversation_stats: { today: 0, this_week: 0, this_month: 0 },
        cost_summary: {
          current_month: 0.0,
          projected_month_end: 0.0,
          by_provider: { openai: 0.0, anthropic: 0.0 },
        },
      }

      // Mock environment variable
      import.meta.env.VITE_API_KEY = 'test-key'

      mockedAxios.get.mockResolvedValueOnce({ data: mockData })

      await analyticsApi.getSummary()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/analytics/summary', {
        headers: {
          'X-API-Key': 'test-key',
        },
      })

      // Clean up
      delete import.meta.env.VITE_API_KEY
    })

    it('should handle API errors', async () => {
      mockedAxios.get.mockRejectedValueOnce(new Error('API error'))

      await expect(analyticsApi.getSummary()).rejects.toThrow('API error')
    })

    it('should return properly typed response', async () => {
      const mockData = {
        qa_stats: {
          total: 50,
          active: 40,
          draft: 8,
          pending: 2,
        },
        conversation_stats: {
          today: 10,
          this_week: 70,
          this_month: 300,
        },
        cost_summary: {
          current_month: 75.25,
          projected_month_end: 150.50,
          by_provider: {
            openai: 60.00,
            anthropic: 15.25,
          },
        },
      }

      mockedAxios.get.mockResolvedValueOnce({ data: mockData })

      const result = await analyticsApi.getSummary()

      // Type checks
      expect(typeof result.qa_stats.total).toBe('number')
      expect(typeof result.conversation_stats.today).toBe('number')
      expect(typeof result.cost_summary.current_month).toBe('number')
      expect(typeof result.cost_summary.by_provider.openai).toBe('number')
    })
  })
})
