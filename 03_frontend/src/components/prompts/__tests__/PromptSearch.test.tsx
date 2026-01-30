/**
 * PromptSearch Component Tests
 *
 * Tests for prompt list search and filter functionality.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, fireEvent, waitFor } from '@testing-library/react'
import { PromptSearch } from '../PromptSearch'

describe('PromptSearch', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('search input', () => {
    it('renders search input', () => {
      render(<PromptSearch onSearchChange={() => {}} onTypeChange={() => {}} />)

      expect(screen.getByPlaceholderText(/search/i)).toBeInTheDocument()
    })

    it('calls onSearchChange with debounced value', async () => {
      const onSearchChange = vi.fn()
      render(<PromptSearch onSearchChange={onSearchChange} onTypeChange={() => {}} />)

      const input = screen.getByPlaceholderText(/search/i)
      fireEvent.change(input, { target: { value: 'test query' } })

      // Should not be called immediately
      expect(onSearchChange).not.toHaveBeenCalled()

      // Advance timers by debounce delay
      vi.advanceTimersByTime(300)

      expect(onSearchChange).toHaveBeenCalledWith('test query')
    })

    it('debounces rapid input changes', () => {
      const onSearchChange = vi.fn()
      render(<PromptSearch onSearchChange={onSearchChange} onTypeChange={() => {}} />)

      const input = screen.getByPlaceholderText(/search/i)

      // Type multiple times rapidly
      fireEvent.change(input, { target: { value: 'a' } })
      vi.advanceTimersByTime(100)
      fireEvent.change(input, { target: { value: 'ab' } })
      vi.advanceTimersByTime(100)
      fireEvent.change(input, { target: { value: 'abc' } })
      vi.advanceTimersByTime(300)

      // Should only be called once with final value
      expect(onSearchChange).toHaveBeenCalledTimes(1)
      expect(onSearchChange).toHaveBeenCalledWith('abc')
    })

    it('clears search when clear button is clicked', () => {
      const onSearchChange = vi.fn()
      render(
        <PromptSearch
          onSearchChange={onSearchChange}
          onTypeChange={() => {}}
          initialSearch="existing"
        />
      )

      // Find and click clear button
      const clearButton = screen.getByRole('button', { name: /clear search/i })
      fireEvent.click(clearButton)

      // Should call immediately with empty string
      expect(onSearchChange).toHaveBeenCalledWith('')
    })

    it('shows clear button only when search has value', () => {
      render(
        <PromptSearch onSearchChange={() => {}} onTypeChange={() => {}} />
      )

      // Should not show clear button initially
      expect(screen.queryByRole('button', { name: /clear search/i })).not.toBeInTheDocument()

      // Type something in the search
      const input = screen.getByPlaceholderText(/search/i)
      fireEvent.change(input, { target: { value: 'test' } })

      // Now clear button should appear
      expect(screen.getByRole('button', { name: /clear search/i })).toBeInTheDocument()
    })
  })

  describe('type filter', () => {
    it('renders type filter dropdown', () => {
      render(<PromptSearch onSearchChange={() => {}} onTypeChange={() => {}} />)

      expect(screen.getByRole('combobox', { name: /type/i })).toBeInTheDocument()
    })

    it('includes "All Types" option', () => {
      render(<PromptSearch onSearchChange={() => {}} onTypeChange={() => {}} />)

      const select = screen.getByRole('combobox', { name: /type/i })
      expect(select).toContainHTML('All Types')
    })

    it('calls onTypeChange when selection changes', () => {
      const onTypeChange = vi.fn()
      render(
        <PromptSearch
          onSearchChange={() => {}}
          onTypeChange={onTypeChange}
          promptTypes={['system', 'user', 'assistant']}
        />
      )

      const select = screen.getByRole('combobox', { name: /type/i })
      fireEvent.change(select, { target: { value: 'system' } })

      expect(onTypeChange).toHaveBeenCalledWith('system')
    })

    it('calls onTypeChange with empty string for "All Types"', () => {
      const onTypeChange = vi.fn()
      render(
        <PromptSearch
          onSearchChange={() => {}}
          onTypeChange={onTypeChange}
          promptTypes={['system', 'user']}
          initialType="system"
        />
      )

      const select = screen.getByRole('combobox', { name: /type/i })
      fireEvent.change(select, { target: { value: '' } })

      expect(onTypeChange).toHaveBeenCalledWith('')
    })

    it('renders provided prompt types', () => {
      render(
        <PromptSearch
          onSearchChange={() => {}}
          onTypeChange={() => {}}
          promptTypes={['system', 'user', 'assistant']}
        />
      )

      const select = screen.getByRole('combobox', { name: /type/i })
      expect(select).toContainHTML('system')
      expect(select).toContainHTML('user')
      expect(select).toContainHTML('assistant')
    })
  })

  describe('initial values', () => {
    it('initializes search input with provided value', () => {
      render(
        <PromptSearch
          onSearchChange={() => {}}
          onTypeChange={() => {}}
          initialSearch="initial query"
        />
      )

      expect(screen.getByPlaceholderText(/search/i)).toHaveValue('initial query')
    })

    it('initializes type filter with provided value', () => {
      render(
        <PromptSearch
          onSearchChange={() => {}}
          onTypeChange={() => {}}
          promptTypes={['system', 'user']}
          initialType="system"
        />
      )

      expect(screen.getByRole('combobox', { name: /type/i })).toHaveValue('system')
    })
  })

  describe('accessibility', () => {
    it('search input has accessible label', () => {
      render(<PromptSearch onSearchChange={() => {}} onTypeChange={() => {}} />)

      expect(screen.getByLabelText(/search prompts/i)).toBeInTheDocument()
    })

    it('type filter has accessible label', () => {
      render(<PromptSearch onSearchChange={() => {}} onTypeChange={() => {}} />)

      expect(screen.getByLabelText(/filter by type/i)).toBeInTheDocument()
    })
  })
})
