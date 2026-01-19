import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, waitFor, fireEvent } from '@testing-library/react'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { PromptEditor } from '../PromptEditor'
import { promptsApi } from '../../../services/prompts-api'

vi.mock('../../../services/prompts-api')

const mockedPromptsApi = vi.mocked(promptsApi)

const mockPrompt = {
  id: 1,
  name: 'System Prompt',
  prompt_type: 'system',
  description: 'Main system prompt',
  created_at: '2025-01-01T00:00:00Z',
  updated_at: '2025-01-01T00:00:00Z',
  versions: [
    {
      id: 1,
      template_id: 1,
      content: 'You are a helpful assistant.',
      version_number: 1,
      is_active: true,
      created_at: '2025-01-01T00:00:00Z',
      created_by: 'admin',
      change_notes: null,
    },
  ],
}

const renderWithRouter = (promptId = '1') => {
  return render(
    <BrowserRouter>
      <Routes>
        <Route path="/prompts/:id" element={<PromptEditor />} />
      </Routes>
    </BrowserRouter>,
    {
      wrapper: ({ children }) => (
        <BrowserRouter>
          <Routes>
            <Route path="/prompts/:id" element={children} />
          </Routes>
        </BrowserRouter>
      ),
    }
  )
}

describe('PromptEditor', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    // Mock useParams to return id
    vi.mock('react-router-dom', async () => {
      const actual = await vi.importActual('react-router-dom')
      return {
        ...actual,
        useParams: () => ({ id: '1' }),
      }
    })
  })

  it('should display loading state initially', () => {
    mockedPromptsApi.getPrompt.mockImplementation(() => new Promise(() => {}))

    render(<PromptEditor />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('should display prompt editor when loaded', async () => {
    mockedPromptsApi.getPrompt.mockResolvedValue(mockPrompt)

    render(<PromptEditor />)

    await waitFor(() => {
      expect(screen.getByText('System Prompt')).toBeInTheDocument()
      expect(screen.getByDisplayValue('You are a helpful assistant.')).toBeInTheDocument()
    })
  })

  it('should display error message when API fails', async () => {
    mockedPromptsApi.getPrompt.mockRejectedValue(new Error('API Error'))

    render(<PromptEditor />)

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument()
    })
  })

  it('should allow editing prompt content', async () => {
    mockedPromptsApi.getPrompt.mockResolvedValue(mockPrompt)

    render(<PromptEditor />)

    await waitFor(() => {
      const textarea = screen.getByDisplayValue('You are a helpful assistant.')
      fireEvent.change(textarea, { target: { value: 'Updated content' } })
      expect(textarea).toHaveValue('Updated content')
    })
  })

  it('should call update API when saving', async () => {
    mockedPromptsApi.getPrompt.mockResolvedValue(mockPrompt)
    mockedPromptsApi.updatePrompt.mockResolvedValue({
      ...mockPrompt,
      versions: [
        {
          id: 2,
          template_id: 1,
          content: 'Updated content',
          version_number: 2,
          is_active: false,
          created_at: '2025-01-01T01:00:00Z',
          created_by: 'admin',
          change_notes: null,
        },
        ...mockPrompt.versions,
      ],
    })

    render(<PromptEditor />)

    await waitFor(() => screen.getByDisplayValue('You are a helpful assistant.'))

    const textarea = screen.getByDisplayValue('You are a helpful assistant.')
    fireEvent.change(textarea, { target: { value: 'Updated content' } })

    const saveButton = screen.getByRole('button', { name: /save/i })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(mockedPromptsApi.updatePrompt).toHaveBeenCalledWith(1, {
        content: 'Updated content',
        created_by: undefined,
        change_notes: undefined,
      })
    })
  })

  it('should display success message after saving', async () => {
    mockedPromptsApi.getPrompt.mockResolvedValue(mockPrompt)
    mockedPromptsApi.updatePrompt.mockResolvedValue({
      ...mockPrompt,
      versions: [
        {
          id: 2,
          template_id: 1,
          content: 'Updated content',
          version_number: 2,
          is_active: false,
          created_at: '2025-01-01T01:00:00Z',
          created_by: 'admin',
          change_notes: null,
        },
        ...mockPrompt.versions,
      ],
    })

    render(<PromptEditor />)

    await waitFor(() => screen.getByDisplayValue('You are a helpful assistant.'))

    const textarea = screen.getByDisplayValue('You are a helpful assistant.')
    fireEvent.change(textarea, { target: { value: 'Updated content' } })

    const saveButton = screen.getByRole('button', { name: /save/i })
    fireEvent.click(saveButton)

    await waitFor(() => {
      expect(screen.getByText(/saved successfully/i)).toBeInTheDocument()
    })
  })

  it('should display prompt name and description', async () => {
    mockedPromptsApi.getPrompt.mockResolvedValue(mockPrompt)

    render(<PromptEditor />)

    await waitFor(() => {
      expect(screen.getByText('System Prompt')).toBeInTheDocument()
      expect(screen.getByText('Main system prompt')).toBeInTheDocument()
    })
  })
})
