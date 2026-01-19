/**
 * PromptEditor Page Component
 *
 * Allows editing prompt template content and saves new versions.
 */
import { useState, useEffect } from 'react'
import { useParams } from 'react-router-dom'
import { promptsApi, PromptTemplate } from '../../services/prompts-api'

export function PromptEditor() {
  const { id } = useParams<{ id: string }>()
  const [prompt, setPrompt] = useState<PromptTemplate | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [editedContent, setEditedContent] = useState('')
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!id) return

    const fetchPrompt = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await promptsApi.getPrompt(parseInt(id))
        setPrompt(data)
        const activeVersion = data.versions.find((v) => v.is_active)
        setEditedContent(activeVersion?.content || '')
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load prompt')
      } finally {
        setLoading(false)
      }
    }

    fetchPrompt()
  }, [id])

  const handleSave = async () => {
    if (!id || !prompt || saving) return

    try {
      setSaving(true)
      setError(null)
      setSuccess(null)
      const updated = await promptsApi.updatePrompt(parseInt(id), {
        content: editedContent,
        created_by: undefined,
        change_notes: undefined,
      })
      setPrompt(updated)
      setSuccess('Prompt saved successfully')
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save prompt')
    } finally {
      setSaving(false)
    }
  }

  if (loading) {
    return (
      <div className="prompt-editor-container">
        <div className="loading-state">Loading...</div>
      </div>
    )
  }

  if (error && !prompt) {
    return (
      <div className="prompt-editor-container">
        <div className="error-state">Error: {error}</div>
      </div>
    )
  }

  if (!prompt) {
    return (
      <div className="prompt-editor-container">
        <div className="not-found-state">Prompt not found</div>
      </div>
    )
  }

  return (
    <div className="prompt-editor-page">
      <header className="page-header">
        <h1>{prompt.name}</h1>
        {prompt.description && <p className="prompt-description">{prompt.description}</p>}
        <div className="prompt-meta">
          <span className="prompt-type">{prompt.prompt_type}</span>
        </div>
      </header>

      {success && <div className="success-message">{success}</div>}
      {error && <div className="error-message">Error: {error}</div>}

      <main className="editor-container">
        <div className="editor-field">
          <label htmlFor="content" className="editor-label">
            Prompt Content
          </label>
          <textarea
            id="content"
            className="editor-textarea"
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            rows={15}
            placeholder="Enter your prompt template content..."
          />
        </div>

        <div className="editor-actions">
          <button onClick={handleSave} disabled={saving} className="save-button">
            {saving ? 'Saving...' : 'Save'}
          </button>
        </div>
      </main>
    </div>
  )
}
