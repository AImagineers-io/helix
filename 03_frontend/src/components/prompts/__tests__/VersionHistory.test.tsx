import { describe, it, expect, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { VersionHistory } from '../VersionHistory'
import { PromptVersion } from '../../../services/prompts-api'

const mockVersions: PromptVersion[] = [
  {
    id: 2,
    template_id: 1,
    content: 'Updated content',
    version_number: 2,
    is_active: false,
    created_at: '2025-01-02T00:00:00Z',
    created_by: 'admin',
    change_notes: 'Fixed typo',
  },
  {
    id: 1,
    template_id: 1,
    content: 'Original content',
    version_number: 1,
    is_active: true,
    created_at: '2025-01-01T00:00:00Z',
    created_by: 'admin',
    change_notes: null,
  },
]

describe('VersionHistory', () => {
  it('should display loading state', () => {
    render(<VersionHistory versions={[]} isLoading={true} onVersionSelect={() => {}} />)

    expect(screen.getByText(/loading/i)).toBeInTheDocument()
  })

  it('should display no history message when empty', () => {
    render(<VersionHistory versions={[]} isLoading={false} onVersionSelect={() => {}} />)

    expect(screen.getByText(/no version history/i)).toBeInTheDocument()
  })

  it('should display all versions', () => {
    render(<VersionHistory versions={mockVersions} isLoading={false} onVersionSelect={() => {}} />)

    expect(screen.getByText(/version 2/i)).toBeInTheDocument()
    expect(screen.getByText(/version 1/i)).toBeInTheDocument()
  })

  it('should display version count', () => {
    render(<VersionHistory versions={mockVersions} isLoading={false} onVersionSelect={() => {}} />)

    expect(screen.getByText(/2 versions/i)).toBeInTheDocument()
  })

  it('should show active version badge', () => {
    render(<VersionHistory versions={mockVersions} isLoading={false} onVersionSelect={() => {}} />)

    expect(screen.getByText(/active/i)).toBeInTheDocument()
  })

  it('should call onVersionSelect when version clicked', () => {
    const onVersionSelect = vi.fn()
    render(<VersionHistory versions={mockVersions} isLoading={false} onVersionSelect={onVersionSelect} />)

    const versionButton = screen.getAllByRole('button')[0]
    fireEvent.click(versionButton)

    expect(onVersionSelect).toHaveBeenCalledWith(mockVersions[0])
  })

  it('should display change notes when available', () => {
    render(<VersionHistory versions={mockVersions} isLoading={false} onVersionSelect={() => {}} />)

    expect(screen.getByText('Fixed typo')).toBeInTheDocument()
  })

  it('should display created_by information', () => {
    render(<VersionHistory versions={mockVersions} isLoading={false} onVersionSelect={() => {}} />)

    expect(screen.getAllByText(/admin/i).length).toBeGreaterThan(0)
  })
})
