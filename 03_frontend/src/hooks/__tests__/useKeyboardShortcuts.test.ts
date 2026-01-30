/**
 * useKeyboardShortcuts Hook Tests
 *
 * Tests for keyboard shortcut handling.
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { renderHook } from '@testing-library/react'
import { useKeyboardShortcuts } from '../useKeyboardShortcuts'

describe('useKeyboardShortcuts', () => {
  let addEventListenerSpy: ReturnType<typeof vi.spyOn>
  let removeEventListenerSpy: ReturnType<typeof vi.spyOn>

  beforeEach(() => {
    addEventListenerSpy = vi.spyOn(document, 'addEventListener')
    removeEventListenerSpy = vi.spyOn(document, 'removeEventListener')
  })

  afterEach(() => {
    addEventListenerSpy.mockRestore()
    removeEventListenerSpy.mockRestore()
  })

  const dispatchKeyEvent = (key: string, modifiers: Partial<KeyboardEventInit> = {}) => {
    const event = new KeyboardEvent('keydown', {
      key,
      bubbles: true,
      ...modifiers,
    })
    document.dispatchEvent(event)
  }

  describe('setup and cleanup', () => {
    it('registers keydown listener on mount', () => {
      renderHook(() => useKeyboardShortcuts({}))

      expect(addEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
    })

    it('removes keydown listener on unmount', () => {
      const { unmount } = renderHook(() => useKeyboardShortcuts({}))

      unmount()

      expect(removeEventListenerSpy).toHaveBeenCalledWith('keydown', expect.any(Function))
    })
  })

  describe('Ctrl+S / Cmd+S - Save', () => {
    it('calls onSave when Ctrl+S is pressed', () => {
      const onSave = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onSave }))

      dispatchKeyEvent('s', { ctrlKey: true })

      expect(onSave).toHaveBeenCalled()
    })

    it('calls onSave when Cmd+S is pressed (Mac)', () => {
      const onSave = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onSave }))

      dispatchKeyEvent('s', { metaKey: true })

      expect(onSave).toHaveBeenCalled()
    })

    it('does not call onSave without modifier', () => {
      const onSave = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onSave }))

      dispatchKeyEvent('s')

      expect(onSave).not.toHaveBeenCalled()
    })

    it('prevents default browser behavior for save shortcut', () => {
      const onSave = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onSave }))

      const event = new KeyboardEvent('keydown', {
        key: 's',
        ctrlKey: true,
        bubbles: true,
        cancelable: true,
      })
      const preventDefaultSpy = vi.spyOn(event, 'preventDefault')

      document.dispatchEvent(event)

      expect(preventDefaultSpy).toHaveBeenCalled()
    })
  })

  describe('Ctrl+Enter / Cmd+Enter - Publish', () => {
    it('calls onPublish when Ctrl+Enter is pressed', () => {
      const onPublish = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onPublish }))

      dispatchKeyEvent('Enter', { ctrlKey: true })

      expect(onPublish).toHaveBeenCalled()
    })

    it('calls onPublish when Cmd+Enter is pressed (Mac)', () => {
      const onPublish = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onPublish }))

      dispatchKeyEvent('Enter', { metaKey: true })

      expect(onPublish).toHaveBeenCalled()
    })

    it('does not call onPublish without modifier', () => {
      const onPublish = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onPublish }))

      dispatchKeyEvent('Enter')

      expect(onPublish).not.toHaveBeenCalled()
    })
  })

  describe('Escape - Cancel/Close', () => {
    it('calls onCancel when Escape is pressed', () => {
      const onCancel = vi.fn()
      renderHook(() => useKeyboardShortcuts({ onCancel }))

      dispatchKeyEvent('Escape')

      expect(onCancel).toHaveBeenCalled()
    })
  })

  describe('disabled state', () => {
    it('does not trigger shortcuts when disabled', () => {
      const onSave = vi.fn()
      const onPublish = vi.fn()
      const onCancel = vi.fn()

      renderHook(() =>
        useKeyboardShortcuts({
          onSave,
          onPublish,
          onCancel,
          disabled: true,
        })
      )

      dispatchKeyEvent('s', { ctrlKey: true })
      dispatchKeyEvent('Enter', { ctrlKey: true })
      dispatchKeyEvent('Escape')

      expect(onSave).not.toHaveBeenCalled()
      expect(onPublish).not.toHaveBeenCalled()
      expect(onCancel).not.toHaveBeenCalled()
    })
  })

  describe('callback updates', () => {
    it('uses latest callback reference', () => {
      const onSave1 = vi.fn()
      const onSave2 = vi.fn()

      const { rerender } = renderHook(
        ({ onSave }) => useKeyboardShortcuts({ onSave }),
        { initialProps: { onSave: onSave1 } }
      )

      rerender({ onSave: onSave2 })

      dispatchKeyEvent('s', { ctrlKey: true })

      expect(onSave1).not.toHaveBeenCalled()
      expect(onSave2).toHaveBeenCalled()
    })
  })

  describe('multiple shortcuts', () => {
    it('handles all shortcuts independently', () => {
      const onSave = vi.fn()
      const onPublish = vi.fn()
      const onCancel = vi.fn()

      renderHook(() =>
        useKeyboardShortcuts({
          onSave,
          onPublish,
          onCancel,
        })
      )

      dispatchKeyEvent('s', { ctrlKey: true })
      expect(onSave).toHaveBeenCalledTimes(1)

      dispatchKeyEvent('Enter', { ctrlKey: true })
      expect(onPublish).toHaveBeenCalledTimes(1)

      dispatchKeyEvent('Escape')
      expect(onCancel).toHaveBeenCalledTimes(1)

      // Verify no cross-triggering
      expect(onSave).toHaveBeenCalledTimes(1)
      expect(onPublish).toHaveBeenCalledTimes(1)
      expect(onCancel).toHaveBeenCalledTimes(1)
    })
  })
})
