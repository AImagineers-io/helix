/**
 * VersionItem Component
 *
 * Displays a single version entry in the version history timeline.
 */
import type { PromptVersion } from '../../services/prompts-api'

interface VersionItemProps {
  /** Version data to display */
  version: PromptVersion
  /** Callback when version is clicked */
  onClick: () => void
}

const formatDate = (dateString: string): string => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function VersionItem({ version, onClick }: VersionItemProps) {
  return (
    <article className={`version-item ${version.is_active ? 'active' : ''}`}>
      <button className="version-button" onClick={onClick} type="button" aria-label={`Select version ${version.version_number}`}>
        <div className="version-header">
          <span className="version-number">Version {version.version_number}</span>
          {version.is_active && <span className="active-badge">Active</span>}
        </div>
        <div className="version-meta">
          <span className="version-author">by {version.created_by || 'System'}</span>
          <time className="version-date" dateTime={version.created_at}>
            {formatDate(version.created_at)}
          </time>
        </div>
        {version.change_notes && <p className="version-notes">{version.change_notes}</p>}
      </button>
    </article>
  )
}
