/**
 * Skeleton Components
 *
 * Loading placeholder components for smooth loading states.
 * These provide visual feedback while content is loading,
 * improving perceived performance.
 *
 * @example
 * ```tsx
 * // Basic usage
 * {loading ? <Skeleton width="200px" height="20px" /> : <span>{text}</span>}
 *
 * // Full editor skeleton
 * {loading ? <PromptEditorSkeleton /> : <PromptEditor />}
 * ```
 */
import { CSSProperties } from 'react'

/** Props for the base Skeleton component */
export interface SkeletonProps {
  /** Width of the skeleton. Default: '100%' */
  width?: string
  /** Height of the skeleton. Default: '1em' */
  height?: string
  /** Border radius. Default: '4px' */
  borderRadius?: string
  /** Shape variant: 'text' | 'rectangular' | 'circle'. Default: 'text' */
  variant?: 'text' | 'rectangular' | 'circle'
}

export function Skeleton({
  width = '100%',
  height = '1em',
  borderRadius = '4px',
  variant = 'text',
}: SkeletonProps) {
  const style: CSSProperties = {
    width,
    height,
    borderRadius: variant === 'circle' ? '50%' : borderRadius,
  }

  const variantClass = variant === 'rectangular' ? 'skeleton--rectangular' : ''

  return <div className={`skeleton ${variantClass}`} style={style} />
}

/** Props for SkeletonText component */
export interface SkeletonTextProps {
  /** Number of text lines to show. Default: 1 */
  lines?: number
}

/**
 * Multi-line text skeleton placeholder.
 * Last line is shorter to simulate natural text.
 */
export function SkeletonText({ lines = 1 }: SkeletonTextProps) {
  return (
    <div className="skeleton-text">
      {Array.from({ length: lines }).map((_, index) => (
        <div
          key={index}
          className={`skeleton-text-line ${index === lines - 1 && lines > 1 ? 'skeleton-text-line--short' : ''}`}
        />
      ))}
    </div>
  )
}

/** Props for SkeletonButton component */
export interface SkeletonButtonProps {
  /** Button size variant. Default: 'medium' */
  size?: 'small' | 'medium' | 'large'
}

/**
 * Button skeleton placeholder.
 */
export function SkeletonButton({ size = 'medium' }: SkeletonButtonProps) {
  return <div className={`skeleton-button skeleton-button--${size}`} />
}

/** Props for SkeletonTextarea component */
export interface SkeletonTextareaProps {
  /** Number of rows (affects height). Default: 10 */
  rows?: number
}

/**
 * Textarea skeleton placeholder.
 * Height is calculated based on row count.
 */
export function SkeletonTextarea({ rows = 10 }: SkeletonTextareaProps) {
  const height = `${rows * 1.5}em`
  return <div className="skeleton-textarea" style={{ height }} />
}

/**
 * Complete skeleton for the PromptEditor page.
 * Includes title, description, textarea, and action button placeholders.
 */
export function PromptEditorSkeleton() {
  return (
    <div className="prompt-editor-skeleton" aria-label="Loading prompt editor">
      <div className="skeleton-editor-title">
        <Skeleton height="2em" width="60%" />
      </div>
      <div className="skeleton-editor-meta">
        <Skeleton height="1em" width="100px" />
      </div>
      <SkeletonTextarea rows={15} />
      <div className="skeleton-editor-actions">
        <SkeletonButton />
      </div>
    </div>
  )
}

/** Props for VersionHistorySkeleton component */
export interface VersionHistorySkeletonProps {
  /** Number of version item placeholders to show. Default: 3 */
  count?: number
}

/**
 * Skeleton for the version history sidebar.
 * Shows placeholder items for version entries.
 */
export function VersionHistorySkeleton({ count = 3 }: VersionHistorySkeletonProps) {
  return (
    <div className="version-history-skeleton" aria-label="Loading version history">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="skeleton-version-item">
          <Skeleton height="1em" width="40%" />
          <Skeleton height="0.8em" width="60%" />
        </div>
      ))}
    </div>
  )
}
