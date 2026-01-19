/**
 * Prompts API Client
 *
 * Provides methods for managing prompt templates and versions.
 * Follows REST API pattern from backend prompts router.
 */
import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || '/api'

/**
 * Represents a single version of a prompt template.
 */
export interface PromptVersion {
  id: number
  template_id: number
  content: string
  version_number: number
  is_active: boolean
  created_at: string
  created_by: string | null
  change_notes: string | null
}

/**
 * Complete prompt template with all versions.
 */
export interface PromptTemplate {
  id: number
  name: string
  prompt_type: string
  description: string | null
  created_at: string
  updated_at: string
  versions: PromptVersion[]
}

/**
 * Lightweight template item for list views (no versions included).
 */
export interface PromptTemplateListItem {
  id: number
  name: string
  prompt_type: string
  description: string | null
  created_at: string
  updated_at: string
}

export interface CreatePromptRequest {
  name: string
  prompt_type: string
  content: string
  description?: string | null
  created_by?: string | null
}

export interface UpdatePromptRequest {
  content?: string | null
  description?: string | null
  created_by?: string | null
  change_notes?: string | null
}

export interface DeletePromptResponse {
  message: string
}

export interface PublishVersionResponse {
  id: number
  template_id: number
  version_number: number
  is_active: boolean
  message: string
}

export const promptsApi = {
  /**
   * List all prompt templates, optionally filtered by type.
   *
   * @param promptType - Optional filter for prompt type (e.g., 'system', 'user')
   * @returns Array of template list items without version details
   */
  async listPrompts(promptType?: string): Promise<PromptTemplateListItem[]> {
    const params: Record<string, string> = {}
    if (promptType) {
      params.prompt_type = promptType
    }
    const response = await axios.get<PromptTemplateListItem[]>(`${API_BASE_URL}/prompts`, {
      params,
    })
    return response.data
  },

  /**
   * Get a single prompt template with all versions.
   *
   * @param id - Template ID
   * @returns Complete template with version history
   */
  async getPrompt(id: number): Promise<PromptTemplate> {
    const response = await axios.get<PromptTemplate>(`${API_BASE_URL}/prompts/${id}`)
    return response.data
  },

  /**
   * Create a new prompt template with initial version.
   *
   * @param request - Prompt creation request
   * @returns Created template with initial version
   */
  async createPrompt(request: CreatePromptRequest): Promise<PromptTemplate> {
    const apiKey = import.meta.env.VITE_API_KEY
    const response = await axios.post<PromptTemplate>(`${API_BASE_URL}/prompts`, request, {
      headers: {
        'X-API-Key': apiKey,
      },
    })
    return response.data
  },

  /**
   * Update a prompt template. If content is provided, creates a new version.
   *
   * @param id - Template ID
   * @param request - Update request
   * @returns Updated template with new version (if content changed)
   */
  async updatePrompt(id: number, request: UpdatePromptRequest): Promise<PromptTemplate> {
    const apiKey = import.meta.env.VITE_API_KEY
    const response = await axios.put<PromptTemplate>(`${API_BASE_URL}/prompts/${id}`, request, {
      headers: {
        'X-API-Key': apiKey,
      },
    })
    return response.data
  },

  /**
   * Delete a prompt template (soft delete).
   *
   * @param id - Template ID
   * @returns Deletion confirmation message
   */
  async deletePrompt(id: number): Promise<DeletePromptResponse> {
    const apiKey = import.meta.env.VITE_API_KEY
    const response = await axios.delete<DeletePromptResponse>(`${API_BASE_URL}/prompts/${id}`, {
      headers: {
        'X-API-Key': apiKey,
      },
    })
    return response.data
  },

  /**
   * Publish (activate) a specific version of a template.
   *
   * @param templateId - Template ID
   * @param versionNumber - Version number to activate
   * @returns Activated version details
   */
  async publishVersion(templateId: number, versionNumber: number): Promise<PublishVersionResponse> {
    const apiKey = import.meta.env.VITE_API_KEY
    const response = await axios.post<PublishVersionResponse>(
      `${API_BASE_URL}/prompts/${templateId}/publish`,
      { version_number: versionNumber },
      {
        headers: {
          'X-API-Key': apiKey,
        },
      }
    )
    return response.data
  },

  /**
   * Rollback to the previous version of a template.
   *
   * @param templateId - Template ID
   * @returns Activated previous version details
   */
  async rollbackVersion(templateId: number): Promise<PublishVersionResponse> {
    const apiKey = import.meta.env.VITE_API_KEY
    const response = await axios.post<PublishVersionResponse>(
      `${API_BASE_URL}/prompts/${templateId}/rollback`,
      undefined,
      {
        headers: {
          'X-API-Key': apiKey,
        },
      }
    )
    return response.data
  },
}
