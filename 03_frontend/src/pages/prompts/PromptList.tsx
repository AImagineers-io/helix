/**
 * PromptList Page Component
 *
 * Displays a list of all prompt templates with links to edit each one.
 */
import { useState, useEffect } from 'react'
import { Link } from 'react-router-dom'
import { promptsApi } from '../../services/prompts-api'
import type { PromptTemplateListItem } from '../../services/prompts-api'

export function PromptList() {
  const [prompts, setPrompts] = useState<PromptTemplateListItem[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const fetchPrompts = async () => {
      try {
        setLoading(true)
        const data = await promptsApi.listPrompts()
        setPrompts(data)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load prompts')
      } finally {
        setLoading(false)
      }
    }

    fetchPrompts()
  }, [])

  if (loading) {
    return (
      <div className="prompt-list-container">
        <div className="loading-state">Loading...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="prompt-list-container">
        <div className="error-state">Error: {error}</div>
      </div>
    )
  }

  if (prompts.length === 0) {
    return (
      <div className="prompt-list-container">
        <div className="empty-state">No prompts available</div>
      </div>
    )
  }

  return (
    <div className="prompt-list-page">
      <header className="page-header">
        <h1>Prompt Templates</h1>
        <p className="page-subtitle">Manage your LLM prompt templates and versions</p>
      </header>

      <main className="prompts-grid">
        {prompts.map((prompt) => (
          <article key={prompt.id} className="prompt-card">
            <Link to={`/prompts/${prompt.id}`} className="prompt-link">
              <h2 className="prompt-name">{prompt.name}</h2>
              <span className="prompt-type">{prompt.prompt_type}</span>
              {prompt.description && <p className="prompt-description">{prompt.description}</p>}
            </Link>
          </article>
        ))}
      </main>
    </div>
  )
}
