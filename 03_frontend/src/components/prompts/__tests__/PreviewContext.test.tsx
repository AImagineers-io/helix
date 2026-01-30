/**
 * PreviewContext Component Tests
 *
 * Tests for context variable editor in preview mode.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PreviewContext } from '../PreviewContext'

describe('PreviewContext', () => {
  const defaultProps = {
    promptContent: 'Hello {user_name}, your order {order_id} is ready.',
    onChange: vi.fn(),
  }

  describe('variable detection', () => {
    it('auto-detects variables from prompt content', () => {
      render(<PreviewContext {...defaultProps} />)

      expect(screen.getByLabelText(/user_name/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/order_id/i)).toBeInTheDocument()
    })

    it('handles prompts with no variables', () => {
      render(
        <PreviewContext
          promptContent="This is a simple prompt with no variables."
          onChange={vi.fn()}
        />
      )

      expect(screen.getByText(/no variables/i)).toBeInTheDocument()
    })

    it('handles multiple occurrences of same variable', () => {
      render(
        <PreviewContext
          promptContent="Hello {name}, {name} is a nice name."
          onChange={vi.fn()}
        />
      )

      // Should only show one input for {name}
      const inputs = screen.getAllByRole('textbox')
      expect(inputs).toHaveLength(1)
    })

    it('detects variables with underscores and numbers', () => {
      render(
        <PreviewContext
          promptContent="Value: {user_input_1}, {item_2_name}"
          onChange={vi.fn()}
        />
      )

      expect(screen.getByLabelText(/user_input_1/i)).toBeInTheDocument()
      expect(screen.getByLabelText(/item_2_name/i)).toBeInTheDocument()
    })
  })

  describe('initial values', () => {
    it('pre-fills inputs with example values', () => {
      render(<PreviewContext {...defaultProps} />)

      const userNameInput = screen.getByLabelText(/user_name/i) as HTMLInputElement
      const orderIdInput = screen.getByLabelText(/order_id/i) as HTMLInputElement

      // Should have some default example value
      expect(userNameInput.value).toBeTruthy()
      expect(orderIdInput.value).toBeTruthy()
    })

    it('uses provided initial values', () => {
      render(
        <PreviewContext
          {...defaultProps}
          initialValues={{ user_name: 'John', order_id: '12345' }}
        />
      )

      const userNameInput = screen.getByLabelText(/user_name/i) as HTMLInputElement
      expect(userNameInput.value).toBe('John')
    })
  })

  describe('editing values', () => {
    it('calls onChange when variable value is edited', () => {
      const onChange = vi.fn()
      render(<PreviewContext {...defaultProps} onChange={onChange} />)

      const userNameInput = screen.getByLabelText(/user_name/i)
      fireEvent.change(userNameInput, { target: { value: 'NewName' } })

      expect(onChange).toHaveBeenCalledWith(
        expect.objectContaining({ user_name: 'NewName' })
      )
    })

    it('maintains other values when one is changed', () => {
      const onChange = vi.fn()
      render(
        <PreviewContext
          {...defaultProps}
          onChange={onChange}
          initialValues={{ user_name: 'John', order_id: '12345' }}
        />
      )

      const userNameInput = screen.getByLabelText(/user_name/i)
      fireEvent.change(userNameInput, { target: { value: 'Jane' } })

      expect(onChange).toHaveBeenCalledWith({
        user_name: 'Jane',
        order_id: '12345',
      })
    })
  })

  describe('preview output', () => {
    it('shows interpolated prompt preview', () => {
      render(
        <PreviewContext
          {...defaultProps}
          initialValues={{ user_name: 'TestUser', order_id: 'ORD123' }}
        />
      )

      expect(screen.getByText(/TestUser/)).toBeInTheDocument()
      expect(screen.getByText(/ORD123/)).toBeInTheDocument()
    })
  })

  describe('JSON mode', () => {
    it('allows switching to JSON editor', () => {
      render(<PreviewContext {...defaultProps} />)

      const jsonToggle = screen.getByRole('button', { name: /json/i })
      fireEvent.click(jsonToggle)

      expect(screen.getByRole('textbox', { name: /json/i })).toBeInTheDocument()
    })

    it('allows editing values as JSON', () => {
      const onChange = vi.fn()
      render(<PreviewContext {...defaultProps} onChange={onChange} />)

      // Switch to JSON mode
      const jsonToggle = screen.getByRole('button', { name: /json/i })
      fireEvent.click(jsonToggle)

      const jsonInput = screen.getByRole('textbox', { name: /json/i })
      fireEvent.change(jsonInput, {
        target: { value: '{"user_name": "FromJSON", "order_id": "J123"}' },
      })

      expect(onChange).toHaveBeenCalledWith({
        user_name: 'FromJSON',
        order_id: 'J123',
      })
    })

    it('shows error for invalid JSON', () => {
      const { container } = render(<PreviewContext {...defaultProps} />)

      // Switch to JSON mode
      const jsonToggle = screen.getByRole('button', { name: /json/i })
      fireEvent.click(jsonToggle)

      const jsonInput = screen.getByRole('textbox', { name: /json/i })
      fireEvent.change(jsonInput, { target: { value: 'not valid json' } })

      // Check for the error message element specifically
      const errorElement = container.querySelector('.preview-context-json-error')
      expect(errorElement).toBeInTheDocument()
      expect(errorElement).toHaveTextContent(/invalid json/i)
    })
  })

  describe('reset functionality', () => {
    it('has a reset button', () => {
      render(<PreviewContext {...defaultProps} />)

      expect(screen.getByRole('button', { name: /reset/i })).toBeInTheDocument()
    })

    it('resets values to examples when reset is clicked', () => {
      const onChange = vi.fn()
      render(
        <PreviewContext
          {...defaultProps}
          onChange={onChange}
          initialValues={{ user_name: 'Custom', order_id: 'Custom' }}
        />
      )

      // Edit a value
      const userNameInput = screen.getByLabelText(/user_name/i)
      fireEvent.change(userNameInput, { target: { value: 'Changed' } })

      // Reset
      const resetButton = screen.getByRole('button', { name: /reset/i })
      fireEvent.click(resetButton)

      // Should call onChange with reset values
      expect(onChange).toHaveBeenLastCalledWith(
        expect.objectContaining({
          user_name: expect.any(String),
          order_id: expect.any(String),
        })
      )
    })
  })

  describe('accessibility', () => {
    it('labels are associated with inputs', () => {
      render(<PreviewContext {...defaultProps} />)

      const userNameInput = screen.getByLabelText(/user_name/i)
      expect(userNameInput).toHaveAttribute('id')
    })

    it('has a heading for the section', () => {
      render(<PreviewContext {...defaultProps} />)

      expect(screen.getByRole('heading', { name: /context/i })).toBeInTheDocument()
    })
  })
})
