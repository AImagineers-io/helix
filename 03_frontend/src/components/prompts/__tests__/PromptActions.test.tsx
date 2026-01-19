import { describe, it, expect, beforeEach, vi } from 'vitest'
import { render, screen, fireEvent } from '@testing-library/react'
import { PromptActions } from '../PromptActions'

describe('PromptActions', () => {
  const mockOnPublish = vi.fn()
  const mockOnRollback = vi.fn()

  beforeEach(() => {
    vi.clearAllMocks()
  })

  it('should render publish and rollback buttons', () => {
    render(
      <PromptActions
        selectedVersionNumber={2}
        activeVersionNumber={1}
        onPublish={mockOnPublish}
        onRollback={mockOnRollback}
      />
    )

    expect(screen.getByRole('button', { name: /publish/i })).toBeInTheDocument()
    expect(screen.getByRole('button', { name: /rollback/i })).toBeInTheDocument()
  })

  it('should call onPublish when publish button clicked', () => {
    render(
      <PromptActions
        selectedVersionNumber={2}
        activeVersionNumber={1}
        onPublish={mockOnPublish}
        onRollback={mockOnRollback}
      />
    )

    const publishButton = screen.getByRole('button', { name: /publish/i })
    fireEvent.click(publishButton)

    expect(mockOnPublish).toHaveBeenCalledTimes(1)
  })

  it('should call onRollback when rollback button clicked', () => {
    render(
      <PromptActions
        selectedVersionNumber={2}
        activeVersionNumber={1}
        onPublish={mockOnPublish}
        onRollback={mockOnRollback}
      />
    )

    const rollbackButton = screen.getByRole('button', { name: /rollback/i })
    fireEvent.click(rollbackButton)

    expect(mockOnRollback).toHaveBeenCalledTimes(1)
  })

  it('should disable publish when selected version is already active', () => {
    render(
      <PromptActions
        selectedVersionNumber={1}
        activeVersionNumber={1}
        onPublish={mockOnPublish}
        onRollback={mockOnRollback}
      />
    )

    const publishButton = screen.getByRole('button', { name: /publish/i })
    expect(publishButton).toBeDisabled()
  })

  it('should enable publish when selected version is not active', () => {
    render(
      <PromptActions
        selectedVersionNumber={2}
        activeVersionNumber={1}
        onPublish={mockOnPublish}
        onRollback={mockOnRollback}
      />
    )

    const publishButton = screen.getByRole('button', { name: /publish/i })
    expect(publishButton).not.toBeDisabled()
  })

  it('should show loading state when publishing', () => {
    render(
      <PromptActions
        selectedVersionNumber={2}
        activeVersionNumber={1}
        onPublish={mockOnPublish}
        onRollback={mockOnRollback}
        isPublishing={true}
      />
    )

    expect(screen.getByText(/publishing/i)).toBeInTheDocument()
  })

  it('should show loading state when rolling back', () => {
    render(
      <PromptActions
        selectedVersionNumber={2}
        activeVersionNumber={1}
        onPublish={mockOnPublish}
        onRollback={mockOnRollback}
        isRollingBack={true}
      />
    )

    expect(screen.getByText(/rolling back/i)).toBeInTheDocument()
  })
})
