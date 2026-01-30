/**
 * PreviewContext Component
 *
 * Context variable editor for preview mode.
 * Auto-detects variables from prompt content (format: {variable_name})
 * and provides both field-based and JSON editing interfaces.
 *
 * Features:
 * - Automatic variable detection from prompt content
 * - Smart example value generation based on variable names
 * - Field-based editor for individual variables
 * - JSON editor for power users
 * - Live preview of interpolated prompt
 *
 * @example
 * ```tsx
 * <PreviewContext
 *   promptContent="Hello {user_name}, order {order_id} confirmed."
 *   onChange={(values) => console.log(values)}
 *   initialValues={{ user_name: 'John' }}
 * />
 * ```
 */
import { useState, useMemo, useCallback, useEffect } from 'react'

/** Regular expression to find variables in format {variable_name} */
const VARIABLE_REGEX = /\{(\w+)\}/g

/** Props for the PreviewContext component */
export interface PreviewContextProps {
  /** Prompt content to extract variables from */
  promptContent: string
  /** Called when context values change */
  onChange: (values: Record<string, string>) => void
  /** Initial values for variables (overrides auto-generated examples) */
  initialValues?: Record<string, string>
}

/** Available editor modes */
export type EditorMode = 'fields' | 'json'

/**
 * Extract unique variable names from prompt content.
 */
function extractVariables(content: string): string[] {
  const matches = content.matchAll(VARIABLE_REGEX)
  const variables = new Set<string>()

  for (const match of matches) {
    variables.add(match[1])
  }

  return Array.from(variables)
}

/**
 * Generate example values for detected variables.
 */
function generateExampleValues(variables: string[]): Record<string, string> {
  const examples: Record<string, string> = {}

  variables.forEach((variable) => {
    // Generate contextual example based on variable name
    if (variable.toLowerCase().includes('name')) {
      examples[variable] = 'John Doe'
    } else if (variable.toLowerCase().includes('email')) {
      examples[variable] = 'user@example.com'
    } else if (variable.toLowerCase().includes('id')) {
      examples[variable] = '12345'
    } else if (variable.toLowerCase().includes('date')) {
      examples[variable] = new Date().toISOString().split('T')[0]
    } else {
      examples[variable] = `[${variable}]`
    }
  })

  return examples
}

/**
 * Interpolate variables into prompt content.
 */
function interpolatePrompt(content: string, values: Record<string, string>): string {
  return content.replace(VARIABLE_REGEX, (match, variable) => {
    return values[variable] ?? match
  })
}

export function PreviewContext({
  promptContent,
  onChange,
  initialValues = {},
}: PreviewContextProps) {
  const [editorMode, setEditorMode] = useState<EditorMode>('fields')
  const [jsonError, setJsonError] = useState<string | null>(null)
  const [jsonText, setJsonText] = useState('')

  // Extract variables from prompt
  const variables = useMemo(() => extractVariables(promptContent), [promptContent])

  // Generate example values
  const exampleValues = useMemo(() => generateExampleValues(variables), [variables])

  // Merge initial values with examples
  const [values, setValues] = useState<Record<string, string>>(() => ({
    ...exampleValues,
    ...initialValues,
  }))

  // Update JSON text when values change
  useEffect(() => {
    setJsonText(JSON.stringify(values, null, 2))
  }, [values])

  // Handle field value change
  const handleFieldChange = useCallback(
    (variable: string, value: string) => {
      const newValues = { ...values, [variable]: value }
      setValues(newValues)
      onChange(newValues)
    },
    [values, onChange]
  )

  // Handle JSON edit
  const handleJsonChange = useCallback(
    (text: string) => {
      setJsonText(text)

      try {
        const parsed = JSON.parse(text)
        setJsonError(null)
        setValues(parsed)
        onChange(parsed)
      } catch {
        setJsonError('Invalid JSON format')
      }
    },
    [onChange]
  )

  // Reset to example values
  const handleReset = useCallback(() => {
    setValues(exampleValues)
    onChange(exampleValues)
    setJsonError(null)
  }, [exampleValues, onChange])

  // Interpolated preview
  const preview = useMemo(
    () => interpolatePrompt(promptContent, values),
    [promptContent, values]
  )

  // No variables case
  if (variables.length === 0) {
    return (
      <div className="preview-context">
        <h4 className="preview-context-heading">Context Variables</h4>
        <p className="preview-context-empty">No variables detected in this prompt.</p>
      </div>
    )
  }

  return (
    <div className="preview-context">
      <div className="preview-context-header">
        <h4 className="preview-context-heading">Context Variables</h4>
        <div className="preview-context-controls">
          <button
            onClick={() => setEditorMode('fields')}
            className={`preview-context-toggle ${editorMode === 'fields' ? 'active' : ''}`}
            aria-pressed={editorMode === 'fields'}
          >
            Fields
          </button>
          <button
            onClick={() => setEditorMode('json')}
            className={`preview-context-toggle ${editorMode === 'json' ? 'active' : ''}`}
            aria-pressed={editorMode === 'json'}
          >
            JSON
          </button>
          <button onClick={handleReset} className="preview-context-reset" aria-label="Reset">
            Reset
          </button>
        </div>
      </div>

      {editorMode === 'fields' ? (
        <div className="preview-context-fields">
          {variables.map((variable) => (
            <div key={variable} className="preview-context-field">
              <label htmlFor={`var-${variable}`} className="preview-context-label">
                {variable}
              </label>
              <input
                id={`var-${variable}`}
                type="text"
                value={values[variable] ?? ''}
                onChange={(e) => handleFieldChange(variable, e.target.value)}
                className="preview-context-input"
              />
            </div>
          ))}
        </div>
      ) : (
        <div className="preview-context-json">
          <label htmlFor="json-editor" className="visually-hidden">
            JSON Editor
          </label>
          <textarea
            id="json-editor"
            value={jsonText}
            onChange={(e) => handleJsonChange(e.target.value)}
            className="preview-context-json-editor"
            rows={6}
            aria-label="JSON editor"
          />
          {jsonError && <p className="preview-context-json-error">{jsonError}</p>}
        </div>
      )}

      <div className="preview-context-output">
        <h5 className="preview-context-output-heading">Preview</h5>
        <pre className="preview-context-preview">{preview}</pre>
      </div>
    </div>
  )
}
