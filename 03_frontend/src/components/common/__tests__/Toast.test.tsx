/**
 * Toast Component Tests
 *
 * Tests for toast notification display component.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { Toast, ToastContainer } from '../Toast'
import type { ToastData } from '../../../hooks/useToast'

describe('Toast', () => {
  const mockToast: ToastData = {
    id: 'toast-1',
    message: 'Test notification',
    type: 'info',
  }

  it('renders toast message', () => {
    render(<Toast toast={mockToast} onDismiss={() => {}} />)

    expect(screen.getByText('Test notification')).toBeInTheDocument()
  })

  it('renders dismiss button', () => {
    render(<Toast toast={mockToast} onDismiss={() => {}} />)

    expect(screen.getByRole('button', { name: /dismiss/i })).toBeInTheDocument()
  })

  it('calls onDismiss when dismiss button is clicked', () => {
    const onDismiss = vi.fn()
    render(<Toast toast={mockToast} onDismiss={onDismiss} />)

    fireEvent.click(screen.getByRole('button', { name: /dismiss/i }))

    expect(onDismiss).toHaveBeenCalledWith('toast-1')
  })

  describe('toast types', () => {
    it('applies error class for error type', () => {
      const errorToast: ToastData = { ...mockToast, type: 'error' }
      const { container } = render(<Toast toast={errorToast} onDismiss={() => {}} />)

      expect(container.querySelector('.toast--error')).toBeInTheDocument()
    })

    it('applies success class for success type', () => {
      const successToast: ToastData = { ...mockToast, type: 'success' }
      const { container } = render(<Toast toast={successToast} onDismiss={() => {}} />)

      expect(container.querySelector('.toast--success')).toBeInTheDocument()
    })

    it('applies warning class for warning type', () => {
      const warningToast: ToastData = { ...mockToast, type: 'warning' }
      const { container } = render(<Toast toast={warningToast} onDismiss={() => {}} />)

      expect(container.querySelector('.toast--warning')).toBeInTheDocument()
    })

    it('applies info class for info type', () => {
      const infoToast: ToastData = { ...mockToast, type: 'info' }
      const { container } = render(<Toast toast={infoToast} onDismiss={() => {}} />)

      expect(container.querySelector('.toast--info')).toBeInTheDocument()
    })
  })
})

describe('ToastContainer', () => {
  it('renders multiple toasts', () => {
    const toasts: ToastData[] = [
      { id: '1', message: 'First toast', type: 'info' },
      { id: '2', message: 'Second toast', type: 'error' },
    ]

    render(<ToastContainer toasts={toasts} onDismiss={() => {}} />)

    expect(screen.getByText('First toast')).toBeInTheDocument()
    expect(screen.getByText('Second toast')).toBeInTheDocument()
  })

  it('renders empty when no toasts', () => {
    const { container } = render(<ToastContainer toasts={[]} onDismiss={() => {}} />)

    expect(container.querySelector('.toast-container')).toBeInTheDocument()
    expect(container.querySelectorAll('.toast')).toHaveLength(0)
  })

  it('passes correct ID to onDismiss', () => {
    const onDismiss = vi.fn()
    const toasts: ToastData[] = [{ id: 'test-id', message: 'Test', type: 'info' }]

    render(<ToastContainer toasts={toasts} onDismiss={onDismiss} />)

    fireEvent.click(screen.getByRole('button', { name: /dismiss/i }))

    expect(onDismiss).toHaveBeenCalledWith('test-id')
  })
})
