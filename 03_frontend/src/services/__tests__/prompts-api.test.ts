import { describe, it, expect, beforeEach, vi } from 'vitest'
import axios from 'axios'
import { promptsApi } from '../prompts-api'

vi.mock('axios')
const mockedAxios = vi.mocked(axios)

describe('prompts-api', () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  describe('listPrompts', () => {
    it('should fetch all prompts without filter', async () => {
      const mockPrompts = [
        {
          id: 1,
          name: 'System Prompt',
          prompt_type: 'system',
          description: 'Main system prompt',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ]
      mockedAxios.get.mockResolvedValue({ data: mockPrompts })

      const result = await promptsApi.listPrompts()

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/prompts', { params: {} })
      expect(result).toEqual(mockPrompts)
    })

    it('should fetch prompts filtered by type', async () => {
      const mockPrompts = [
        {
          id: 1,
          name: 'System Prompt',
          prompt_type: 'system',
          description: 'Main system prompt',
          created_at: '2025-01-01T00:00:00Z',
          updated_at: '2025-01-01T00:00:00Z',
        },
      ]
      mockedAxios.get.mockResolvedValue({ data: mockPrompts })

      const result = await promptsApi.listPrompts('system')

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/prompts', {
        params: { prompt_type: 'system' },
      })
      expect(result).toEqual(mockPrompts)
    })
  })

  describe('getPrompt', () => {
    it('should fetch single prompt with versions', async () => {
      const mockPrompt = {
        id: 1,
        name: 'System Prompt',
        prompt_type: 'system',
        description: 'Main system prompt',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        versions: [
          {
            id: 1,
            template_id: 1,
            content: 'You are a helpful assistant.',
            version_number: 1,
            is_active: true,
            created_at: '2025-01-01T00:00:00Z',
            created_by: 'admin',
            change_notes: 'Initial version',
          },
        ],
      }
      mockedAxios.get.mockResolvedValue({ data: mockPrompt })

      const result = await promptsApi.getPrompt(1)

      expect(mockedAxios.get).toHaveBeenCalledWith('/api/prompts/1')
      expect(result).toEqual(mockPrompt)
    })
  })

  describe('createPrompt', () => {
    it('should create new prompt template', async () => {
      const request = {
        name: 'New Prompt',
        prompt_type: 'system',
        content: 'You are helpful.',
        description: 'Test prompt',
        created_by: 'admin',
      }
      const mockResponse = {
        id: 2,
        name: 'New Prompt',
        prompt_type: 'system',
        description: 'Test prompt',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T00:00:00Z',
        versions: [
          {
            id: 2,
            template_id: 2,
            content: 'You are helpful.',
            version_number: 1,
            is_active: true,
            created_at: '2025-01-01T00:00:00Z',
            created_by: 'admin',
            change_notes: null,
          },
        ],
      }
      mockedAxios.post.mockResolvedValue({ data: mockResponse })

      const result = await promptsApi.createPrompt(request)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/prompts', request, {
        headers: { 'X-API-Key': undefined },
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('updatePrompt', () => {
    it('should update prompt and create new version', async () => {
      const request = {
        content: 'Updated content',
        created_by: 'admin',
        change_notes: 'Fixed typo',
      }
      const mockResponse = {
        id: 1,
        name: 'System Prompt',
        prompt_type: 'system',
        description: 'Main system prompt',
        created_at: '2025-01-01T00:00:00Z',
        updated_at: '2025-01-01T01:00:00Z',
        versions: [
          {
            id: 2,
            template_id: 1,
            content: 'Updated content',
            version_number: 2,
            is_active: false,
            created_at: '2025-01-01T01:00:00Z',
            created_by: 'admin',
            change_notes: 'Fixed typo',
          },
          {
            id: 1,
            template_id: 1,
            content: 'Old content',
            version_number: 1,
            is_active: true,
            created_at: '2025-01-01T00:00:00Z',
            created_by: 'admin',
            change_notes: null,
          },
        ],
      }
      mockedAxios.put.mockResolvedValue({ data: mockResponse })

      const result = await promptsApi.updatePrompt(1, request)

      expect(mockedAxios.put).toHaveBeenCalledWith('/api/prompts/1', request, {
        headers: { 'X-API-Key': undefined },
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('deletePrompt', () => {
    it('should delete prompt template', async () => {
      const mockResponse = {
        message: 'Prompt template deleted successfully',
      }
      mockedAxios.delete.mockResolvedValue({ data: mockResponse })

      const result = await promptsApi.deletePrompt(1)

      expect(mockedAxios.delete).toHaveBeenCalledWith('/api/prompts/1', {
        headers: { 'X-API-Key': undefined },
      })
      expect(result).toEqual(mockResponse)
    })
  })

  describe('publishVersion', () => {
    it('should publish specific version', async () => {
      const mockResponse = {
        id: 2,
        template_id: 1,
        version_number: 2,
        is_active: true,
        message: 'Version 2 is now active',
      }
      mockedAxios.post.mockResolvedValue({ data: mockResponse })

      const result = await promptsApi.publishVersion(1, 2)

      expect(mockedAxios.post).toHaveBeenCalledWith(
        '/api/prompts/1/publish',
        { version_number: 2 },
        {
          headers: { 'X-API-Key': undefined },
        }
      )
      expect(result).toEqual(mockResponse)
    })
  })

  describe('rollbackVersion', () => {
    it('should rollback to previous version', async () => {
      const mockResponse = {
        id: 1,
        template_id: 1,
        version_number: 1,
        is_active: true,
        message: 'Rolled back to version 1',
      }
      mockedAxios.post.mockResolvedValue({ data: mockResponse })

      const result = await promptsApi.rollbackVersion(1)

      expect(mockedAxios.post).toHaveBeenCalledWith('/api/prompts/1/rollback', undefined, {
        headers: { 'X-API-Key': undefined },
      })
      expect(result).toEqual(mockResponse)
    })
  })
})
