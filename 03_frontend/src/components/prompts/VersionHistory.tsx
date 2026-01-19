/**
 * VersionHistory Component
 *
 * Displays version history sidebar for prompt templates.
 */
import { PromptVersion } from '../../services/prompts-api'
import { VersionItem } from './VersionItem'

interface VersionHistoryProps {
  /** Array of prompt versions to display */
  versions: PromptVersion[]
  /** Loading state indicator */
  isLoading: boolean
  /** Callback when a version is selected */
  onVersionSelect: (version: PromptVersion) => void
}

export function VersionHistory({ versions, isLoading, onVersionSelect }: VersionHistoryProps) {
  if (isLoading) {
    return (
      <div className="version-history">
        <div className="history-header">
          <h3>Version History</h3>
        </div>
        <div className="history-loading">Loading...</div>
      </div>
    )
  }

  if (versions.length === 0) {
    return (
      <div className="version-history">
        <div className="history-header">
          <h3>Version History</h3>
        </div>
        <p className="no-history">No version history available</p>
      </div>
    )
  }

  return (
    <aside className="version-history">
      <header className="history-header">
        <h3>Version History</h3>
        <span className="history-count">{versions.length} versions</span>
      </header>

      <div className="history-timeline">
        {versions.map((version) => (
          <VersionItem
            key={version.id}
            version={version}
            onClick={() => onVersionSelect(version)}
          />
        ))}
      </div>
    </aside>
  )
}
