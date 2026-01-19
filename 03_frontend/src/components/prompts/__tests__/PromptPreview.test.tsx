import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PromptPreview } from '../PromptPreview'
import { promptsApi } from '../../../services/prompts-api'

vi.mock('../../../services/prompts-api')

const mockedPromptsApi = vi.mocked(promptsApi)

describe('PromptPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render sample input textarea', () => {
    render(<PromptPreview promptContent="Test prompt" />)

    expect(screen.getByLabelText(/sample input/i)).toBeInTheDocument()
  })

  it('should have a preview button', () => {
    render(<PromptPreview promptContent="Test prompt" />)

    expect(screen.getByRole('button', { name: /preview/i })).toBeInTheDocument()
  })

  it('should allow entering sample input', () => {
    render(<PromptPreview promptContent="Test prompt" />)

    const textarea = screen.getByLabelText(/sample input/i)
    fireEvent.change(textarea, { target: { value: 'Sample user input' } })

    expect(textarea).toHaveValue('Sample user input')
  })

  it('should show preview when generated', async () => {
    render(<PromptPreview promptContent="Test prompt" />)

    const textarea = screen.getByLabelText(/sample input/i)
    fireEvent.change(textarea, { target: { value: 'Hello' } })

    const previewButton = screen.getByRole('button', { name: /preview/i })
    fireEvent.click(previewButton)

    // For now, preview shows the combined content locally
    await waitFor(() => {
      expect(screen.getByText(/test prompt/i)).toBeInTheDocument()
    })
  })

  it('should display prompt content in preview', async () => {
    render(<PromptPreview promptContent="You are a helpful assistant." />)

    const textarea = screen.getByLabelText(/sample input/i)
    fireEvent.change(textarea, { target: { value: 'Hello' } })

    const previewButton = screen.getByRole('button', { name: /preview/i })
    fireEvent.click(previewButton)

    await waitFor(() => {
      expect(screen.getByText(/you are a helpful assistant/i)).toBeInTheDocument()
    })
  })
})
