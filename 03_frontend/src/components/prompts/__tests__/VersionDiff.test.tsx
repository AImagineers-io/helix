/**
 * VersionDiff Component Tests
 *
 * Tests for side-by-side version diff display.
 */
import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { VersionDiff } from '../VersionDiff'

describe('VersionDiff', () => {
  const defaultProps = {
    oldContent: 'line 1\nline 2\nline 3',
    newContent: 'line 1\nmodified line 2\nline 3',
    oldVersion: 1,
    newVersion: 2,
  }

  describe('rendering', () => {
    it('renders diff container', () => {
      const { container } = render(<VersionDiff {...defaultProps} />)

      expect(container.querySelector('.version-diff')).toBeInTheDocument()
    })

    it('shows version labels', () => {
      render(<VersionDiff {...defaultProps} />)

      expect(screen.getByText(/version 1/i)).toBeInTheDocument()
      expect(screen.getByText(/version 2/i)).toBeInTheDocument()
    })

    it('displays added lines with green styling', () => {
      const { container } = render(<VersionDiff {...defaultProps} />)

      const addedLines = container.querySelectorAll('.diff-line--added')
      expect(addedLines.length).toBeGreaterThan(0)
    })

    it('displays removed lines with red styling', () => {
      const { container } = render(<VersionDiff {...defaultProps} />)

      const removedLines = container.querySelectorAll('.diff-line--removed')
      expect(removedLines.length).toBeGreaterThan(0)
    })

    it('displays unchanged lines', () => {
      const { container } = render(<VersionDiff {...defaultProps} />)

      const unchangedLines = container.querySelectorAll('.diff-line--unchanged')
      expect(unchangedLines.length).toBeGreaterThan(0)
    })
  })

  describe('view modes', () => {
    it('renders unified view by default', () => {
      const { container } = render(<VersionDiff {...defaultProps} />)

      expect(container.querySelector('.diff-view--unified')).toBeInTheDocument()
    })

    it('renders split view when specified', () => {
      const { container } = render(<VersionDiff {...defaultProps} viewMode="split" />)

      expect(container.querySelector('.diff-view--split')).toBeInTheDocument()
    })

    it('allows toggling between unified and split views', () => {
      const { container } = render(<VersionDiff {...defaultProps} />)

      // Toggle to split view
      const toggleButton = screen.getByRole('button', { name: /split/i })
      fireEvent.click(toggleButton)

      expect(container.querySelector('.diff-view--split')).toBeInTheDocument()
    })
  })

  describe('no changes', () => {
    it('shows message when content is identical', () => {
      render(
        <VersionDiff
          oldContent="same content"
          newContent="same content"
          oldVersion={1}
          newVersion={2}
        />
      )

      expect(screen.getByText(/no changes/i)).toBeInTheDocument()
    })
  })

  describe('empty content', () => {
    it('handles empty old content', () => {
      render(
        <VersionDiff
          oldContent=""
          newContent="new content"
          oldVersion={1}
          newVersion={2}
        />
      )

      const addedLines = screen.getAllByText('new content')
      expect(addedLines.length).toBeGreaterThan(0)
    })

    it('handles empty new content', () => {
      render(
        <VersionDiff
          oldContent="old content"
          newContent=""
          oldVersion={1}
          newVersion={2}
        />
      )

      expect(screen.getByText('old content')).toBeInTheDocument()
    })
  })

  describe('line numbers', () => {
    it('displays line numbers', () => {
      const { container } = render(<VersionDiff {...defaultProps} />)

      const lineNumbers = container.querySelectorAll('.diff-line-number')
      expect(lineNumbers.length).toBeGreaterThan(0)
    })
  })

  describe('onClose callback', () => {
    it('calls onClose when close button is clicked', () => {
      const onClose = vi.fn()
      render(<VersionDiff {...defaultProps} onClose={onClose} />)

      const closeButton = screen.getByRole('button', { name: /close/i })
      fireEvent.click(closeButton)

      expect(onClose).toHaveBeenCalled()
    })

    it('does not render close button when onClose is not provided', () => {
      render(<VersionDiff {...defaultProps} />)

      expect(screen.queryByRole('button', { name: /close/i })).not.toBeInTheDocument()
    })
  })

  describe('accessibility', () => {
    it('has accessible diff region', () => {
      render(<VersionDiff {...defaultProps} />)

      expect(screen.getByRole('region', { name: /diff/i })).toBeInTheDocument()
    })
  })
})
