/**
 * Diff Utilities
 *
 * Functions for computing text differences between versions.
 * Uses a Longest Common Subsequence (LCS) based algorithm
 * for accurate line-by-line diffing.
 *
 * @example
 * ```ts
 * const diff = computeDiff(oldText, newText)
 * diff.forEach(line => {
 *   if (line.type === DiffType.Added) console.log('+', line.content)
 *   if (line.type === DiffType.Removed) console.log('-', line.content)
 * })
 * ```
 */

/** Type of difference for a line */
export const DiffType = {
  /** Line exists in both versions unchanged */
  Unchanged: 'unchanged',
  /** Line was added in the new version */
  Added: 'added',
  /** Line was removed from the old version */
  Removed: 'removed',
} as const

export type DiffType = (typeof DiffType)[keyof typeof DiffType]

/** Represents a single line in the diff output */
export interface DiffLine {
  /** Type of change for this line */
  type: DiffType
  /** The actual text content of the line */
  content: string
  /** Line number in the old version (undefined for added lines) */
  oldLineNumber?: number
  /** Line number in the new version (undefined for removed lines) */
  newLineNumber?: number
}

/**
 * Compute the diff between two text strings.
 * Uses a simple line-based diff algorithm.
 *
 * @param oldText - Original text content
 * @param newText - New text content
 * @returns Array of DiffLine objects
 */
export function computeDiff(oldText: string, newText: string): DiffLine[] {
  // Handle empty strings
  if (!oldText && !newText) {
    return []
  }

  const oldLines = oldText ? oldText.split('\n') : []
  const newLines = newText ? newText.split('\n') : []

  // Build LCS table for line-based diff
  const lcs = buildLCSTable(oldLines, newLines)

  // Generate diff from LCS
  return generateDiff(oldLines, newLines, lcs)
}

/**
 * Build Longest Common Subsequence table.
 */
function buildLCSTable(oldLines: string[], newLines: string[]): number[][] {
  const m = oldLines.length
  const n = newLines.length

  // Initialize table with zeros
  const table: number[][] = Array(m + 1)
    .fill(null)
    .map(() => Array(n + 1).fill(0))

  // Fill the table
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      if (oldLines[i - 1] === newLines[j - 1]) {
        table[i][j] = table[i - 1][j - 1] + 1
      } else {
        table[i][j] = Math.max(table[i - 1][j], table[i][j - 1])
      }
    }
  }

  return table
}

/**
 * Generate diff output from LCS table.
 */
function generateDiff(
  oldLines: string[],
  newLines: string[],
  lcs: number[][]
): DiffLine[] {
  let i = oldLines.length
  let j = newLines.length

  // Backtrack through LCS table
  const result: DiffLine[] = []

  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && oldLines[i - 1] === newLines[j - 1]) {
      // Lines match - unchanged
      result.unshift({
        type: DiffType.Unchanged,
        content: oldLines[i - 1],
        oldLineNumber: i,
        newLineNumber: j,
      })
      i--
      j--
    } else if (j > 0 && (i === 0 || lcs[i][j - 1] >= lcs[i - 1][j])) {
      // Added in new
      result.unshift({
        type: DiffType.Added,
        content: newLines[j - 1],
        newLineNumber: j,
      })
      j--
    } else if (i > 0) {
      // Removed from old
      result.unshift({
        type: DiffType.Removed,
        content: oldLines[i - 1],
        oldLineNumber: i,
      })
      i--
    }
  }

  return result
}
