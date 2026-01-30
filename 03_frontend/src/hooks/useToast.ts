/**
 * useToast Hook
 *
 * State management hook for toast notifications.
 * Provides methods to show, dismiss, and manage toast messages.
 *
 * @example
 * ```tsx
 * function MyComponent() {
 *   const { toasts, showToast, dismissToast, showError } = useToast()
 *
 *   const handleSave = async () => {
 *     try {
 *       await saveData()
 *       showToast({ message: 'Saved!', type: 'success' })
 *     } catch (err) {
 *       showError(err.message)
 *     }
 *   }
 *
 *   return (
 *     <>
 *       <button onClick={handleSave}>Save</button>
 *       <ToastContainer toasts={toasts} onDismiss={dismissToast} />
 *     </>
 *   )
 * }
 * ```
 */
import { useState, useCallback, useRef, useEffect } from 'react'

/** Available toast notification types */
export type ToastType = 'info' | 'success' | 'warning' | 'error'

/** Data structure for a single toast notification */
export interface ToastData {
  /** Unique identifier for the toast */
  id: string
  /** Message to display */
  message: string
  /** Visual style/severity of the toast */
  type: ToastType
}

/** Options for showing a new toast */
export interface ShowToastOptions {
  /** Message to display */
  message: string
  /** Visual style/severity of the toast */
  type: ToastType
  /** Duration in ms before auto-dismiss. Set to 0 for persistent toast. Default: 5000 */
  duration?: number
}

/** Default auto-dismiss duration in milliseconds */
const DEFAULT_DURATION = 5000

/** Conflict error message for 409 responses */
const CONFLICT_MESSAGE = 'Someone else edited this prompt. Refresh to see changes.'

export function useToast() {
  const [toasts, setToasts] = useState<ToastData[]>([])
  const timersRef = useRef<Map<string, ReturnType<typeof setTimeout>>>(new Map())

  // Cleanup timers on unmount
  useEffect(() => {
    return () => {
      timersRef.current.forEach((timer) => clearTimeout(timer))
    }
  }, [])

  const dismissToast = useCallback((id: string) => {
    // Clear timer if exists
    const timer = timersRef.current.get(id)
    if (timer) {
      clearTimeout(timer)
      timersRef.current.delete(id)
    }

    setToasts((prev) => prev.filter((toast) => toast.id !== id))
  }, [])

  const showToast = useCallback(
    (options: ShowToastOptions) => {
      const id = `toast-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`
      const duration = options.duration ?? DEFAULT_DURATION

      const newToast: ToastData = {
        id,
        message: options.message,
        type: options.type,
      }

      setToasts((prev) => [...prev, newToast])

      // Set auto-dismiss timer if duration > 0
      if (duration > 0) {
        const timer = setTimeout(() => {
          dismissToast(id)
        }, duration)
        timersRef.current.set(id, timer)
      }
    },
    [dismissToast]
  )

  const showError = useCallback(
    (message: string) => {
      showToast({ message, type: 'error' })
    },
    [showToast]
  )

  /**
   * Show a 409 Conflict error toast with a specific message.
   * Toast is persistent until manually dismissed.
   */
  const showConflictError = useCallback(() => {
    showToast({
      message: CONFLICT_MESSAGE,
      type: 'warning',
      duration: 0, // Persistent until user dismisses
    })
  }, [showToast])

  const clearAll = useCallback(() => {
    // Clear all timers
    timersRef.current.forEach((timer) => clearTimeout(timer))
    timersRef.current.clear()

    setToasts([])
  }, [])

  return {
    toasts,
    showToast,
    dismissToast,
    showError,
    showConflictError,
    clearAll,
  }
}
