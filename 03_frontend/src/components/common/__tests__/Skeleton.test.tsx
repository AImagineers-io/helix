/**
 * Skeleton Component Tests
 *
 * Tests for loading skeleton placeholder components.
 */
import { describe, it, expect } from 'vitest'
import { render, screen } from '@testing-library/react'
import {
  Skeleton,
  SkeletonText,
  SkeletonButton,
  SkeletonTextarea,
  PromptEditorSkeleton,
  VersionHistorySkeleton,
} from '../Skeleton'

describe('Skeleton', () => {
  it('renders with default styles', () => {
    const { container } = render(<Skeleton />)

    expect(container.querySelector('.skeleton')).toBeInTheDocument()
  })

  it('applies custom width', () => {
    const { container } = render(<Skeleton width="200px" />)

    const skeleton = container.querySelector('.skeleton')
    expect(skeleton).toHaveStyle({ width: '200px' })
  })

  it('applies custom height', () => {
    const { container } = render(<Skeleton height="50px" />)

    const skeleton = container.querySelector('.skeleton')
    expect(skeleton).toHaveStyle({ height: '50px' })
  })

  it('applies custom border radius', () => {
    const { container } = render(<Skeleton borderRadius="10px" />)

    const skeleton = container.querySelector('.skeleton')
    expect(skeleton).toHaveStyle({ borderRadius: '10px' })
  })

  it('supports circle variant', () => {
    const { container } = render(<Skeleton variant="circle" width="40px" height="40px" />)

    const skeleton = container.querySelector('.skeleton')
    expect(skeleton).toHaveStyle({ borderRadius: '50%' })
  })

  it('supports rectangular variant', () => {
    const { container } = render(<Skeleton variant="rectangular" />)

    expect(container.querySelector('.skeleton--rectangular')).toBeInTheDocument()
  })
})

describe('SkeletonText', () => {
  it('renders a single line by default', () => {
    const { container } = render(<SkeletonText />)

    expect(container.querySelectorAll('.skeleton-text-line')).toHaveLength(1)
  })

  it('renders multiple lines', () => {
    const { container } = render(<SkeletonText lines={3} />)

    expect(container.querySelectorAll('.skeleton-text-line')).toHaveLength(3)
  })

  it('last line is shorter', () => {
    const { container } = render(<SkeletonText lines={3} />)

    const lines = container.querySelectorAll('.skeleton-text-line')
    const lastLine = lines[lines.length - 1]

    expect(lastLine).toHaveClass('skeleton-text-line--short')
  })
})

describe('SkeletonButton', () => {
  it('renders button placeholder', () => {
    const { container } = render(<SkeletonButton />)

    expect(container.querySelector('.skeleton-button')).toBeInTheDocument()
  })

  it('supports different sizes', () => {
    const { container: small } = render(<SkeletonButton size="small" />)
    const { container: large } = render(<SkeletonButton size="large" />)

    expect(small.querySelector('.skeleton-button--small')).toBeInTheDocument()
    expect(large.querySelector('.skeleton-button--large')).toBeInTheDocument()
  })
})

describe('SkeletonTextarea', () => {
  it('renders textarea placeholder', () => {
    const { container } = render(<SkeletonTextarea />)

    expect(container.querySelector('.skeleton-textarea')).toBeInTheDocument()
  })

  it('applies custom rows', () => {
    const { container } = render(<SkeletonTextarea rows={5} />)

    // Height should be based on rows
    const textarea = container.querySelector('.skeleton-textarea')
    expect(textarea).toBeInTheDocument()
  })
})

describe('PromptEditorSkeleton', () => {
  it('renders editor loading state', () => {
    render(<PromptEditorSkeleton />)

    expect(screen.getByLabelText('Loading prompt editor')).toBeInTheDocument()
  })

  it('includes title skeleton', () => {
    const { container } = render(<PromptEditorSkeleton />)

    expect(container.querySelector('.skeleton-editor-title')).toBeInTheDocument()
  })

  it('includes textarea skeleton', () => {
    const { container } = render(<PromptEditorSkeleton />)

    expect(container.querySelector('.skeleton-textarea')).toBeInTheDocument()
  })

  it('includes button skeleton', () => {
    const { container } = render(<PromptEditorSkeleton />)

    expect(container.querySelector('.skeleton-button')).toBeInTheDocument()
  })
})

describe('VersionHistorySkeleton', () => {
  it('renders version history loading state', () => {
    render(<VersionHistorySkeleton />)

    expect(screen.getByLabelText('Loading version history')).toBeInTheDocument()
  })

  it('renders multiple version item placeholders', () => {
    const { container } = render(<VersionHistorySkeleton count={5} />)

    expect(container.querySelectorAll('.skeleton-version-item')).toHaveLength(5)
  })

  it('defaults to 3 items', () => {
    const { container } = render(<VersionHistorySkeleton />)

    expect(container.querySelectorAll('.skeleton-version-item')).toHaveLength(3)
  })
})
