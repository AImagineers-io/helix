/**
 * useUnsavedChanges Hook
 *
 * Manages unsaved changes state and prevents navigation when there are
 * pending changes. Uses beforeunload event for browser navigation.
 *
 * @example
 * ```tsx
 * function PromptEditor() {
 *   const [content, setContent] = useState('')
 *   const { hasUnsavedChanges, setHasUnsavedChanges, resetChanges } = useUnsavedChanges()
 *
 *   const handleChange = (newContent: string) => {
 *     setContent(newContent)
 *     setHasUnsavedChanges(true)
 *   }
 *
 *   const handleSave = async () => {
 *     await saveContent(content)
 *     resetChanges() // Clears unsaved state after save
 *   }
 *
 *   return (
 *     <textarea value={content} onChange={(e) => handleChange(e.target.value)} />
 *   )
 * }
 * ```
 */
import { useState, useCallback, useEffect, useRef } from 'react'

/** Warning message shown when user tries to navigate away with unsaved changes */
const CONFIRM_MESSAGE = 'You have unsaved changes. Are you sure you want to leave?'

/** Return type for useUnsavedChanges hook */
export interface UseUnsavedChangesReturn {
  /** Whether there are currently unsaved changes */
  hasUnsavedChanges: boolean
  /** Set the unsaved changes state */
  setHasUnsavedChanges: (value: boolean) => void
  /** Whether navigation should be blocked (alias for hasUnsavedChanges) */
  shouldBlock: boolean
  /** Reset the unsaved changes state to false */
  resetChanges: () => void
  /** The confirmation message shown to users */
  confirmMessage: string
}

/**
 * Hook for managing unsaved changes and navigation blocking.
 *
 * @returns Object with state and methods for managing unsaved changes
 */
export function useUnsavedChanges(): UseUnsavedChangesReturn {
  const [hasUnsavedChanges, setHasUnsavedChanges] = useState(false)
  const beforeUnloadHandlerRef = useRef<((e: BeforeUnloadEvent) => void) | null>(null)

  // Create the beforeunload handler
  const handleBeforeUnload = useCallback((e: BeforeUnloadEvent) => {
    e.preventDefault()
    e.returnValue = CONFIRM_MESSAGE
    return CONFIRM_MESSAGE
  }, [])

  // Manage beforeunload event listener
  useEffect(() => {
    if (hasUnsavedChanges) {
      beforeUnloadHandlerRef.current = handleBeforeUnload
      window.addEventListener('beforeunload', handleBeforeUnload)
    } else {
      if (beforeUnloadHandlerRef.current) {
        window.removeEventListener('beforeunload', beforeUnloadHandlerRef.current)
        beforeUnloadHandlerRef.current = null
      }
    }

    // Cleanup on unmount
    return () => {
      if (beforeUnloadHandlerRef.current) {
        window.removeEventListener('beforeunload', beforeUnloadHandlerRef.current)
      }
    }
  }, [hasUnsavedChanges, handleBeforeUnload])

  const resetChanges = useCallback(() => {
    setHasUnsavedChanges(false)
  }, [])

  return {
    hasUnsavedChanges,
    setHasUnsavedChanges,
    shouldBlock: hasUnsavedChanges,
    resetChanges,
    confirmMessage: CONFIRM_MESSAGE,
  }
}
