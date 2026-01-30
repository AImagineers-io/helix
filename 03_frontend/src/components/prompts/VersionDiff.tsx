/**
 * VersionDiff Component
 *
 * Side-by-side diff display for comparing prompt versions.
 * Supports unified (inline) and split (side-by-side) view modes.
 *
 * Visual indicators:
 * - Green highlighting: Lines added in the new version
 * - Red highlighting: Lines removed from the old version
 * - No highlighting: Unchanged lines
 *
 * @example
 * ```tsx
 * <VersionDiff
 *   oldContent="Original prompt text"
 *   newContent="Updated prompt text"
 *   oldVersion={1}
 *   newVersion={2}
 *   onClose={() => setShowDiff(false)}
 * />
 * ```
 */
import { useState, useMemo } from 'react'
import { computeDiff, DiffType } from '../../utils/diff'
import type { DiffLine } from '../../utils/diff'

/** Available view modes for the diff display */
export type ViewMode = 'unified' | 'split'

/** Props for the VersionDiff component */
export interface VersionDiffProps {
  /** Content of the older version */
  oldContent: string
  /** Content of the newer version */
  newContent: string
  /** Version number of the old version (displayed in header) */
  oldVersion: number
  /** Version number of the new version (displayed in header) */
  newVersion: number
  /** Initial view mode. Default: 'unified' */
  viewMode?: ViewMode
  /** Optional callback when diff view is closed */
  onClose?: () => void
}

export function VersionDiff({
  oldContent,
  newContent,
  oldVersion,
  newVersion,
  viewMode: initialViewMode = 'unified',
  onClose,
}: VersionDiffProps) {
  const [viewMode, setViewMode] = useState<ViewMode>(initialViewMode)

  const diffLines = useMemo(() => {
    return computeDiff(oldContent, newContent)
  }, [oldContent, newContent])

  const hasChanges = diffLines.some((line) => line.type !== DiffType.Unchanged)

  if (!hasChanges) {
    return (
      <div className="version-diff" role="region" aria-label="Version diff">
        <div className="diff-header">
          <div className="diff-version-labels">
            <span className="diff-version-label">Version {oldVersion}</span>
            <span className="diff-version-label">Version {newVersion}</span>
          </div>
          {onClose && (
            <button onClick={onClose} className="diff-close-button" aria-label="Close">
              ×
            </button>
          )}
        </div>
        <div className="diff-no-changes">
          <p>No changes between versions</p>
        </div>
      </div>
    )
  }

  return (
    <div className="version-diff" role="region" aria-label="Version diff">
      <div className="diff-header">
        <div className="diff-version-labels">
          <span className="diff-version-label">Version {oldVersion}</span>
          <span className="diff-version-label">Version {newVersion}</span>
        </div>
        <div className="diff-controls">
          <button
            onClick={() => setViewMode('unified')}
            className={`diff-view-toggle ${viewMode === 'unified' ? 'active' : ''}`}
            aria-pressed={viewMode === 'unified'}
          >
            Unified
          </button>
          <button
            onClick={() => setViewMode('split')}
            className={`diff-view-toggle ${viewMode === 'split' ? 'active' : ''}`}
            aria-pressed={viewMode === 'split'}
          >
            Split
          </button>
        </div>
        {onClose && (
          <button onClick={onClose} className="diff-close-button" aria-label="Close">
            ×
          </button>
        )}
      </div>

      <div className={`diff-view diff-view--${viewMode}`}>
        {viewMode === 'unified' ? (
          <UnifiedDiffView lines={diffLines} />
        ) : (
          <SplitDiffView lines={diffLines} />
        )}
      </div>
    </div>
  )
}

interface DiffViewProps {
  lines: DiffLine[]
}

function UnifiedDiffView({ lines }: DiffViewProps) {
  return (
    <div className="diff-unified">
      {lines.map((line, index) => (
        <div
          key={index}
          className={`diff-line diff-line--${line.type}`}
        >
          <span className="diff-line-number diff-line-number--old">
            {line.oldLineNumber ?? ''}
          </span>
          <span className="diff-line-number diff-line-number--new">
            {line.newLineNumber ?? ''}
          </span>
          <span className="diff-line-prefix">
            {line.type === DiffType.Added ? '+' : line.type === DiffType.Removed ? '-' : ' '}
          </span>
          <span className="diff-line-content">{line.content}</span>
        </div>
      ))}
    </div>
  )
}

function SplitDiffView({ lines }: DiffViewProps) {
  // Separate lines into left (old) and right (new) columns
  const { leftLines, rightLines } = useMemo(() => {
    const left: (DiffLine | null)[] = []
    const right: (DiffLine | null)[] = []

    let i = 0
    while (i < lines.length) {
      const line = lines[i]

      if (line.type === DiffType.Unchanged) {
        left.push(line)
        right.push(line)
        i++
      } else if (line.type === DiffType.Removed) {
        // Check if next line is Added (modification)
        const nextLine = lines[i + 1]
        if (nextLine && nextLine.type === DiffType.Added) {
          left.push(line)
          right.push(nextLine)
          i += 2
        } else {
          left.push(line)
          right.push(null)
          i++
        }
      } else if (line.type === DiffType.Added) {
        left.push(null)
        right.push(line)
        i++
      }
    }

    return { leftLines: left, rightLines: right }
  }, [lines])

  return (
    <div className="diff-split">
      <div className="diff-split-side diff-split-side--old">
        {leftLines.map((line, index) => (
          <div
            key={index}
            className={`diff-line ${line ? `diff-line--${line.type}` : 'diff-line--empty'}`}
          >
            <span className="diff-line-number">
              {line?.oldLineNumber ?? ''}
            </span>
            <span className="diff-line-content">{line?.content ?? ''}</span>
          </div>
        ))}
      </div>
      <div className="diff-split-side diff-split-side--new">
        {rightLines.map((line, index) => (
          <div
            key={index}
            className={`diff-line ${line ? `diff-line--${line.type}` : 'diff-line--empty'}`}
          >
            <span className="diff-line-number">
              {line?.newLineNumber ?? ''}
            </span>
            <span className="diff-line-content">{line?.content ?? ''}</span>
          </div>
        ))}
      </div>
    </div>
  )
}
