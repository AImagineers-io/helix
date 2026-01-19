/**
 * PromptActions Component
 *
 * Provides publish and rollback actions for prompt versions.
 */

interface PromptActionsProps {
  /** Currently selected version number */
  selectedVersionNumber: number
  /** Currently active version number */
  activeVersionNumber: number
  /** Callback to publish selected version */
  onPublish: () => void
  /** Callback to rollback to previous version */
  onRollback: () => void
  /** Loading state for publish operation */
  isPublishing?: boolean
  /** Loading state for rollback operation */
  isRollingBack?: boolean
}

export function PromptActions({
  selectedVersionNumber,
  activeVersionNumber,
  onPublish,
  onRollback,
  isPublishing = false,
  isRollingBack = false,
}: PromptActionsProps) {
  const isAlreadyActive = selectedVersionNumber === activeVersionNumber
  const isLoading = isPublishing || isRollingBack

  return (
    <div className="prompt-actions">
      <button
        onClick={onPublish}
        disabled={isAlreadyActive || isLoading}
        className="publish-button"
        aria-label="Publish selected version"
      >
        {isPublishing ? 'Publishing...' : 'Publish'}
      </button>
      <button
        onClick={onRollback}
        disabled={isLoading}
        className="rollback-button"
        aria-label="Rollback to previous version"
      >
        {isRollingBack ? 'Rolling back...' : 'Rollback'}
      </button>
    </div>
  )
}
