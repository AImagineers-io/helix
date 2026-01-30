/**
 * ErrorBoundary Component
 *
 * Global error boundary that catches render errors and displays
 * a user-friendly error message with recovery options.
 *
 * @example
 * ```tsx
 * // Basic usage
 * <ErrorBoundary>
 *   <App />
 * </ErrorBoundary>
 *
 * // With custom fallback
 * <ErrorBoundary fallback={<CustomErrorPage />}>
 *   <App />
 * </ErrorBoundary>
 *
 * // With error logging
 * <ErrorBoundary onError={(error, info) => logToService(error, info)}>
 *   <App />
 * </ErrorBoundary>
 * ```
 */
import { Component, ReactNode, ErrorInfo } from 'react'

/**
 * Props for the ErrorBoundary component.
 */
export interface ErrorBoundaryProps {
  /** Child components to render */
  children: ReactNode
  /** Optional custom fallback UI to display when an error occurs */
  fallback?: ReactNode
  /** Optional callback invoked when an error is caught */
  onError?: (error: Error, errorInfo: ErrorInfo) => void
}

interface ErrorBoundaryState {
  hasError: boolean
  error: Error | null
  errorInfo: ErrorInfo | null
}

const INITIAL_STATE: ErrorBoundaryState = {
  hasError: false,
  error: null,
  errorInfo: null,
}

/**
 * ErrorBoundary catches JavaScript errors anywhere in its child component tree,
 * logs those errors, and displays a fallback UI instead of the component tree that crashed.
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props)
    this.state = INITIAL_STATE
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    return { hasError: true, error }
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    this.setState({ errorInfo })
    this.props.onError?.(error, errorInfo)
  }

  /**
   * Reset the error state to allow retry.
   */
  private handleRetry = (): void => {
    this.setState(INITIAL_STATE)
  }

  /**
   * Copy error details to clipboard for debugging/support.
   */
  private handleCopyError = async (): Promise<void> => {
    const { error, errorInfo } = this.state
    const errorDetails = this.formatErrorDetails(error, errorInfo)
    await navigator.clipboard.writeText(errorDetails)
  }

  /**
   * Format error information into a readable string.
   */
  private formatErrorDetails(error: Error | null, errorInfo: ErrorInfo | null): string {
    return [
      `Error: ${error?.message || 'Unknown error'}`,
      `Stack: ${error?.stack || 'No stack trace'}`,
      `Component Stack: ${errorInfo?.componentStack || 'No component stack'}`,
    ].join('\n\n')
  }

  /**
   * Render the default error UI.
   */
  private renderErrorUI(): ReactNode {
    const { error } = this.state

    return (
      <div className="error-boundary">
        <div className="error-boundary-content">
          <h2>Something went wrong</h2>
          <p className="error-message">{error?.message}</p>
          <div className="error-actions">
            <button onClick={this.handleRetry} className="retry-button">
              Retry
            </button>
            <button onClick={this.handleCopyError} className="copy-error-button">
              Copy Error Details
            </button>
          </div>
        </div>
      </div>
    )
  }

  render(): ReactNode {
    const { hasError } = this.state
    const { children, fallback } = this.props

    if (hasError) {
      return fallback ?? this.renderErrorUI()
    }

    return children
  }
}
