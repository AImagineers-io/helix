/**
 * useUnsavedChanges Hook Tests
 *
 * Tests for navigation blocking when there are unsaved changes.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook, act } from '@testing-library/react'
import { useUnsavedChanges } from '../useUnsavedChanges'

describe('useUnsavedChanges', () => {
  let addEventListenerSpy: ReturnType<typeof vi.spyOn>
  let removeEventListenerSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    addEventListenerSpy = vi.spyOn(window, 'addEventListener')
    removeEventListenerSpy = vi.spyOn(window, 'removeEventListener')
  })

  afterEach(() => {
    addEventListenerSpy.mockRestore()
    removeEventListenerSpy.mockRestore()
  })

  describe('initial state', () => {
    it('starts with no unsaved changes', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      expect(result.current.hasUnsavedChanges).toBe(false)
    })

    it('does not block navigation initially', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      expect(result.current.shouldBlock).toBe(false)
    })
  })

  describe('setHasUnsavedChanges', () => {
    it('updates hasUnsavedChanges state', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      expect(result.current.hasUnsavedChanges).toBe(true)
    })

    it('enables blocking when there are unsaved changes', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      expect(result.current.shouldBlock).toBe(true)
    })

    it('disables blocking when changes are saved', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      expect(result.current.shouldBlock).toBe(true)

      act(() => {
        result.current.setHasUnsavedChanges(false)
      })

      expect(result.current.shouldBlock).toBe(false)
    })
  })

  describe('beforeunload event', () => {
    it('adds beforeunload listener when there are unsaved changes', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      expect(addEventListenerSpy).toHaveBeenCalledWith(
        'beforeunload',
        expect.any(Function)
      )
    })

    it('removes beforeunload listener when changes are saved', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      act(() => {
        result.current.setHasUnsavedChanges(false)
      })

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'beforeunload',
        expect.any(Function)
      )
    })

    it('removes listener on unmount', () => {
      const { result, unmount } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith(
        'beforeunload',
        expect.any(Function)
      )
    })

    it('prevents unload when there are unsaved changes', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      // Get the beforeunload handler
      const beforeunloadHandler = addEventListenerSpy.mock.calls.find(
        (call) => call[0] === 'beforeunload'
      )?.[1] as EventListener

      const event = new Event('beforeunload') as BeforeUnloadEvent
      Object.defineProperty(event, 'returnValue', {
        writable: true,
        value: '',
      })

      beforeunloadHandler(event)

      expect(event.returnValue).toBe('You have unsaved changes. Are you sure you want to leave?')
    })
  })

  describe('resetChanges', () => {
    it('clears unsaved changes state', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      act(() => {
        result.current.setHasUnsavedChanges(true)
      })

      expect(result.current.hasUnsavedChanges).toBe(true)

      act(() => {
        result.current.resetChanges()
      })

      expect(result.current.hasUnsavedChanges).toBe(false)
      expect(result.current.shouldBlock).toBe(false)
    })
  })

  describe('confirmMessage', () => {
    it('returns the warning message', () => {
      const { result } = renderHook(() => useUnsavedChanges())

      expect(result.current.confirmMessage).toBe(
        'You have unsaved changes. Are you sure you want to leave?'
      )
    })
  })
})
