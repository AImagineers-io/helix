/**
 * Settings page component
 *
 * Displays current instance configuration (read-only).
 */
import { useEffect, useState } from 'react'
import axios from 'axios'

interface BrandingConfig {
  app_name: string
  app_description: string
  bot_name: string
  logo_url: string | null
  primary_color: string
}

export default function Settings() {
  const [config, setConfig] = useState<BrandingConfig | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchConfig() {
      try {
        setLoading(true)
        const response = await axios.get<BrandingConfig>('/api/branding/config')
        setConfig(response.data)
      } catch (err) {
        setError('Failed to load configuration')
      } finally {
        setLoading(false)
      }
    }

    fetchConfig()
  }, [])

  if (loading) {
    return <div>Loading...</div>
  }

  if (error) {
    return <div>Error: {error}</div>
  }

  if (!config) {
    return <div>No configuration available</div>
  }

  return (
    <div>
      <h1>Settings</h1>

      <section>
        <h2>Instance Configuration</h2>
        <div>
          <div>
            <strong>App Name:</strong> {config.app_name}
          </div>
          <div>
            <strong>Description:</strong> {config.app_description}
          </div>
          <div>
            <strong>Bot Name:</strong> {config.bot_name}
          </div>
        </div>
      </section>

      <section>
        <h2>Branding Preview</h2>
        <div>
          <div>
            <strong>Primary Color:</strong>{' '}
            <span style={{ color: config.primary_color }}>{config.primary_color}</span>
          </div>
          {config.logo_url && (
            <div>
              <strong>Logo URL:</strong> {config.logo_url}
            </div>
          )}
        </div>
      </section>
    </div>
  )
}
