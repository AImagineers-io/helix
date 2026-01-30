/**
 * Diff Utility Tests
 *
 * Tests for text diff computation utilities.
 */
import { describe, it, expect } from 'vitest'
import { computeDiff, DiffType, DiffLine } from '../diff'

describe('computeDiff', () => {
  describe('identical content', () => {
    it('returns all lines as unchanged when texts are identical', () => {
      const result = computeDiff('line 1\nline 2\nline 3', 'line 1\nline 2\nline 3')

      expect(result).toHaveLength(3)
      result.forEach((line) => {
        expect(line.type).toBe(DiffType.Unchanged)
      })
    })

    it('returns empty array for empty strings', () => {
      const result = computeDiff('', '')

      expect(result).toHaveLength(0)
    })
  })

  describe('additions', () => {
    it('marks new lines as added', () => {
      const result = computeDiff('line 1\nline 2', 'line 1\nline 2\nline 3')

      expect(result).toHaveLength(3)
      expect(result[0].type).toBe(DiffType.Unchanged)
      expect(result[1].type).toBe(DiffType.Unchanged)
      expect(result[2].type).toBe(DiffType.Added)
      expect(result[2].content).toBe('line 3')
    })

    it('handles additions at the beginning', () => {
      const result = computeDiff('line 2\nline 3', 'line 1\nline 2\nline 3')

      const addedLines = result.filter((l) => l.type === DiffType.Added)
      expect(addedLines).toHaveLength(1)
      expect(addedLines[0].content).toBe('line 1')
    })

    it('handles additions in the middle', () => {
      const result = computeDiff('line 1\nline 3', 'line 1\nline 2\nline 3')

      const addedLines = result.filter((l) => l.type === DiffType.Added)
      expect(addedLines).toHaveLength(1)
      expect(addedLines[0].content).toBe('line 2')
    })
  })

  describe('deletions', () => {
    it('marks removed lines as deleted', () => {
      const result = computeDiff('line 1\nline 2\nline 3', 'line 1\nline 2')

      const deletedLines = result.filter((l) => l.type === DiffType.Removed)
      expect(deletedLines).toHaveLength(1)
      expect(deletedLines[0].content).toBe('line 3')
    })

    it('handles deletions at the beginning', () => {
      const result = computeDiff('line 1\nline 2\nline 3', 'line 2\nline 3')

      const deletedLines = result.filter((l) => l.type === DiffType.Removed)
      expect(deletedLines).toHaveLength(1)
      expect(deletedLines[0].content).toBe('line 1')
    })
  })

  describe('modifications', () => {
    it('shows removed and added for modified lines', () => {
      const result = computeDiff('old line', 'new line')

      expect(result).toHaveLength(2)
      const removed = result.find((l) => l.type === DiffType.Removed)
      const added = result.find((l) => l.type === DiffType.Added)

      expect(removed?.content).toBe('old line')
      expect(added?.content).toBe('new line')
    })
  })

  describe('complex diffs', () => {
    it('handles multiple changes', () => {
      const oldText = 'line 1\nline 2\nline 3\nline 4'
      const newText = 'line 1\nmodified line 2\nline 3\nline 5'

      const result = computeDiff(oldText, newText)

      // Should have unchanged, removed, added, unchanged, removed, added
      const removed = result.filter((l) => l.type === DiffType.Removed)
      const added = result.filter((l) => l.type === DiffType.Added)
      const unchanged = result.filter((l) => l.type === DiffType.Unchanged)

      expect(removed.length).toBeGreaterThan(0)
      expect(added.length).toBeGreaterThan(0)
      expect(unchanged.length).toBeGreaterThan(0)
    })
  })

  describe('line numbers', () => {
    it('assigns correct old line numbers', () => {
      const result = computeDiff('line 1\nline 2\nline 3', 'line 1\nline 2')

      const unchangedLines = result.filter((l) => l.type === DiffType.Unchanged)
      expect(unchangedLines[0].oldLineNumber).toBe(1)
      expect(unchangedLines[1].oldLineNumber).toBe(2)
    })

    it('assigns correct new line numbers', () => {
      const result = computeDiff('line 1\nline 2', 'line 1\nline 2\nline 3')

      const unchangedLines = result.filter((l) => l.type === DiffType.Unchanged)
      expect(unchangedLines[0].newLineNumber).toBe(1)
      expect(unchangedLines[1].newLineNumber).toBe(2)

      const addedLine = result.find((l) => l.type === DiffType.Added)
      expect(addedLine?.newLineNumber).toBe(3)
    })

    it('removed lines have no new line number', () => {
      const result = computeDiff('line 1\nline 2\nline 3', 'line 1\nline 2')

      const removedLine = result.find((l) => l.type === DiffType.Removed)
      expect(removedLine?.newLineNumber).toBeUndefined()
    })

    it('added lines have no old line number', () => {
      const result = computeDiff('line 1\nline 2', 'line 1\nline 2\nline 3')

      const addedLine = result.find((l) => l.type === DiffType.Added)
      expect(addedLine?.oldLineNumber).toBeUndefined()
    })
  })
})
