/**
 * PromptSearch Component
 *
 * Search bar and type filter for the prompt list.
 * Features debounced text search (300ms) and dropdown type filter.
 *
 * @example
 * ```tsx
 * function PromptList() {
 *   const [search, setSearch] = useState('')
 *   const [type, setType] = useState('')
 *
 *   return (
 *     <div>
 *       <PromptSearch
 *         onSearchChange={setSearch}
 *         onTypeChange={setType}
 *         promptTypes={['system', 'user', 'assistant']}
 *       />
 *       <PromptGrid filter={{ search, type }} />
 *     </div>
 *   )
 * }
 * ```
 */
import { useState, useEffect, useRef, useCallback } from 'react'

/** Delay in milliseconds before search callback is triggered */
const DEBOUNCE_DELAY = 300

/** Props for the PromptSearch component */
export interface PromptSearchProps {
  /** Called when search query changes (debounced by 300ms) */
  onSearchChange: (query: string) => void
  /** Called immediately when type filter changes */
  onTypeChange: (type: string) => void
  /** Available prompt types for filter dropdown */
  promptTypes?: string[]
  /** Initial search query value */
  initialSearch?: string
  /** Initial type filter value */
  initialType?: string
}

export function PromptSearch({
  onSearchChange,
  onTypeChange,
  promptTypes = [],
  initialSearch = '',
  initialType = '',
}: PromptSearchProps) {
  const [searchValue, setSearchValue] = useState(initialSearch)
  const [selectedType, setSelectedType] = useState(initialType)
  const debounceTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  // Debounced search callback
  useEffect(() => {
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }

    debounceTimerRef.current = setTimeout(() => {
      onSearchChange(searchValue)
    }, DEBOUNCE_DELAY)

    return () => {
      if (debounceTimerRef.current) {
        clearTimeout(debounceTimerRef.current)
      }
    }
  }, [searchValue, onSearchChange])

  /**
   * Handle search input changes.
   * Value is debounced before calling onSearchChange.
   */
  const handleSearchChange = useCallback((event: React.ChangeEvent<HTMLInputElement>) => {
    setSearchValue(event.target.value)
  }, [])

  /**
   * Clear search input and immediately notify parent.
   */
  const handleClearSearch = useCallback(() => {
    setSearchValue('')
    // Clear pending debounce timer
    if (debounceTimerRef.current) {
      clearTimeout(debounceTimerRef.current)
    }
    // Immediately notify of clear (don't wait for debounce)
    onSearchChange('')
  }, [onSearchChange])

  /**
   * Handle type filter selection changes.
   * Immediately calls onTypeChange (no debounce).
   */
  const handleTypeChange = useCallback((event: React.ChangeEvent<HTMLSelectElement>) => {
    const value = event.target.value
    setSelectedType(value)
    onTypeChange(value)
  }, [onTypeChange])

  return (
    <div className="prompt-search">
      <div className="search-input-container">
        <label htmlFor="prompt-search" className="visually-hidden">
          Search prompts
        </label>
        <input
          id="prompt-search"
          type="text"
          value={searchValue}
          onChange={handleSearchChange}
          placeholder="Search prompts..."
          className="search-input"
        />
        {searchValue && (
          <button
            onClick={handleClearSearch}
            className="clear-search-button"
            aria-label="Clear search"
            type="button"
          >
            ×
          </button>
        )}
      </div>

      <div className="type-filter-container">
        <label htmlFor="type-filter" className="visually-hidden">
          Filter by type
        </label>
        <select
          id="type-filter"
          value={selectedType}
          onChange={handleTypeChange}
          className="type-filter"
          aria-label="Filter by type"
        >
          <option value="">All Types</option>
          {promptTypes.map((type) => (
            <option key={type} value={type}>
              {type}
            </option>
          ))}
        </select>
      </div>
    </div>
  )
}
