/**
 * useKeyboardShortcuts Hook
 *
 * Handles keyboard shortcuts for common editor actions.
 * Works cross-platform with both Ctrl (Windows/Linux) and Cmd (Mac) modifiers.
 *
 * Supported shortcuts:
 * - Ctrl+S / Cmd+S: Save draft
 * - Ctrl+Enter / Cmd+Enter: Publish
 * - Escape: Cancel/Close
 *
 * @example
 * ```tsx
 * function PromptEditor() {
 *   const handleSave = () => console.log('Saving...')
 *   const handlePublish = () => console.log('Publishing...')
 *   const handleCancel = () => console.log('Cancelled')
 *
 *   useKeyboardShortcuts({
 *     onSave: handleSave,
 *     onPublish: handlePublish,
 *     onCancel: handleCancel,
 *   })
 *
 *   return <textarea />
 * }
 * ```
 */
import { useEffect, useRef } from 'react'

/** Configuration options for keyboard shortcuts */
export interface KeyboardShortcutsOptions {
  /** Handler for Ctrl+S / Cmd+S (Save draft) */
  onSave?: () => void
  /** Handler for Ctrl+Enter / Cmd+Enter (Publish) */
  onPublish?: () => void
  /** Handler for Escape (Cancel/Close) */
  onCancel?: () => void
  /** Disable all shortcuts (useful during loading states) */
  disabled?: boolean
}

/** Check if a modifier key (Ctrl or Cmd) is pressed */
const hasModifier = (event: KeyboardEvent): boolean => {
  return event.ctrlKey || event.metaKey
}

/**
 * Hook for handling common keyboard shortcuts in the editor.
 *
 * @param options - Configuration object with callback handlers
 */
export function useKeyboardShortcuts({
  onSave,
  onPublish,
  onCancel,
  disabled = false,
}: KeyboardShortcutsOptions): void {
  // Use refs to always have latest callbacks without re-registering listener
  const callbacksRef = useRef({ onSave, onPublish, onCancel })

  // Keep refs in sync with props
  useEffect(() => {
    callbacksRef.current = { onSave, onPublish, onCancel }
  }, [onSave, onPublish, onCancel])

  useEffect(() => {
    const handleKeyDown = (event: KeyboardEvent) => {
      if (disabled) return

      const { onSave, onPublish, onCancel } = callbacksRef.current

      // Ctrl+S or Cmd+S - Save draft
      if (hasModifier(event) && event.key === 's') {
        if (onSave) {
          event.preventDefault()
          onSave()
        }
        return
      }

      // Ctrl+Enter or Cmd+Enter - Publish
      if (hasModifier(event) && event.key === 'Enter') {
        if (onPublish) {
          event.preventDefault()
          onPublish()
        }
        return
      }

      // Escape - Cancel/Close
      if (event.key === 'Escape') {
        if (onCancel) {
          event.preventDefault()
          onCancel()
        }
      }
    }

    document.addEventListener('keydown', handleKeyDown)

    return () => {
      document.removeEventListener('keydown', handleKeyDown)
    }
  }, [disabled])
}
