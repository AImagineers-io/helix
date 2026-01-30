/**
 * ErrorBoundary Component Tests
 *
 * Tests for global error boundary that catches render errors
 * and provides user-friendly recovery options.
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { ErrorBoundary } from '../ErrorBoundary'

// Component that throws an error for testing
function ThrowingComponent({ shouldThrow }: { shouldThrow: boolean }) {
  if (shouldThrow) {
    throw new Error('Test render error')
  }
  return <div>Content rendered successfully</div>
}

// Controllable throwing component using a ref
let shouldThrowRef = false
function ControllableThrowingComponent() {
  if (shouldThrowRef) {
    throw new Error('Controlled test error')
  }
  return <div>Content rendered successfully</div>
}

// Suppress console.error for expected errors during tests
const originalError = console.error
beforeEach(() => {
  console.error = vi.fn()
})

afterEach(() => {
  console.error = originalError
})

describe('ErrorBoundary', () => {
  describe('when no error occurs', () => {
    it('renders children normally', () => {
      render(
        <ErrorBoundary>
          <div>Child content</div>
        </ErrorBoundary>
      )

      expect(screen.getByText('Child content')).toBeInTheDocument()
    })
  })

  describe('when a render error occurs', () => {
    it('displays friendly error message', () => {
      render(
        <ErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()
    })

    it('displays retry button', () => {
      render(
        <ErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument()
    })

    it('displays copy error details button', () => {
      render(
        <ErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByRole('button', { name: /copy error details/i })).toBeInTheDocument()
    })

    it('resets error state when retry is clicked', () => {
      // Set to throw initially
      shouldThrowRef = true

      render(
        <ErrorBoundary>
          <ControllableThrowingComponent />
        </ErrorBoundary>
      )

      expect(screen.getByText('Something went wrong')).toBeInTheDocument()

      // Stop throwing before clicking retry
      shouldThrowRef = false

      // Click retry to reset error state and re-render children
      fireEvent.click(screen.getByRole('button', { name: /retry/i }))

      expect(screen.getByText('Content rendered successfully')).toBeInTheDocument()
    })

    it('copies error details to clipboard when copy button is clicked', async () => {
      const mockClipboard = {
        writeText: vi.fn().mockResolvedValue(undefined),
      }
      Object.assign(navigator, { clipboard: mockClipboard })

      render(
        <ErrorBoundary>
          <ThrowingComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      fireEvent.click(screen.getByRole('button', { name: /copy error details/i }))

      expect(mockClipboard.writeText).toHaveBeenCalled()
      expect(mockClipboard.writeText.mock.calls[0][0]).toContain('Test render error')
    })
  })

  describe('with custom fallback', () => {
    it('renders custom fallback UI when provided', () => {
      render(
        <ErrorBoundary fallback={<div>Custom error UI</div>}>
          <ThrowingComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(screen.getByText('Custom error UI')).toBeInTheDocument()
    })
  })

  describe('with onError callback', () => {
    it('calls onError callback with error info', () => {
      const onError = vi.fn()

      render(
        <ErrorBoundary onError={onError}>
          <ThrowingComponent shouldThrow={true} />
        </ErrorBoundary>
      )

      expect(onError).toHaveBeenCalledWith(
        expect.any(Error),
        expect.objectContaining({
          componentStack: expect.any(String),
        })
      )
    })
  })
})
