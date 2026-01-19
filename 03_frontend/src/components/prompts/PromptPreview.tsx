/**
 * PromptPreview Component
 *
 * Allows testing prompt templates with sample input.
 * Shows how the prompt will appear when combined with user input.
 */
import { useState } from 'react'

interface PromptPreviewProps {
  /** Prompt template content to preview */
  promptContent: string
}

export function PromptPreview({ promptContent }: PromptPreviewProps) {
  const [sampleInput, setSampleInput] = useState('')
  const [preview, setPreview] = useState('')

  const handlePreview = () => {
    // Generate preview by combining prompt template with sample input
    const combined = `Prompt: ${promptContent}\n\nUser Input: ${sampleInput}`
    setPreview(combined)
  }

  return (
    <div className="prompt-preview">
      <div className="preview-section">
        <div className="preview-input">
          <label htmlFor="sample-input" className="preview-label">
            Sample Input
          </label>
          <textarea
            id="sample-input"
            value={sampleInput}
            onChange={(e) => setSampleInput(e.target.value)}
            rows={3}
            placeholder="Enter sample user input to test the prompt..."
            className="preview-textarea"
          />
        </div>

        <button onClick={handlePreview} className="preview-button">
          Preview
        </button>
      </div>

      {preview && (
        <div className="preview-output">
          <h4 className="preview-output-title">Preview:</h4>
          <pre className="preview-content">{preview}</pre>
        </div>
      )}
    </div>
  )
}
