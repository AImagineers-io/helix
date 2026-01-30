/**
 * useToast Hook Tests
 *
 * Tests for toast notification state management hook.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useToast } from '../useToast'

describe('useToast', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    vi.useRealTimers()
  })

  describe('showToast', () => {
    it('adds a toast to the list', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Test message', type: 'info' })
      })

      expect(result.current.toasts).toHaveLength(1)
      expect(result.current.toasts[0].message).toBe('Test message')
      expect(result.current.toasts[0].type).toBe('info')
    })

    it('assigns unique IDs to each toast', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'First', type: 'info' })
        result.current.showToast({ message: 'Second', type: 'info' })
      })

      expect(result.current.toasts[0].id).not.toBe(result.current.toasts[1].id)
    })

    it('supports error type toasts', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Error occurred', type: 'error' })
      })

      expect(result.current.toasts[0].type).toBe('error')
    })

    it('supports success type toasts', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Operation succeeded', type: 'success' })
      })

      expect(result.current.toasts[0].type).toBe('success')
    })

    it('supports warning type toasts', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Warning', type: 'warning' })
      })

      expect(result.current.toasts[0].type).toBe('warning')
    })
  })

  describe('dismissToast', () => {
    it('removes toast by ID', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Test', type: 'info' })
      })

      const toastId = result.current.toasts[0].id

      act(() => {
        result.current.dismissToast(toastId)
      })

      expect(result.current.toasts).toHaveLength(0)
    })

    it('only removes the specified toast', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'First', type: 'info' })
        result.current.showToast({ message: 'Second', type: 'info' })
      })

      const firstToastId = result.current.toasts[0].id

      act(() => {
        result.current.dismissToast(firstToastId)
      })

      expect(result.current.toasts).toHaveLength(1)
      expect(result.current.toasts[0].message).toBe('Second')
    })
  })

  describe('auto-dismiss', () => {
    it('automatically dismisses toast after default duration', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Auto dismiss', type: 'info' })
      })

      expect(result.current.toasts).toHaveLength(1)

      act(() => {
        vi.advanceTimersByTime(5000) // Default duration
      })

      expect(result.current.toasts).toHaveLength(0)
    })

    it('respects custom duration', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Custom duration', type: 'info', duration: 3000 })
      })

      act(() => {
        vi.advanceTimersByTime(2999)
      })

      expect(result.current.toasts).toHaveLength(1)

      act(() => {
        vi.advanceTimersByTime(1)
      })

      expect(result.current.toasts).toHaveLength(0)
    })

    it('does not auto-dismiss when duration is 0 (persistent)', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'Persistent', type: 'error', duration: 0 })
      })

      act(() => {
        vi.advanceTimersByTime(60000) // Long time
      })

      expect(result.current.toasts).toHaveLength(1)
    })
  })

  describe('showError helper', () => {
    it('shows error toast with message', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showError('Something went wrong')
      })

      expect(result.current.toasts[0].type).toBe('error')
      expect(result.current.toasts[0].message).toBe('Something went wrong')
    })
  })

  describe('showConflictError helper', () => {
    it('shows specific 409 conflict message', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showConflictError()
      })

      expect(result.current.toasts[0].type).toBe('warning')
      expect(result.current.toasts[0].message).toContain('Someone else edited')
    })
  })

  describe('clearAll', () => {
    it('removes all toasts', () => {
      const { result } = renderHook(() => useToast())

      act(() => {
        result.current.showToast({ message: 'First', type: 'info' })
        result.current.showToast({ message: 'Second', type: 'error' })
        result.current.showToast({ message: 'Third', type: 'success' })
      })

      expect(result.current.toasts).toHaveLength(3)

      act(() => {
        result.current.clearAll()
      })

      expect(result.current.toasts).toHaveLength(0)
    })
  })
})
