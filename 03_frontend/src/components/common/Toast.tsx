/**
 * Toast Components
 *
 * Toast notification display components for showing feedback messages.
 * Use with the useToast hook for state management.
 *
 * @example
 * ```tsx
 * function App() {
 *   const { toasts, dismissToast } = useToast()
 *   return <ToastContainer toasts={toasts} onDismiss={dismissToast} />
 * }
 * ```
 */
import type { ToastData } from '../../hooks/useToast'

/** Props for individual Toast component */
export interface ToastProps {
  /** Toast data to display */
  toast: ToastData
  /** Callback when toast is dismissed */
  onDismiss: (id: string) => void
}

/**
 * Individual toast notification.
 * Displays message with type-based styling and dismiss button.
 */
export function Toast({ toast, onDismiss }: ToastProps) {
  const handleDismiss = () => onDismiss(toast.id)

  return (
    <div className={`toast toast--${toast.type}`} role="alert">
      <span className="toast-message">{toast.message}</span>
      <button
        onClick={handleDismiss}
        className="toast-dismiss"
        aria-label="Dismiss"
      >
        ×
      </button>
    </div>
  )
}

/** Props for ToastContainer component */
export interface ToastContainerProps {
  /** Array of toasts to display */
  toasts: ToastData[]
  /** Callback when any toast is dismissed */
  onDismiss: (id: string) => void
}

/**
 * Container for rendering multiple toast notifications.
 * Position this component at a fixed location in your app (e.g., top-right).
 */
export function ToastContainer({ toasts, onDismiss }: ToastContainerProps) {
  return (
    <div className="toast-container">
      {toasts.map((toast) => (
        <Toast key={toast.id} toast={toast} onDismiss={onDismiss} />
      ))}
    </div>
  )
}
