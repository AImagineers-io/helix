import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { BrowserRouter } from 'react-router-dom'
import { PromptList } from '../PromptList'
import { promptsApi } from '../../../services/prompts-api'

vi.mock('../../../services/prompts-api')

const mockedPromptsApi = vi.mocked(promptsApi)

const renderWithRouter = (component: React.ReactElement) => {
  return render(<BrowserRouter>{component}</BrowserRouter>)
}

describe('PromptList', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should display loading state initially', () => {
    mockedPromptsApi.listPrompts.mockImplementation(
      () => new Promise(() => {}) // Never resolves
    )

    renderWithRouter(<PromptList />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('should display prompts list when loaded', async () => {
    const mockPrompts = [
      {
        id: 1,
        name: 'System Prompt',
        prompt_type: 'system',
        description: 'Main system prompt',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
      {
        id: 2,
        name: 'User Greeting',
        prompt_type: 'greeting',
        description: 'Greeting message',
        created_at: '2025-01-02T00:00:00Z',
        updated_at: '2025-01-02T00:00:00Z',
      },
    ]
    mockedPromptsApi.listPrompts.mockResolvedValue(mockPrompts)

    renderWithRouter(<PromptList />)

    await waitFor(() => {
      expect(screen.getByText('System Prompt')).toBeInTheDocument()
      expect(screen.getByText('User Greeting')).toBeInTheDocument()
    })
  })

  it('should display error message when API fails', async () => {
    mockedPromptsApi.listPrompts.mockRejectedValue(new Error('API Error'))

    renderWithRouter(<PromptList />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('should display empty state when no prompts', async () => {
    mockedPromptsApi.listPrompts.mockResolvedValue([])

    renderWithRouter(<PromptList />)

    await waitFor(() => {
      expect(screen.getByText(/no prompts/i)).toBeInTheDocument()
    })
  })

  it('should have links to edit each prompt', async () => {
    const mockPrompts = [
      {
        id: 1,
        name: 'System Prompt',
        prompt_type: 'system',
        description: 'Main system prompt',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
    ]
    mockedPromptsApi.listPrompts.mockResolvedValue(mockPrompts)

    renderWithRouter(<PromptList />)

    await waitFor(() => {
      const link = screen.getByRole('link', { name: /system prompt/i })
      expect(link).toHaveAttribute('href', '/prompts/1')
    })
  })

  it('should display prompt descriptions', async () => {
    const mockPrompts = [
      {
        id: 1,
        name: 'System Prompt',
        prompt_type: 'system',
        description: 'Main system prompt',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
      },
    ]
    mockedPromptsApi.listPrompts.mockResolvedValue(mockPrompts)

    renderWithRouter(<PromptList />)

    await waitFor(() => {
      expect(screen.getByText('Main system prompt')).toBeInTheDocument()
    })
  })
})
